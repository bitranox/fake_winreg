"""CLI --set override integration tests."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from click.testing import CliRunner, Result

from fake_winreg.adapters import cli as cli_mod


@pytest.mark.os_agnostic
def test_when_set_override_is_passed_config_reflects_change(
    cli_runner: CliRunner,
    config_cli_context: Callable[[dict[str, Any]], Callable[[], Any]],
) -> None:
    """Verify --set override is visible in config command output."""
    factory = config_cli_context(
        {
            "lib_log_rich": {
                "console_level": "INFO",
            }
        }
    )

    result: Result = cli_runner.invoke(
        cli_mod.cli,
        ["--set", "lib_log_rich.console_level=DEBUG", "config", "--section", "lib_log_rich"],
        obj=factory,
    )

    assert result.exit_code == 0
    assert "DEBUG" in result.output


@pytest.mark.os_agnostic
def test_when_multiple_set_overrides_are_passed_all_apply(
    cli_runner: CliRunner,
    config_cli_context: Callable[[dict[str, Any]], Callable[[], Any]],
) -> None:
    """Verify multiple --set options all apply."""
    factory = config_cli_context(
        {
            "lib_log_rich": {
                "console_level": "INFO",
                "force_color": False,
            }
        }
    )

    result: Result = cli_runner.invoke(
        cli_mod.cli,
        [
            "--set",
            "lib_log_rich.console_level=DEBUG",
            "--set",
            "lib_log_rich.force_color=true",
            "config",
            "--section",
            "lib_log_rich",
        ],
        obj=factory,
    )

    assert result.exit_code == 0
    assert "DEBUG" in result.output


@pytest.mark.os_agnostic
def test_when_set_override_has_nested_key_it_works(
    cli_runner: CliRunner,
    config_cli_context: Callable[[dict[str, Any]], Callable[[], Any]],
) -> None:
    """Verify nested key override (e.g., SECTION.SUB.KEY=VALUE) works."""
    factory = config_cli_context(
        {
            "lib_log_rich": {
                "payload_limits": {
                    "message_max_chars": 4096,
                },
            }
        }
    )

    result: Result = cli_runner.invoke(
        cli_mod.cli,
        ["--set", "lib_log_rich.payload_limits.message_max_chars=8192", "config", "--format", "json"],
        obj=factory,
    )

    assert result.exit_code == 0
    assert "8192" in result.stdout


@pytest.mark.os_agnostic
def test_when_set_override_is_invalid_it_shows_usage_error(
    cli_runner: CliRunner,
    production_factory: Callable[[], Any],
) -> None:
    """Verify invalid --set format shows usage error."""
    result: Result = cli_runner.invoke(
        cli_mod.cli,
        ["--set", "invalid_no_equals", "config"],
        obj=production_factory,
    )

    assert result.exit_code != 0
    assert "must contain '='" in result.output or "must contain '='" in (result.stderr or "")


@pytest.mark.os_agnostic
def test_when_set_override_has_no_dot_it_shows_usage_error(
    cli_runner: CliRunner,
    production_factory: Callable[[], Any],
) -> None:
    """Verify --set without dot in key shows usage error."""
    result: Result = cli_runner.invoke(
        cli_mod.cli,
        ["--set", "nodot=value", "config"],
        obj=production_factory,
    )

    assert result.exit_code != 0


@pytest.mark.os_agnostic
def test_when_set_override_is_empty_string_it_shows_error(
    cli_runner: CliRunner,
    production_factory: Callable[[], Any],
) -> None:
    """Verify --set with empty string shows error."""
    result: Result = cli_runner.invoke(
        cli_mod.cli,
        ["--set", "", "config"],
        obj=production_factory,
    )

    assert result.exit_code != 0


@pytest.mark.os_agnostic
def test_when_no_set_overrides_config_is_unchanged(
    cli_runner: CliRunner,
    config_cli_context: Callable[[dict[str, Any]], Callable[[], Any]],
) -> None:
    """Verify no --set leaves config unchanged."""
    factory = config_cli_context(
        {
            "lib_log_rich": {
                "console_level": "WARNING",
            }
        }
    )

    result: Result = cli_runner.invoke(
        cli_mod.cli,
        ["config", "--section", "lib_log_rich"],
        obj=factory,
    )

    assert result.exit_code == 0
    assert "WARNING" in result.output
