"""Tests for config-deploy permission options.

Verifies that permission parameters are correctly parsed, passed through
the CLI, and delivered to deploy_configuration.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner, Result
from lib_layered_config import Config

from fake_winreg.adapters import cli as cli_mod
from fake_winreg.adapters.config.permissions import (
    get_modes_for_target,
    get_permission_defaults,
    parse_mode,
)
from fake_winreg.composition import AppServices, build_production
from fake_winreg.domain.enums import DeployTarget

# ======================== Permission Settings Loader Tests ========================


@pytest.mark.os_agnostic
def test_get_permission_defaults_returns_library_defaults_when_not_configured(
    config_factory: Callable[[dict[str, Any]], Config],
) -> None:
    """Returns lib_layered_config defaults when no config section exists."""
    config = config_factory({})

    defaults = get_permission_defaults(config)

    assert defaults.app_directory == 0o755
    assert defaults.app_file == 0o644
    assert defaults.host_directory == 0o755
    assert defaults.host_file == 0o644
    assert defaults.user_directory == 0o700
    assert defaults.user_file == 0o600
    assert defaults.enabled is True


@pytest.mark.os_agnostic
def test_get_permission_defaults_reads_from_config(
    config_factory: Callable[[dict[str, Any]], Config],
) -> None:
    """Reads permission defaults from [lib_layered_config.default_permissions]."""
    config = config_factory(
        {
            "lib_layered_config": {
                "default_permissions": {
                    "user_directory": 0o750,
                    "user_file": 0o640,
                    "enabled": False,
                }
            }
        }
    )

    defaults = get_permission_defaults(config)

    assert defaults.user_directory == 0o750
    assert defaults.user_file == 0o640
    assert defaults.enabled is False
    # Non-overridden values use library defaults
    assert defaults.app_directory == 0o755


@pytest.mark.os_agnostic
def test_get_modes_for_target_returns_config_defaults(
    config_factory: Callable[[dict[str, Any]], Config],
) -> None:
    """Returns configured defaults for the specified target layer."""
    config = config_factory(
        {
            "lib_layered_config": {
                "default_permissions": {
                    "user_directory": 0o750,
                    "user_file": 0o640,
                }
            }
        }
    )

    dir_mode, file_mode = get_modes_for_target(DeployTarget.USER, config)

    assert dir_mode == 0o750
    assert file_mode == 0o640


@pytest.mark.os_agnostic
def test_get_modes_for_target_cli_override_takes_precedence(
    config_factory: Callable[[dict[str, Any]], Config],
) -> None:
    """CLI overrides take precedence over config defaults."""
    config = config_factory(
        {
            "lib_layered_config": {
                "default_permissions": {
                    "user_directory": 0o750,
                    "user_file": 0o640,
                }
            }
        }
    )

    dir_mode, file_mode = get_modes_for_target(
        DeployTarget.USER,
        config,
        dir_mode_override=0o700,
        file_mode_override=0o600,
    )

    assert dir_mode == 0o700
    assert file_mode == 0o600


@pytest.mark.os_agnostic
def test_get_modes_for_target_returns_library_defaults_for_app_layer(
    config_factory: Callable[[dict[str, Any]], Config],
) -> None:
    """Returns library defaults for app layer when not configured."""
    config = config_factory({})

    dir_mode, file_mode = get_modes_for_target(DeployTarget.APP, config)

    assert dir_mode == 0o755
    assert file_mode == 0o644


# ======================== parse_mode Tests ========================


@pytest.mark.os_agnostic
def test_parse_mode_accepts_integer() -> None:
    """parse_mode returns integer values unchanged."""
    assert parse_mode(493, 0o644) == 493
    assert parse_mode(0o755, 0o644) == 0o755


@pytest.mark.os_agnostic
def test_parse_mode_accepts_octal_string_with_prefix() -> None:
    """parse_mode parses '0o755' format."""
    assert parse_mode("0o755", 0o644) == 0o755
    assert parse_mode("0o644", 0o755) == 0o644
    assert parse_mode("0o700", 0o755) == 0o700


@pytest.mark.os_agnostic
def test_parse_mode_accepts_octal_string_without_prefix() -> None:
    """parse_mode parses '755' format (no 0o prefix)."""
    assert parse_mode("755", 0o644) == 0o755
    assert parse_mode("644", 0o755) == 0o644
    assert parse_mode("600", 0o755) == 0o600


@pytest.mark.os_agnostic
def test_parse_mode_returns_default_on_invalid_string() -> None:
    """parse_mode returns default for invalid octal strings."""
    assert parse_mode("abc", 0o644) == 0o644
    assert parse_mode("999", 0o755) == 0o755  # 9 is not a valid octal digit
    assert parse_mode("", 0o700) == 0o700


@pytest.mark.os_agnostic
def test_get_permission_defaults_accepts_octal_strings(
    config_factory: Callable[[dict[str, Any]], Config],
) -> None:
    """get_permission_defaults parses octal strings from config."""
    config = config_factory(
        {
            "lib_layered_config": {
                "default_permissions": {
                    "user_directory": "0o750",
                    "user_file": "640",  # Without 0o prefix
                }
            }
        }
    )

    defaults = get_permission_defaults(config)

    assert defaults.user_directory == 0o750
    assert defaults.user_file == 0o640


# ======================== CLI Option Parsing Tests ========================


@dataclass
class CapturedDeployArgs:
    """Container for captured deploy_configuration arguments."""

    targets: tuple[DeployTarget, ...]
    force: bool
    profile: str | None
    set_permissions: bool
    dir_mode: int | None
    file_mode: int | None


@pytest.fixture
def inject_deploy_with_permission_capture(
    clear_config_cache: None,
) -> Callable[[Path, list[CapturedDeployArgs]], Callable[[], Any]]:
    """Return a factory that captures all deploy_configuration arguments."""

    def _inject(deployed_path: Path, captured: list[CapturedDeployArgs]) -> Callable[[], Any]:
        def _capturing_deploy(
            *,
            targets: Any,
            force: bool = False,
            profile: str | None = None,
            set_permissions: bool = True,
            dir_mode: int | None = None,
            file_mode: int | None = None,
        ) -> list[Path]:
            captured.append(
                CapturedDeployArgs(
                    targets=targets,
                    force=force,
                    profile=profile,
                    set_permissions=set_permissions,
                    dir_mode=dir_mode,
                    file_mode=file_mode,
                )
            )
            return [deployed_path]

        prod = build_production()
        test_services = AppServices(
            get_config=prod.get_config,
            get_default_config_path=prod.get_default_config_path,
            deploy_configuration=_capturing_deploy,
            display_config=prod.display_config,
            init_logging=prod.init_logging,
        )
        return lambda: test_services

    return _inject


@pytest.mark.os_agnostic
def test_cli_deploy_passes_set_permissions_true_by_default(
    cli_runner: CliRunner,
    tmp_path: Path,
    inject_deploy_with_permission_capture: Callable[[Path, list[CapturedDeployArgs]], Callable[[], Any]],
) -> None:
    """Default behavior sets permissions (enabled in default config)."""
    deployed_path = tmp_path / "config.toml"
    deployed_path.touch()
    captured: list[CapturedDeployArgs] = []

    factory = inject_deploy_with_permission_capture(deployed_path, captured)

    result: Result = cli_runner.invoke(cli_mod.cli, ["config-deploy", "--target", "user"], obj=factory)

    assert result.exit_code == 0
    assert len(captured) == 1
    assert captured[0].set_permissions is True


@pytest.mark.os_agnostic
def test_cli_deploy_no_permissions_flag_disables_permissions(
    cli_runner: CliRunner,
    tmp_path: Path,
    inject_deploy_with_permission_capture: Callable[[Path, list[CapturedDeployArgs]], Callable[[], Any]],
) -> None:
    """--no-permissions flag disables permission setting."""
    deployed_path = tmp_path / "config.toml"
    deployed_path.touch()
    captured: list[CapturedDeployArgs] = []

    factory = inject_deploy_with_permission_capture(deployed_path, captured)

    result: Result = cli_runner.invoke(
        cli_mod.cli, ["config-deploy", "--target", "user", "--no-permissions"], obj=factory
    )

    assert result.exit_code == 0
    assert len(captured) == 1
    assert captured[0].set_permissions is False


@pytest.mark.os_agnostic
def test_cli_deploy_permissions_flag_enables_permissions(
    cli_runner: CliRunner,
    tmp_path: Path,
    inject_deploy_with_permission_capture: Callable[[Path, list[CapturedDeployArgs]], Callable[[], Any]],
) -> None:
    """--permissions flag explicitly enables permission setting."""
    deployed_path = tmp_path / "config.toml"
    deployed_path.touch()
    captured: list[CapturedDeployArgs] = []

    factory = inject_deploy_with_permission_capture(deployed_path, captured)

    result: Result = cli_runner.invoke(cli_mod.cli, ["config-deploy", "--target", "user", "--permissions"], obj=factory)

    assert result.exit_code == 0
    assert len(captured) == 1
    assert captured[0].set_permissions is True


@pytest.mark.os_agnostic
def test_cli_deploy_dir_mode_parses_octal_without_prefix(
    cli_runner: CliRunner,
    tmp_path: Path,
    inject_deploy_with_permission_capture: Callable[[Path, list[CapturedDeployArgs]], Callable[[], Any]],
) -> None:
    """--dir-mode accepts octal string without 0o prefix (e.g., '750')."""
    deployed_path = tmp_path / "config.toml"
    deployed_path.touch()
    captured: list[CapturedDeployArgs] = []

    factory = inject_deploy_with_permission_capture(deployed_path, captured)

    result: Result = cli_runner.invoke(
        cli_mod.cli, ["config-deploy", "--target", "user", "--dir-mode", "750"], obj=factory
    )

    assert result.exit_code == 0
    assert len(captured) == 1
    assert captured[0].dir_mode == 0o750


@pytest.mark.os_agnostic
def test_cli_deploy_dir_mode_parses_octal_with_prefix(
    cli_runner: CliRunner,
    tmp_path: Path,
    inject_deploy_with_permission_capture: Callable[[Path, list[CapturedDeployArgs]], Callable[[], Any]],
) -> None:
    """--dir-mode accepts octal string with 0o prefix (e.g., '0o750')."""
    deployed_path = tmp_path / "config.toml"
    deployed_path.touch()
    captured: list[CapturedDeployArgs] = []

    factory = inject_deploy_with_permission_capture(deployed_path, captured)

    result: Result = cli_runner.invoke(
        cli_mod.cli, ["config-deploy", "--target", "user", "--dir-mode", "0o750"], obj=factory
    )

    assert result.exit_code == 0
    assert len(captured) == 1
    assert captured[0].dir_mode == 0o750


@pytest.mark.os_agnostic
def test_cli_deploy_file_mode_parses_octal(
    cli_runner: CliRunner,
    tmp_path: Path,
    inject_deploy_with_permission_capture: Callable[[Path, list[CapturedDeployArgs]], Callable[[], Any]],
) -> None:
    """--file-mode accepts octal string."""
    deployed_path = tmp_path / "config.toml"
    deployed_path.touch()
    captured: list[CapturedDeployArgs] = []

    factory = inject_deploy_with_permission_capture(deployed_path, captured)

    result: Result = cli_runner.invoke(
        cli_mod.cli, ["config-deploy", "--target", "user", "--file-mode", "640"], obj=factory
    )

    assert result.exit_code == 0
    assert len(captured) == 1
    assert captured[0].file_mode == 0o640


@pytest.mark.os_agnostic
def test_cli_deploy_invalid_octal_dir_mode_rejected(
    cli_runner: CliRunner,
    production_factory: Callable[[], Any],
) -> None:
    """Invalid octal mode string is rejected with error."""
    result: Result = cli_runner.invoke(
        cli_mod.cli, ["config-deploy", "--target", "user", "--dir-mode", "abc"], obj=production_factory
    )

    assert result.exit_code != 0
    assert "Invalid octal mode" in result.output


@pytest.mark.os_agnostic
def test_cli_deploy_invalid_octal_file_mode_rejected(
    cli_runner: CliRunner,
    production_factory: Callable[[], Any],
) -> None:
    """Invalid octal mode string for file-mode is rejected."""
    result: Result = cli_runner.invoke(
        cli_mod.cli, ["config-deploy", "--target", "user", "--file-mode", "xyz"], obj=production_factory
    )

    assert result.exit_code != 0
    assert "Invalid octal mode" in result.output


@pytest.mark.os_agnostic
def test_cli_deploy_both_mode_options_passed(
    cli_runner: CliRunner,
    tmp_path: Path,
    inject_deploy_with_permission_capture: Callable[[Path, list[CapturedDeployArgs]], Callable[[], Any]],
) -> None:
    """Both --dir-mode and --file-mode can be specified together."""
    deployed_path = tmp_path / "config.toml"
    deployed_path.touch()
    captured: list[CapturedDeployArgs] = []

    factory = inject_deploy_with_permission_capture(deployed_path, captured)

    result: Result = cli_runner.invoke(
        cli_mod.cli,
        ["config-deploy", "--target", "user", "--dir-mode", "750", "--file-mode", "640"],
        obj=factory,
    )

    assert result.exit_code == 0
    assert len(captured) == 1
    assert captured[0].dir_mode == 0o750
    assert captured[0].file_mode == 0o640


@pytest.mark.os_agnostic
def test_cli_deploy_no_permissions_reports_in_output(
    cli_runner: CliRunner,
    tmp_path: Path,
    inject_deploy_with_permission_capture: Callable[[Path, list[CapturedDeployArgs]], Callable[[], Any]],
) -> None:
    """When --no-permissions is used, output mentions permissions not set."""
    deployed_path = tmp_path / "config.toml"
    deployed_path.touch()
    captured: list[CapturedDeployArgs] = []

    factory = inject_deploy_with_permission_capture(deployed_path, captured)

    result: Result = cli_runner.invoke(
        cli_mod.cli, ["config-deploy", "--target", "user", "--no-permissions"], obj=factory
    )

    assert result.exit_code == 0
    assert "permissions not set" in result.output


@pytest.mark.os_agnostic
def test_cli_deploy_help_shows_permission_options(
    cli_runner: CliRunner,
    production_factory: Callable[[], Any],
) -> None:
    """Help text includes permission-related options."""
    result: Result = cli_runner.invoke(cli_mod.cli, ["config-deploy", "--help"], obj=production_factory)

    assert result.exit_code == 0
    assert "--permissions" in result.output
    assert "--no-permissions" in result.output
    assert "--dir-mode" in result.output
    assert "--file-mode" in result.output


# ======================== deploy.py Integration Tests ========================


@pytest.mark.os_agnostic
def test_deploy_configuration_passes_set_permissions_to_library(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """deploy_configuration passes set_permissions to deploy_config."""
    from fake_winreg.adapters.config import deploy as deploy_mod

    captured_kwargs: list[dict[str, Any]] = []

    def mock_deploy_config(**kwargs: Any) -> list[Any]:
        captured_kwargs.append(kwargs)
        return []

    monkeypatch.setattr(deploy_mod, "deploy_config", mock_deploy_config)

    deploy_mod.deploy_configuration(
        targets=[DeployTarget.USER],
        force=False,
        set_permissions=False,
    )

    assert len(captured_kwargs) == 1
    assert captured_kwargs[0]["set_permissions"] is False


@pytest.mark.os_agnostic
def test_deploy_configuration_passes_mode_overrides_to_library(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """deploy_configuration passes dir_mode and file_mode to deploy_config."""
    from fake_winreg.adapters.config import deploy as deploy_mod

    captured_kwargs: list[dict[str, Any]] = []

    def mock_deploy_config(**kwargs: Any) -> list[Any]:
        captured_kwargs.append(kwargs)
        return []

    monkeypatch.setattr(deploy_mod, "deploy_config", mock_deploy_config)

    deploy_mod.deploy_configuration(
        targets=[DeployTarget.USER],
        force=False,
        dir_mode=0o750,
        file_mode=0o640,
    )

    assert len(captured_kwargs) == 1
    assert captured_kwargs[0]["dir_mode"] == 0o750
    assert captured_kwargs[0]["file_mode"] == 0o640
