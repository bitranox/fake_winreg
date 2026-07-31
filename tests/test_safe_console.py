"""Tests for the encode-safe console adapter.

These pin the behaviour that a legacy-codepage console (the Windows default,
cp1252) must never turn a successful command into a crash, and the guard that
keeps the next output line someone adds covered by construction.
"""

from __future__ import annotations

import io
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
