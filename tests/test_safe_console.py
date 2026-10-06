"""Tests for the encode-safe console adapter.

These pin the behaviour that a legacy-codepage console (the Windows default,
cp1252) must never turn a successful command into a crash, and the guard that
keeps the next output line someone adds covered by construction.
"""

from __future__ import annotations

import io
import os
import subprocess
import sys
from pathlib import Path

import pytest
from rich.console import Console

from fake_winreg.adapters.cli import safe_console

PKG = Path(__file__).resolve().parent.parent / "src" / "fake_winreg"


def _cp1252_stream() -> io.TextIOWrapper:
    """Build the stream shape a Windows cp1252 console hands to Python."""
    return io.TextIOWrapper(io.BytesIO(), encoding="cp1252", errors="strict", newline="")


def _read_back(stream: io.TextIOWrapper) -> str:
    stream.flush()
    buffer = stream.buffer
    assert isinstance(buffer, io.BytesIO)
    return buffer.getvalue().decode("cp1252")


class TestEchoOnALegacyCodepage:
    """A cp1252 console must degrade the character, not raise."""

    def test_check_mark_does_not_raise(self) -> None:
        stream = _cp1252_stream()
        safe_console.echo("\u2713 done", file=stream)
        assert "[OK]" in _read_back(stream)

    @pytest.mark.parametrize(
        ("glyph", "expected"),
        [("\u2713", "[OK]"), ("\u2717", "[X]"), ("\u26a0", "[!]"), ("\u2265", ">="), ("\u2192", "->")],
    )
    def test_a_character_cp1252_lacks_degrades_to_its_ascii_form(self, glyph: str, expected: str) -> None:
        stream = _cp1252_stream()
        safe_console.echo(f"{glyph} status", file=stream)
        assert expected in _read_back(stream)

    @pytest.mark.parametrize("glyph", ["\u2022", "\u2026", "\u2019"])
    def test_a_character_cp1252_has_is_left_alone(self, glyph: str) -> None:
        """Degrade only what the stream cannot take; cp1252 has these."""
        stream = _cp1252_stream()
        safe_console.echo(f"{glyph} status", file=stream)
        assert glyph in _read_back(stream)

    def test_an_unmapped_character_is_replaced_rather_than_raising(self) -> None:
        stream = _cp1252_stream()
        safe_console.echo("name \u4e2d\u6587 here", file=stream)
        assert "name" in _read_back(stream)

    def test_the_message_is_written_exactly_once(self) -> None:
        """A retry-after-failure would emit the surviving prefix twice."""
        stream = _cp1252_stream()
        safe_console.echo("\n\u2713 done", file=stream)
        assert _read_back(stream).count("done") == 1


class TestEchoOnAUtf8Console:
    """The common case must be untouched: the character survives verbatim."""

    def test_character_is_preserved(self) -> None:
        stream = io.TextIOWrapper(io.BytesIO(), encoding="utf-8", errors="strict", newline="")
        safe_console.echo("\u2713 done", file=stream)
        stream.flush()
        buffer = stream.buffer
        assert isinstance(buffer, io.BytesIO)
        assert "\u2713" in buffer.getvalue().decode("utf-8")


class TestTheDefaultTargetFollowsTheStreamEchoWritesTo:
    """With no `file`, the encoding must come from the stream `echo` lands on.

    click resolves that target itself from ``sys.stdout``/``sys.stderr``. Judge
    the wrong stream and a legacy-codepage console gets exactly the crash this
    module exists to prevent, while every test passing an explicit `file` stays
    green and says nothing about it.
    """

    def test_a_cp1252_stdout_degrades_the_glyph(self, monkeypatch: pytest.MonkeyPatch) -> None:
        stream = _cp1252_stream()
        monkeypatch.setattr(sys, "stdout", stream)
        safe_console.echo("✓ deployed")
        assert "[OK]" in _read_back(stream)

    def test_err_is_judged_against_stderr_not_stdout(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A stdout that could take the glyph must not excuse a cp1252 stderr."""
        stream = _cp1252_stream()
        monkeypatch.setattr(sys, "stdout", io.TextIOWrapper(io.BytesIO(), encoding="utf-8", newline=""))
        monkeypatch.setattr(sys, "stderr", stream)
        safe_console.echo("✓ deployed", err=True)
        assert "[OK]" in _read_back(stream)


class TestOnlyTheUnencodableCharacterDegrades:
    """The fallback replaces what the stream cannot take, never the rest of the text."""

    def test_a_glyph_cp1252_has_survives_beside_one_it_lacks(self) -> None:
        """The check mark forces the fallback; the ellipsis and the apostrophe must not be rewritten."""
        assert safe_console.encode_safe("\u2713 done\u2026 it\u2019s", "cp1252") == "[OK] done\u2026 it\u2019s"

    def test_rich_output_keeps_what_cp1252_can_print(self) -> None:
        stream = _cp1252_stream()
        Console(file=safe_console.safe_stream(stream), legacy_windows=False, width=80).print("\u2713 done\u2026 ok")
        assert "[OK] done\u2026 ok" in _read_back(stream)


class TestALoneSurrogate:
    """A surrogate (a non-UTF-8 path byte decoded with surrogateescape) encodes in NO codec,
    including utf-8/16/32, so a universal encoding is no reason to skip the check."""

    @pytest.mark.parametrize("encoding", ["utf-8", "UTF-8", "utf-16", "utf-32", "cp1252"])
    def test_it_degrades_to_a_question_mark(self, encoding: str) -> None:
        result = safe_console.encode_safe("path-\udcff-name", encoding)

        result.encode(encoding)
        assert result == "path-?-name"

    def test_only_the_surrogate_is_replaced_on_utf8(self) -> None:
        assert safe_console.encode_safe("check \u2713 \udcff", "utf-8") == "check \u2713 ?"

    def test_echo_on_a_strict_utf8_stream_does_not_raise(self) -> None:
        stream = io.TextIOWrapper(io.BytesIO(), encoding="utf-8", errors="strict", newline="")
        safe_console.echo("path-\udcff-name \u2713", file=stream)
        stream.flush()
        buffer = stream.buffer
        assert isinstance(buffer, io.BytesIO)
        assert buffer.getvalue().decode("utf-8") == "path-?-name \u2713\n"


@pytest.mark.skipif(
    not sys.platform.startswith("linux"), reason="Windows and APFS refuse a filename that is not valid UTF-8"
)
def test_a_command_echoing_a_surrogate_escaped_path_still_exits_0(tmp_path: Path) -> None:
    """A destination holding a raw non-UTF-8 byte reaches echo as a lone surrogate; the files
    are written, so the path line must degrade rather than turn the run into a crash."""
    completed = subprocess.run(
        [sys.executable, "-m", "fake_winreg", "config-generate-examples", "--destination", "ex\udcff"],
        capture_output=True,
        check=False,
        cwd=tmp_path,
        env={**os.environ, "PYTHONIOENCODING": "utf-8:strict"},
    )

    assert completed.returncode == 0, completed.stderr.decode("utf-8", "replace")
    assert b"Generated" in completed.stdout
    assert any((tmp_path / os.fsdecode(b"ex\xff")).iterdir())


def _bytes_written(stream: io.TextIOWrapper) -> bytes:
    stream.flush()
    buffer = stream.buffer
    assert isinstance(buffer, io.BytesIO)
    return buffer.getvalue()


class TestTheStreamsOwnErrorHandlerIsHonoured:
    """What the fallback table does not cover goes to the stream's own error handler.

    Under Python's UTF-8 mode or a C/POSIX locale stdout uses ``surrogateescape``, which writes a
    non-UTF-8 path byte back exactly; stderr always uses ``backslashreplace``. Only a ``strict``
    stream gets ``?`` for such a character.
    """

    def test_a_surrogateescape_stream_writes_the_original_path_byte(self) -> None:
        stream = io.TextIOWrapper(io.BytesIO(), encoding="utf-8", errors="surrogateescape", newline="")

        safe_console.echo("path-\udcff-name \u2713", file=stream)

        assert _bytes_written(stream) == b"path-\xff-name \xe2\x9c\x93\n"

    def test_a_known_glyph_still_gets_its_ascii_form_on_a_surrogateescape_codepage(self) -> None:
        stream = io.TextIOWrapper(io.BytesIO(), encoding="cp1252", errors="surrogateescape", newline="")

        safe_console.echo("\u2713 \udcff \u4e2d", file=stream)

        # The check mark has an ASCII form; the surrogate is the stream's to write; surrogateescape
        # cannot take the CJK character, so that one becomes "?".
        assert _bytes_written(stream) == b"[OK] \xff ?\n"

    def test_a_backslashreplace_stream_escapes_what_the_table_lacks(self) -> None:
        stream = io.TextIOWrapper(io.BytesIO(), encoding="cp1252", errors="backslashreplace", newline="")

        safe_console.echo("\u2713 \u4e2d", file=stream)

        assert _bytes_written(stream) == b"[OK] \\u4e2d\n"

    def test_rich_output_honours_the_handler_too(self) -> None:
        stream = io.TextIOWrapper(io.BytesIO(), encoding="utf-8", errors="surrogateescape", newline="")

        Console(file=safe_console.safe_stream(stream), legacy_windows=False, width=80).print("ex\udcff")

        assert b"ex\xff" in _bytes_written(stream)

    def test_encode_safe_takes_the_handler(self) -> None:
        assert safe_console.encode_safe("ex\udcff", "utf-8", errors="surrogateescape") == "ex\udcff"
        assert safe_console.encode_safe("ex\udcff", "utf-8") == "ex?"


@pytest.mark.skipif(
    not sys.platform.startswith("linux"), reason="Windows and APFS refuse a filename that is not valid UTF-8"
)
def test_a_surrogateescape_stdout_prints_the_path_that_is_on_disk(tmp_path: Path) -> None:
    """End to end: with stdout at surrogateescape the printed path names the real directory."""
    completed = subprocess.run(
        [sys.executable, "-m", "fake_winreg", "config-generate-examples", "--destination", "ex\udcff"],
        capture_output=True,
        check=False,
        cwd=tmp_path,
        env={**os.environ, "PYTHONIOENCODING": "utf-8:surrogateescape"},
    )

    assert completed.returncode == 0, completed.stderr.decode("utf-8", "replace")
    assert b"ex\xff" in completed.stdout
    assert b"ex?" not in completed.stdout


class TestSafeStreamProtectsRich:
    """Rich raises on a legacy codepage too; it renders through its own writer."""

    def test_rich_output_degrades_instead_of_raising(self) -> None:
        stream = _cp1252_stream()
        Console(file=safe_console.safe_stream(stream), legacy_windows=False, width=80).print(
            "check \u2713 done \u2265 90%"
        )
        written = _read_back(stream)
        assert "[OK]" in written
        assert ">= 90%" in written


class TestNoModuleBypassesTheAdapter:
    """The guard that keeps this fixed for the next output line someone adds."""

    def test_no_module_calls_click_echo_directly(self) -> None:
        offenders = [
            f"{path.relative_to(PKG)}:{number}"
            for path in sorted(PKG.rglob("*.py"))
            if path.name != "safe_console.py"
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
            if "click.echo(" in line
        ]
        assert not offenders, (
            "these call click.echo directly and will crash on a cp1252 console; "
            f"use safe_console.echo instead: {offenders}"
        )

    def test_no_module_builds_an_unwrapped_rich_console_on_stdout(self) -> None:
        offenders = [
            f"{path.relative_to(PKG)}:{number}"
            for path in sorted(PKG.rglob("*.py"))
            if path.name != "safe_console.py"
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
            if "Console(file=sys.stdout" in line
        ]
        assert not offenders, f"wrap the writer with safe_console.safe_stream(sys.stdout): {offenders}"
