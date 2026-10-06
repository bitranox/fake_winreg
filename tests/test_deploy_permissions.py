"""Tests for config-deploy permission options.

Verifies that permission parameters are correctly parsed, passed through
the CLI, and delivered to deploy_configuration.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import pytest

from fake_winreg.adapters import cli as cli_mod
from fake_winreg.composition import AppServices, build_production
from fake_winreg.domain.enums import DeployTarget

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from pathlib import Path

    from click.testing import CliRunner, Result

# ======================== CLI Option Parsing Tests ========================


@dataclass
class CapturedDeployArgs:
    """Container for captured deploy_configuration arguments."""

    targets: tuple[DeployTarget, ...]
    force: bool
    profile: str | None
    set_permissions: bool | None
    dir_mode: int | None
    file_mode: int | None
    permission_overrides: Mapping[str, object] | None


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
            set_permissions: bool | None = None,
            dir_mode: int | None = None,
            file_mode: int | None = None,
            permission_overrides: Mapping[str, object] | None = None,
        ) -> list[Path]:
            captured.append(
                CapturedDeployArgs(
                    targets=targets,
                    force=force,
                    profile=profile,
                    set_permissions=set_permissions,
                    dir_mode=dir_mode,
                    file_mode=file_mode,
                    permission_overrides=permission_overrides,
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
def test_cli_deploy_leaves_the_permission_decision_to_the_library_by_default(
    cli_runner: CliRunner,
    tmp_path: Path,
    inject_deploy_with_permission_capture: Callable[[Path, list[CapturedDeployArgs]], Callable[[], Any]],
) -> None:
    """Without an option the command decides nothing: the library follows the configured ``enabled``."""
    deployed_path = tmp_path / "config.toml"
    deployed_path.touch()
    captured: list[CapturedDeployArgs] = []

    factory = inject_deploy_with_permission_capture(deployed_path, captured)

    result: Result = cli_runner.invoke(cli_mod.cli, ["config-deploy", "--target", "user"], obj=factory)

    assert result.exit_code == 0
    assert len(captured) == 1
    assert (captured[0].set_permissions, captured[0].dir_mode, captured[0].file_mode) == (None, None, None)
    assert captured[0].permission_overrides is None
    assert "permissions not set" not in result.output


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
    """A mode that is not a plain octal literal is rejected with an error."""
    result: Result = cli_runner.invoke(
        cli_mod.cli, ["config-deploy", "--target", "user", "--dir-mode", "abc"], obj=production_factory
    )

    assert result.exit_code != 0
    assert "is not a plain octal literal" in result.output


@pytest.mark.os_agnostic
def test_cli_deploy_invalid_octal_file_mode_rejected(
    cli_runner: CliRunner,
    production_factory: Callable[[], Any],
) -> None:
    """A file mode that is not a plain octal literal is rejected."""
    result: Result = cli_runner.invoke(
        cli_mod.cli, ["config-deploy", "--target", "user", "--file-mode", "xyz"], obj=production_factory
    )

    assert result.exit_code != 0
    assert "is not a plain octal literal" in result.output


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
    deploy_mod.deploy_configuration(targets=[DeployTarget.USER])

    assert [kwargs["set_permissions"] for kwargs in captured_kwargs] == [False, None]


@pytest.mark.os_agnostic
def test_deploy_configuration_passes_permission_overrides_to_library(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """deploy_configuration hands permission_overrides to deploy_config unchanged."""
    from fake_winreg.adapters.config import deploy as deploy_mod

    captured_kwargs: list[dict[str, Any]] = []

    def mock_deploy_config(**kwargs: Any) -> list[Any]:
        captured_kwargs.append(kwargs)
        return []

    monkeypatch.setattr(deploy_mod, "deploy_config", mock_deploy_config)
    overrides = {"user_file": "0o640"}

    deploy_mod.deploy_configuration(targets=[DeployTarget.USER], permission_overrides=overrides)
    deploy_mod.deploy_configuration(targets=[DeployTarget.USER])

    assert [kwargs["permission_overrides"] for kwargs in captured_kwargs] == [overrides, None]


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
