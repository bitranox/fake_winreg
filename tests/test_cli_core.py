"""CLI core stories: traceback, main entry, help, hello, fail, info, unknown command."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import lib_cli_exit_tools
import pytest
from click.testing import CliRunner, Result

from fake_winreg import __init__conf__
from fake_winreg.adapters import cli as cli_mod
from fake_winreg.composition import build_production


@pytest.mark.os_agnostic
def test_snapshot_traceback_state_returns_disabled_by_default(managed_traceback_state: None) -> None:
    """snapshot_traceback_state returns both flags disabled initially."""
    assert cli_mod.snapshot_traceback_state() == (False, False)


@pytest.mark.os_agnostic
def test_apply_traceback_preferences_enables_both_flags(managed_traceback_state: None) -> None:
    """apply_traceback_preferences(True) enables traceback and force_color."""
    cli_mod.apply_traceback_preferences(True)

    assert lib_cli_exit_tools.config.traceback is True
    assert lib_cli_exit_tools.config.traceback_force_color is True


@pytest.mark.os_agnostic
def test_restore_traceback_state_resets_flags_to_previous(managed_traceback_state: None) -> None:
    """restore_traceback_state resets flags to their pre-apply values."""
    previous = cli_mod.snapshot_traceback_state()
    cli_mod.apply_traceback_preferences(True)

    cli_mod.restore_traceback_state(previous)

    assert lib_cli_exit_tools.config.traceback is False
    assert lib_cli_exit_tools.config.traceback_force_color is False


@pytest.mark.os_agnostic
def test_traceback_flag_is_active_during_info_command(
    monkeypatch: pytest.MonkeyPatch,
    managed_traceback_state: None,
) -> None:
    """--traceback enables both flags during command execution."""
    notes: list[tuple[bool, bool]] = []

    def record() -> None:
        notes.append(
            (
                lib_cli_exit_tools.config.traceback,
                lib_cli_exit_tools.config.traceback_force_color,
            )
        )

    monkeypatch.setattr(__init__conf__, "print_info", record)

    exit_code = cli_mod.main(["--traceback", "info"], services_factory=build_production)

    assert exit_code == 0
    assert notes == [(True, True)]


@pytest.mark.os_agnostic
def test_traceback_flags_restored_after_info_command(
    monkeypatch: pytest.MonkeyPatch,
    managed_traceback_state: None,
) -> None:
    """--traceback flags are restored to disabled after command completes."""
    monkeypatch.setattr(__init__conf__, "print_info", lambda: None)

    cli_mod.main(["--traceback", "info"], services_factory=build_production)

    assert lib_cli_exit_tools.config.traceback is False
    assert lib_cli_exit_tools.config.traceback_force_color is False


@pytest.mark.os_agnostic
def test_when_main_is_called_it_invokes_cli_with_services_factory(
    managed_traceback_state: None,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify main() invokes CLI with services_factory passed via ctx.obj."""
    result = cli_mod.main(["info"], services_factory=build_production)

    assert result == 0
    captured = capsys.readouterr()
    assert __init__conf__.name in captured.out


@pytest.mark.os_agnostic
def test_when_cli_runs_without_arguments_help_is_printed(
    cli_runner: CliRunner,
    production_factory: Callable[[], Any],
) -> None:
    """Verify CLI with no arguments displays help text."""
    result = cli_runner.invoke(cli_mod.cli, [], obj=production_factory)

    assert result.exit_code == 0
    assert "Usage:" in result.output


@pytest.mark.os_agnostic
def test_when_main_receives_no_arguments_help_is_shown(
    managed_traceback_state: None,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify main with no args shows help."""
    exit_code = cli_mod.main([], services_factory=build_production)

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Usage:" in captured.out


@pytest.mark.os_agnostic
def test_when_traceback_is_requested_without_command_help_is_shown(
    cli_runner: CliRunner,
    production_factory: Callable[[], Any],
) -> None:
    """Verify --traceback without command still shows help."""
    result = cli_runner.invoke(cli_mod.cli, ["--traceback"], obj=production_factory)

    assert result.exit_code == 0
    assert "Usage:" in result.output


@pytest.mark.os_agnostic
def test_traceback_flag_displays_full_exception_traceback(
    managed_traceback_state: None,
    capsys: pytest.CaptureFixture[str],
    strip_ansi: Callable[[str], str],
) -> None:
    """--traceback prints the complete traceback on failure for unknown commands."""
    exit_code = cli_mod.main(["--traceback", "--unknown-option-xyz"], services_factory=build_production)

    assert exit_code != 0
    assert lib_cli_exit_tools.config.traceback is False
    assert lib_cli_exit_tools.config.traceback_force_color is False


@pytest.mark.os_agnostic
def test_info_command_displays_project_metadata(
    cli_runner: CliRunner,
    production_factory: Callable[[], Any],
) -> None:
    """info command displays project name and version."""
    result: Result = cli_runner.invoke(cli_mod.cli, ["info"], obj=production_factory)

    assert result.exit_code == 0
    assert f"Info for {__init__conf__.name}:" in result.output
    assert __init__conf__.version in result.output


@pytest.mark.os_agnostic
def test_unknown_command_shows_no_such_command_error(
    cli_runner: CliRunner,
    production_factory: Callable[[], Any],
) -> None:
    """Unknown command produces 'No such command' error."""
    result: Result = cli_runner.invoke(cli_mod.cli, ["does-not-exist"], obj=production_factory)

    assert result.exit_code != 0
    assert "No such command" in result.output


@pytest.mark.os_agnostic
def test_restore_traceback_false_keeps_flags_enabled(
    managed_traceback_state: None,
) -> None:
    """restore_traceback=False leaves traceback flags enabled after command."""
    cli_mod.apply_traceback_preferences(False)

    cli_mod.main(["--traceback", "info"], restore_traceback=False, services_factory=build_production)

    assert lib_cli_exit_tools.config.traceback is True
    assert lib_cli_exit_tools.config.traceback_force_color is True


@pytest.mark.os_agnostic
def test_when_logdemo_is_invoked_it_completes_successfully(
    cli_runner: CliRunner,
    production_factory: Callable[[], Any],
) -> None:
    """Verify logdemo command runs and exits with code 0."""
    result: Result = cli_runner.invoke(cli_mod.cli, ["logdemo"], obj=production_factory)

    assert result.exit_code == 0
    assert "Log demo completed" in result.output
