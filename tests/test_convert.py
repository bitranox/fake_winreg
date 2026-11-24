# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false
"""Tests for streaming registry format conversion."""

from __future__ import annotations

from itertools import pairwise
from typing import TYPE_CHECKING

import pytest

import fake_winreg as winreg
from fake_winreg.adapters.persistence.convert import convert_registry, copy_backend
from fake_winreg.adapters.persistence.sqlite_backend import SqliteBackend
from fake_winreg.domain.constants import hive_name_hashed_by_int
from fake_winreg.domain.memory_backend import InMemoryBackend

if TYPE_CHECKING:
    from pathlib import Path

    from fake_winreg.domain.registry import FakeRegistryKey


def _populate_sqlite(db_path: Path) -> None:
    """Create a SQLite registry with test data."""
    backend = SqliteBackend(db_path)
    winreg.use_backend(backend)  # type: ignore[arg-type]
    reg = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
    key = winreg.CreateKey(reg, r"Software\ConvertTest")
    winreg.SetValueEx(key, "StringVal", 0, winreg.REG_SZ, "hello")
    winreg.SetValueEx(key, "DwordVal", 0, winreg.REG_DWORD, 42)
    winreg.SetValueEx(key, "BinaryVal", 0, winreg.REG_BINARY, b"\xde\xad")
    winreg.SetValueEx(key, "MultiVal", 0, winreg.REG_MULTI_SZ, ["a", "b", "c"])
    backend.close()


@pytest.fixture(autouse=True)
def _restore_backend():  # type: ignore[no-untyped-def]  # pyright: ignore[reportUnusedFunction]
    """Restore default InMemoryBackend after each test."""
    yield
    winreg.use_backend(InMemoryBackend())  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Round-trip tests
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_sqlite_to_json_to_sqlite(tmp_path: Path) -> None:
    db1 = tmp_path / "source.db"
    json_file = tmp_path / "middle.json"
    db2 = tmp_path / "target.db"

    _populate_sqlite(db1)

    count1 = convert_registry(db1, json_file)
    assert count1 > 0
    assert json_file.exists()

    count2 = convert_registry(json_file, db2)
    assert count2 > 0

    # Verify data survived the round-trip
    backend = SqliteBackend(db2)
    winreg.use_backend(backend)  # type: ignore[arg-type]
    reg = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
    key = winreg.OpenKey(reg, r"Software\ConvertTest")
    assert winreg.QueryValueEx(key, "StringVal") == ("hello", winreg.REG_SZ)
    assert winreg.QueryValueEx(key, "DwordVal") == (42, winreg.REG_DWORD)
    backend.close()


@pytest.mark.os_agnostic
def test_sqlite_to_reg_to_sqlite(tmp_path: Path) -> None:
    db1 = tmp_path / "source.db"
    reg_file = tmp_path / "middle.reg"
    db2 = tmp_path / "target.db"

    _populate_sqlite(db1)

    count1 = convert_registry(db1, reg_file)
    assert count1 > 0
    assert reg_file.exists()
    content = reg_file.read_text(encoding="utf-16")
    assert "Windows Registry Editor Version 5.00" in content

    count2 = convert_registry(reg_file, db2)
    assert count2 > 0

    backend = SqliteBackend(db2)
    winreg.use_backend(backend)  # type: ignore[arg-type]
    reg = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
    key = winreg.OpenKey(reg, r"Software\ConvertTest")
    assert winreg.QueryValueEx(key, "StringVal") == ("hello", winreg.REG_SZ)
    backend.close()


@pytest.mark.os_agnostic
def test_json_to_reg(tmp_path: Path) -> None:
    db = tmp_path / "source.db"
    json_file = tmp_path / "source.json"
    reg_file = tmp_path / "target.reg"

    _populate_sqlite(db)
    convert_registry(db, json_file)
    count = convert_registry(json_file, reg_file)
    assert count > 0
    assert "ConvertTest" in reg_file.read_text(encoding="utf-16")


@pytest.mark.os_agnostic
def test_reg_to_json(tmp_path: Path) -> None:
    db = tmp_path / "source.db"
    reg_file = tmp_path / "source.reg"
    json_file = tmp_path / "target.json"

    _populate_sqlite(db)
    convert_registry(db, reg_file)
    count = convert_registry(reg_file, json_file)
    assert count > 0
    assert json_file.exists()


@pytest.mark.os_agnostic
def test_sqlite_to_sqlite(tmp_path: Path) -> None:
    db1 = tmp_path / "source.db"
    db2 = tmp_path / "copy.db"

    _populate_sqlite(db1)
    count = convert_registry(db1, db2)
    assert count > 0

    backend = SqliteBackend(db2)
    winreg.use_backend(backend)  # type: ignore[arg-type]
    reg = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
    key = winreg.OpenKey(reg, r"Software\ConvertTest")
    assert winreg.QueryValueEx(key, "StringVal") == ("hello", winreg.REG_SZ)
    backend.close()


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_unknown_extension_raises(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Unknown registry format"):
        convert_registry(tmp_path / "file.xyz", tmp_path / "out.db")


@pytest.mark.os_agnostic
def test_unknown_target_extension_raises(tmp_path: Path) -> None:
    db = tmp_path / "source.db"
    _populate_sqlite(db)
    with pytest.raises(ValueError, match="Unknown registry format"):
        convert_registry(db, tmp_path / "out.xyz")


# ---------------------------------------------------------------------------
# Backend restoration
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_convert_restores_previous_backend(tmp_path: Path) -> None:
    db = tmp_path / "test.db"
    json_file = tmp_path / "test.json"
    _populate_sqlite(db)

    # Set original AFTER _populate_sqlite (which changes the backend)
    original = InMemoryBackend()
    winreg.use_backend(original)  # type: ignore[arg-type]

    convert_registry(db, json_file)

    # The original backend should be restored after conversion
    assert winreg.get_backend() is original


# ---------------------------------------------------------------------------
# CLI smoke test
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_cli_convert_command(tmp_path: Path) -> None:
    from click.testing import CliRunner

    from fake_winreg.adapters.cli import cli
    from fake_winreg.composition import build_testing

    db = tmp_path / "cli_test.db"
    reg_file = tmp_path / "cli_test.reg"

    _populate_sqlite(db)

    # Through the root group: convert binds job context onto the lib_log_rich runtime, which
    # only the root starts, so invoking the command alone passed only when an earlier test
    # had left a runtime running.
    runner = CliRunner()
    result = runner.invoke(cli, ["convert", f"if={db}", f"of={reg_file}"], obj=build_testing)
    assert result.exit_code == 0, result.output
    assert "Converted" in result.output
    assert reg_file.exists()


@pytest.mark.os_agnostic
def test_cli_convert_missing_args() -> None:
    from click.testing import CliRunner

    from fake_winreg.adapters.cli.commands.convert import cli_convert

    runner = CliRunner()

    result = runner.invoke(cli_convert, ["if=source.db"])
    assert result.exit_code != 0

    result = runner.invoke(cli_convert, ["of=target.db"])
    assert result.exit_code != 0

    result = runner.invoke(cli_convert, [])
    assert result.exit_code != 0


# ---------------------------------------------------------------------------
# Format detection and transactional import
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_format_is_detected_from_the_suffix_in_any_case(tmp_path: Path) -> None:
    db = tmp_path / "src.db"
    _populate_sqlite(db)
    chain = [db, tmp_path / "a.JSON", tmp_path / "b.SQLite", tmp_path / "c.Reg", tmp_path / "d.sqlite3"]
    for source, target in pairwise(chain):
        convert_registry(source, target)
    assert _snapshot(chain[-1]) == _snapshot(db)


@pytest.mark.os_agnostic
@pytest.mark.parametrize(
    ("broken_tail", "error"),
    [
        # Not UTF-8: decoded only when the reader gets there, after the key above was written.
        (b'"bad"="\xff\xfe\xfd"\r\n', UnicodeDecodeError),
        (b'"bad"=hex(b):zz\r\n', ValueError),
    ],
    ids=["undecodable", "bad-hex"],
)
def test_failed_reg_import_leaves_the_sqlite_target_unchanged(
    tmp_path: Path, broken_tail: bytes, error: type[Exception]
) -> None:
    """The import runs in one transaction, so a file that breaks halfway adds nothing."""
    db = tmp_path / "target.db"
    _populate_sqlite(db)
    before = _snapshot(db)
    reg_file = tmp_path / "broken.reg"
    reg_file.write_bytes(
        b"Windows Registry Editor Version 5.00\r\n\r\n[HKEY_CURRENT_USER\\Software\\Partial]\r\n"
        + b'"x"="1"\r\n' * 2000
        + broken_tail
    )
    with pytest.raises(error):
        convert_registry(reg_file, db)
    assert _snapshot(db) == before


@pytest.mark.os_agnostic
def test_reg_into_sqlite_keeps_every_key(tmp_path: Path) -> None:
    db1 = tmp_path / "one.db"
    _populate_sqlite(db1)
    reg_file = tmp_path / "one.reg"
    convert_registry(db1, reg_file)
    db2 = tmp_path / "two.db"
    convert_registry(reg_file, db2)
    assert _snapshot(db2) == _snapshot(db1)


def _snapshot(db_path: Path) -> list[tuple[str, list[tuple[str, object, int]]]]:
    """Every key path with its values, read through a fresh backend."""
    with SqliteBackend(db_path) as backend:
        rows: list[tuple[str, list[tuple[str, object, int]]]] = []

        def walk(key: FakeRegistryKey) -> None:
            rows.append((key.full_key, [(e.name, e.data, e.value_type) for e in backend.enum_values(key)]))
            for name in backend.enum_keys(key):
                walk(backend.get_key(key, name))

        for hive_int in sorted(hive_name_hashed_by_int):
            walk(backend.get_hive(hive_int))
        return rows


# ---------------------------------------------------------------------------
# Missing source
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
@pytest.mark.parametrize("source_name", ["nope.db", "nope.sqlite", "nope.json", "nope.reg"])
@pytest.mark.parametrize("target_name", ["out.db", "out.json", "out.reg"])
def test_missing_source_is_refused_and_creates_no_file(tmp_path: Path, source_name: str, target_name: str) -> None:
    """Opening a SQLite path creates it, so the refusal must come before any backend is opened."""
    source = tmp_path / source_name
    with pytest.raises(FileNotFoundError, match=source_name) as raised:
        convert_registry(source, tmp_path / target_name)
    assert raised.value.filename == str(source)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.os_agnostic
@pytest.mark.parametrize("source_name", ["nope.db", "nope.json"])
def test_cli_missing_source_exits_like_a_missing_reg_source(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], source_name: str
) -> None:
    """A missing .reg source always failed through open(); every format now exits the same way."""
    from fake_winreg.adapters.cli.main import main
    from fake_winreg.composition import build_testing

    reference = main(
        ["convert", f"if={tmp_path / 'nope.reg'}", f"of={tmp_path / 'out.json'}"], services_factory=build_testing
    )
    capsys.readouterr()

    exit_code = main(
        ["convert", f"if={tmp_path / source_name}", f"of={tmp_path / 'out.json'}"], services_factory=build_testing
    )

    assert reference != 0
    assert exit_code == reference
    assert "FileNotFoundError" in capsys.readouterr().err
    assert list(tmp_path.iterdir()) == []


@pytest.mark.os_agnostic
def test_copy_backend_copies_every_key_and_value_into_sqlite(tmp_path: Path) -> None:
    source_db = tmp_path / "source.db"
    _populate_sqlite(source_db)
    target_db = tmp_path / "target.db"
    with SqliteBackend(source_db) as source, SqliteBackend(target_db) as target, target.bulk():
        count = copy_backend(source, target)
    assert _snapshot(target_db) == _snapshot(source_db)
    assert count == len(_snapshot(source_db))
