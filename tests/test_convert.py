# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false
"""Tests for streaming registry format conversion."""

from __future__ import annotations

from pathlib import Path

import pytest

import fake_winreg as winreg
from fake_winreg.adapters.persistence.convert import convert_registry
from fake_winreg.adapters.persistence.sqlite_backend import SqliteBackend
from fake_winreg.domain.memory_backend import InMemoryBackend


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
    from fake_winreg.domain.api import _get_backend  # pyright: ignore[reportPrivateUsage]

    assert _get_backend() is original


# ---------------------------------------------------------------------------
# CLI smoke test
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_cli_convert_command(tmp_path: Path) -> None:
    from click.testing import CliRunner

    from fake_winreg.adapters.cli.commands.convert import cli_convert

    db = tmp_path / "cli_test.db"
    reg_file = tmp_path / "cli_test.reg"

    _populate_sqlite(db)

    runner = CliRunner()
    result = runner.invoke(cli_convert, [f"if={db}", f"of={reg_file}"])
    assert result.exit_code == 0
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
