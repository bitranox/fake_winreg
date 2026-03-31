# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false
"""Tests for the ``reg`` CLI command group."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from fake_winreg.adapters.cli.commands.reg import cli_reg
from fake_winreg.adapters.persistence.sqlite_backend import SqliteBackend
from fake_winreg.domain.constants import (
    HKEY_LOCAL_MACHINE,
    REG_DWORD,
    REG_SZ,
)


def _seed_db(db_path: Path) -> None:
    """Create a SQLite registry with test data."""
    backend = SqliteBackend(db_path)
    hklm = backend.get_hive(HKEY_LOCAL_MACHINE)
    sw = backend.create_key(hklm, r"SOFTWARE\TestApp")
    backend.set_value(sw, "Name", "hello", REG_SZ)
    backend.set_value(sw, "Count", 42, REG_DWORD)
    backend.create_key(hklm, r"SOFTWARE\TestApp\Sub1")
    backend.create_key(hklm, r"SOFTWARE\TestApp\Sub2")
    backend.close()


@pytest.fixture()
def db(tmp_path: Path) -> Path:
    p = tmp_path / "test.db"
    _seed_db(p)
    return p


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


# ---------------------------------------------------------------------------
# list-keys
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_list_keys(runner: CliRunner, db: Path) -> None:
    result = runner.invoke(cli_reg, ["--db", str(db), "list-keys", r"HKEY_LOCAL_MACHINE\SOFTWARE\TestApp"])
    assert result.exit_code == 0
    assert "Sub1" in result.output
    assert "Sub2" in result.output


@pytest.mark.os_agnostic
def test_list_keys_missing_key(runner: CliRunner, db: Path) -> None:
    result = runner.invoke(cli_reg, ["--db", str(db), "list-keys", r"HKEY_LOCAL_MACHINE\NoSuchKey"])
    assert result.exit_code != 0
    assert "not found" in result.output.lower() or "error" in result.output.lower()


# ---------------------------------------------------------------------------
# create-key / delete-key
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_create_and_delete_key(runner: CliRunner, db: Path) -> None:
    result = runner.invoke(cli_reg, ["--db", str(db), "create-key", r"HKEY_CURRENT_USER\Software\NewApp"])
    assert result.exit_code == 0

    result = runner.invoke(cli_reg, ["--db", str(db), "list-keys", r"HKEY_CURRENT_USER\Software"])
    assert "NewApp" in result.output

    result = runner.invoke(cli_reg, ["--db", str(db), "delete-key", r"HKEY_CURRENT_USER\Software\NewApp"])
    assert result.exit_code == 0


@pytest.mark.os_agnostic
def test_delete_key_with_children_fails(runner: CliRunner, db: Path) -> None:
    result = runner.invoke(cli_reg, ["--db", str(db), "delete-key", r"HKEY_LOCAL_MACHINE\SOFTWARE\TestApp"])
    assert result.exit_code != 0
    assert "subkeys" in result.output.lower() or "error" in result.output.lower()


# ---------------------------------------------------------------------------
# info
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_info(runner: CliRunner, db: Path) -> None:
    result = runner.invoke(cli_reg, ["--db", str(db), "info", r"HKEY_LOCAL_MACHINE\SOFTWARE\TestApp"])
    assert result.exit_code == 0
    assert "Subkeys: 2" in result.output
    assert "Values:  2" in result.output


# ---------------------------------------------------------------------------
# list-values
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_list_values(runner: CliRunner, db: Path) -> None:
    result = runner.invoke(cli_reg, ["--db", str(db), "list-values", r"HKEY_LOCAL_MACHINE\SOFTWARE\TestApp"])
    assert result.exit_code == 0
    assert "Name" in result.output
    assert "Count" in result.output
    assert "REG_SZ" in result.output
    assert "REG_DWORD" in result.output


# ---------------------------------------------------------------------------
# get / set / delete-value
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_get_value(runner: CliRunner, db: Path) -> None:
    result = runner.invoke(cli_reg, ["--db", str(db), "get", r"HKEY_LOCAL_MACHINE\SOFTWARE\TestApp", "Name"])
    assert result.exit_code == 0
    assert result.output.strip() == "hello"


@pytest.mark.os_agnostic
def test_get_value_missing(runner: CliRunner, db: Path) -> None:
    result = runner.invoke(cli_reg, ["--db", str(db), "get", r"HKEY_LOCAL_MACHINE\SOFTWARE\TestApp", "NoSuch"])
    assert result.exit_code != 0


@pytest.mark.os_agnostic
def test_set_value_string(runner: CliRunner, db: Path) -> None:
    result = runner.invoke(cli_reg, ["--db", str(db), "set", r"HKEY_LOCAL_MACHINE\SOFTWARE\TestApp", "NewVal", "world"])
    assert result.exit_code == 0

    result = runner.invoke(cli_reg, ["--db", str(db), "get", r"HKEY_LOCAL_MACHINE\SOFTWARE\TestApp", "NewVal"])
    assert result.output.strip() == "world"


@pytest.mark.os_agnostic
def test_set_value_dword(runner: CliRunner, db: Path) -> None:
    result = runner.invoke(
        cli_reg,
        ["--db", str(db), "set", r"HKEY_LOCAL_MACHINE\SOFTWARE\TestApp", "Num", "99", "--type", "REG_DWORD"],
    )
    assert result.exit_code == 0

    result = runner.invoke(cli_reg, ["--db", str(db), "get", r"HKEY_LOCAL_MACHINE\SOFTWARE\TestApp", "Num"])
    assert result.output.strip() == "99"


@pytest.mark.os_agnostic
def test_set_value_binary(runner: CliRunner, db: Path) -> None:
    result = runner.invoke(
        cli_reg,
        ["--db", str(db), "set", r"HKEY_LOCAL_MACHINE\SOFTWARE\TestApp", "Bin", "deadbeef", "--type", "REG_BINARY"],
    )
    assert result.exit_code == 0

    result = runner.invoke(cli_reg, ["--db", str(db), "get", r"HKEY_LOCAL_MACHINE\SOFTWARE\TestApp", "Bin"])
    assert result.output.strip() == "deadbeef"


@pytest.mark.os_agnostic
def test_set_value_multi_sz(runner: CliRunner, db: Path) -> None:
    result = runner.invoke(
        cli_reg,
        ["--db", str(db), "set", r"HKEY_LOCAL_MACHINE\SOFTWARE\TestApp", "List", "a,b,c", "--type", "REG_MULTI_SZ"],
    )
    assert result.exit_code == 0

    result = runner.invoke(cli_reg, ["--db", str(db), "get", r"HKEY_LOCAL_MACHINE\SOFTWARE\TestApp", "List"])
    assert "a" in result.output and "b" in result.output and "c" in result.output


@pytest.mark.os_agnostic
def test_delete_value(runner: CliRunner, db: Path) -> None:
    result = runner.invoke(cli_reg, ["--db", str(db), "delete-value", r"HKEY_LOCAL_MACHINE\SOFTWARE\TestApp", "Name"])
    assert result.exit_code == 0

    result = runner.invoke(cli_reg, ["--db", str(db), "get", r"HKEY_LOCAL_MACHINE\SOFTWARE\TestApp", "Name"])
    assert result.exit_code != 0


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_no_db_specified(runner: CliRunner) -> None:
    result = runner.invoke(cli_reg, ["list-keys", "HKEY_LOCAL_MACHINE"])
    assert result.exit_code != 0


@pytest.mark.os_agnostic
def test_unknown_hive(runner: CliRunner, db: Path) -> None:
    result = runner.invoke(cli_reg, ["--db", str(db), "list-keys", "HKEY_FAKE"])
    assert result.exit_code != 0
    assert "Unknown hive" in result.output


@pytest.mark.os_agnostic
def test_set_invalid_type(runner: CliRunner, db: Path) -> None:
    result = runner.invoke(
        cli_reg,
        ["--db", str(db), "set", r"HKEY_LOCAL_MACHINE\SOFTWARE\TestApp", "X", "y", "--type", "REG_BOGUS"],
    )
    assert result.exit_code != 0
    assert "Unknown type" in result.output
