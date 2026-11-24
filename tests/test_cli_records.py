"""Typed CLI records and read-only tables: what each one guarantees to its callers."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import pytest
from click.testing import CliRunner

from fake_winreg.adapters.cli import cli, cli_config, cli_reg
from fake_winreg.adapters.cli.context import TracebackState, restore_traceback_state, snapshot_traceback_state
from fake_winreg.adapters.cli.safe_console import ASCII_FALLBACKS
from fake_winreg.adapters.config.overrides import nest_overrides
from fake_winreg.adapters.persistence.sqlite_backend import SqliteBackend
from fake_winreg.composition import build_testing
from fake_winreg.domain.constants import HKEY_CURRENT_USER, REG_DWORD

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.os_agnostic
def test_each_command_owns_its_context_settings() -> None:
    """A change to one command's settings never reaches another (rich_click updates them in place)."""
    assert cli.context_settings is not cli_reg.context_settings
    cli_config.context_settings["probe"] = True
    try:
        assert "probe" not in cli.context_settings
        assert "probe" not in cli_reg.context_settings
    finally:
        del cli_config.context_settings["probe"]


@pytest.mark.os_agnostic
def test_reg_set_type_is_case_insensitive(tmp_path: Path) -> None:
    db = tmp_path / "t.db"
    result = CliRunner().invoke(
        cli_reg, ["--db", str(db), "set", r"HKEY_CURRENT_USER\Software\X", "v", "5", "--type", "reg_dword"]
    )
    assert result.exit_code == 0, result.output
    with SqliteBackend(db) as backend:
        key = backend.get_key(backend.get_hive(HKEY_CURRENT_USER), r"Software\X")
        value = backend.get_value(key, "v")
    assert (value.value, value.value_type) == (5, REG_DWORD)


@pytest.mark.os_agnostic
def test_reg_set_unknown_type_keeps_its_message(tmp_path: Path) -> None:
    args = ["--db", str(tmp_path / "t.db"), "set", r"HKEY_CURRENT_USER\Software\X", "v", "5", "--type", "REG_BOGUS"]
    result = CliRunner().invoke(cli_reg, args)
    assert result.exit_code == 2
    expected = (
        "Unknown type: REG_BOGUS. Valid types: "
        "REG_BINARY, REG_DWORD, REG_EXPAND_SZ, REG_MULTI_SZ, REG_NONE, REG_QWORD, REG_SZ"
    )
    # rich-click draws the error in a box wrapped at the terminal width: drop the box-drawing
    # characters (U+2500-U+257F) and collapse whitespace before comparing.
    flattened = " ".join("".join(" " if 0x2500 <= ord(ch) <= 0x257F else ch for ch in result.output).split())
    assert expected in flattened


@pytest.mark.os_agnostic
def test_reg_empty_db_option_counts_as_not_given() -> None:
    result = CliRunner().invoke(cli_reg, ["--db", "", "list-keys", "HKEY_USERS"])
    assert result.exit_code == 2
    assert "No registry database specified" in result.output


@pytest.mark.os_agnostic
def test_traceback_state_names_its_flags_and_still_equals_a_pair(managed_traceback_state: None) -> None:
    state = snapshot_traceback_state()
    assert isinstance(state, TracebackState)
    assert (state.traceback_enabled, state.force_color) == (False, False)
    assert state == (False, False)
    restore_traceback_state(TracebackState(traceback_enabled=True, force_color=False))
    assert snapshot_traceback_state() == TracebackState(traceback_enabled=True, force_color=False)


@pytest.mark.os_agnostic
def test_ascii_fallbacks_is_read_only() -> None:
    with pytest.raises(TypeError):
        # The cast hides the read-only type on purpose: the write has to reach the runtime object.
        cast("dict[str, str]", ASCII_FALLBACKS)["x"] = "y"


@pytest.mark.os_agnostic
def test_nest_overrides_returns_the_tree() -> None:
    assert nest_overrides(("a.b=1", "a.c.d=x")) == {"a": {"b": 1, "c": {"d": "x"}}}


@pytest.mark.os_agnostic
def test_export_demo_registries_writes_the_nine_files_its_help_names(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    # Through the root group: it starts logging, which the command's own log line needs.
    result = CliRunner().invoke(cli, ["export-demo-registries"], obj=build_testing)
    assert result.exit_code == 0, result.output
    expected = {f"{name}{ext}" for name in ("windows10", "windows11", "wine") for ext in (".json", ".reg", ".db")}
    assert {path.name for path in tmp_path.iterdir()} == expected
