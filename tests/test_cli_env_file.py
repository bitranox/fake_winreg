"""CLI --env-file option: path passing, validation, and value override."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner, Result
from lib_layered_config import Config

from fake_winreg.adapters import cli as cli_mod
from fake_winreg.composition import AppServices, build_production


@dataclass
class CapturedGetConfigArgs:
    """Container for captured get_config keyword arguments."""

    profile: str | None
    dotenv_path: str | None


@pytest.fixture
def inject_config_with_dotenv_capture(
    clear_config_cache: None,
) -> Callable[[Config, list[CapturedGetConfigArgs]], Callable[[], AppServices]]:
    """Return a factory that captures dotenv_path passed to get_config."""

    def _inject(config: Config, captured: list[CapturedGetConfigArgs]) -> Callable[[], AppServices]:
        def _capturing_get_config(
            *,
            profile: str | None = None,
            start_dir: str | None = None,
            dotenv_path: str | None = None,
        ) -> Config:
            captured.append(CapturedGetConfigArgs(profile=profile, dotenv_path=dotenv_path))
            return config

        prod = build_production()
        test_services = AppServices(
            get_config=_capturing_get_config,
            get_default_config_path=prod.get_default_config_path,
            deploy_configuration=prod.deploy_configuration,
            display_config=prod.display_config,
            send_email=prod.send_email,
            send_notification=prod.send_notification,
            load_email_config_from_dict=prod.load_email_config_from_dict,
            init_logging=prod.init_logging,
        )
        return lambda: test_services

    return _inject


# ======================== --env-file argument passing ========================


@pytest.mark.os_agnostic
def test_env_file_passes_dotenv_path_to_get_config(
    cli_runner: CliRunner,
    tmp_path: Path,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config_with_dotenv_capture: Callable[[Config, list[CapturedGetConfigArgs]], Callable[[], AppServices]],
) -> None:
    """--env-file passes the file path as dotenv_path to get_config."""
    env_file = tmp_path / ".env"
    env_file.write_text("# empty\n")
    config = config_factory({})
    captured: list[CapturedGetConfigArgs] = []

    factory = inject_config_with_dotenv_capture(config, captured)

    result: Result = cli_runner.invoke(cli_mod.cli, ["--env-file", str(env_file), "info"], obj=factory)

    assert result.exit_code == 0
    assert len(captured) == 1
    assert captured[0].dotenv_path == str(env_file)


@pytest.mark.os_agnostic
def test_env_file_not_specified_passes_none_dotenv_path(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config_with_dotenv_capture: Callable[[Config, list[CapturedGetConfigArgs]], Callable[[], AppServices]],
) -> None:
    """Without --env-file, dotenv_path is None (upward search used)."""
    config = config_factory({})
    captured: list[CapturedGetConfigArgs] = []

    factory = inject_config_with_dotenv_capture(config, captured)

    result: Result = cli_runner.invoke(cli_mod.cli, ["info"], obj=factory)

    assert result.exit_code == 0
    assert len(captured) == 1
    assert captured[0].dotenv_path is None


@pytest.mark.os_agnostic
def test_env_file_combined_with_profile(
    cli_runner: CliRunner,
    tmp_path: Path,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config_with_dotenv_capture: Callable[[Config, list[CapturedGetConfigArgs]], Callable[[], AppServices]],
) -> None:
    """--env-file and --profile can be used together."""
    env_file = tmp_path / ".env"
    env_file.write_text("# empty\n")
    config = config_factory({})
    captured: list[CapturedGetConfigArgs] = []

    factory = inject_config_with_dotenv_capture(config, captured)

    result: Result = cli_runner.invoke(
        cli_mod.cli, ["--env-file", str(env_file), "--profile", "staging", "info"], obj=factory
    )

    assert result.exit_code == 0
    assert len(captured) == 1
    assert captured[0].dotenv_path == str(env_file)
    assert captured[0].profile == "staging"


# ======================== --env-file validation ========================


@pytest.mark.os_agnostic
def test_env_file_nonexistent_path_rejected(
    cli_runner: CliRunner,
    production_factory: Callable[[], AppServices],
) -> None:
    """--env-file with nonexistent path is rejected by Click."""
    result: Result = cli_runner.invoke(
        cli_mod.cli, ["--env-file", "/tmp/nonexistent_env_file_xyz.env", "info"], obj=production_factory
    )

    assert result.exit_code != 0
    assert "does not exist" in result.output


@pytest.mark.os_agnostic
def test_env_file_directory_rejected(
    cli_runner: CliRunner,
    tmp_path: Path,
    production_factory: Callable[[], AppServices],
) -> None:
    """--env-file with a directory path is rejected by Click."""
    result: Result = cli_runner.invoke(cli_mod.cli, ["--env-file", str(tmp_path), "info"], obj=production_factory)

    assert result.exit_code != 0


# ======================== --env-file end-to-end integration ========================


@pytest.mark.os_agnostic
def test_env_file_values_appear_in_config(
    cli_runner: CliRunner,
    tmp_path: Path,
    clear_config_cache: None,
    production_factory: Callable[[], AppServices],
) -> None:
    """Values from an --env-file are visible in the merged config output."""
    env_file = tmp_path / ".env"
    env_file.write_text("LIB_LOG_RICH__ENVIRONMENT=from-env-file\n")

    result: Result = cli_runner.invoke(
        cli_mod.cli,
        ["--env-file", str(env_file), "config", "--format", "json", "--section", "lib_log_rich"],
        obj=production_factory,
    )

    assert result.exit_code == 0
    assert "from-env-file" in result.stdout
