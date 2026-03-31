"""CLI config stories: display, JSON format, sections, deploy, profile, generate-examples, redaction."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner, Result
from lib_layered_config import Config

from fake_winreg.adapters import cli as cli_mod
from fake_winreg.adapters.config import loader as config_mod


@pytest.mark.os_agnostic
def test_when_config_is_invoked_it_displays_configuration(
    cli_runner: CliRunner,
    production_factory: Callable[[], Any],
) -> None:
    """Verify config command displays configuration."""
    result: Result = cli_runner.invoke(cli_mod.cli, ["config"], obj=production_factory)

    assert result.exit_code == 0
    # With default config (all commented), output may be empty or show only log messages


@pytest.mark.os_agnostic
def test_when_config_is_invoked_with_json_format_it_outputs_json(
    cli_runner: CliRunner,
    production_factory: Callable[[], Any],
) -> None:
    """Verify config --format json outputs JSON."""
    result: Result = cli_runner.invoke(cli_mod.cli, ["config", "--format", "json"], obj=production_factory)

    assert result.exit_code == 0
    # Use result.stdout to avoid async log messages from stderr
    assert "{" in result.stdout


@pytest.mark.os_agnostic
def test_when_config_is_invoked_with_nonexistent_section_it_fails(
    cli_runner: CliRunner,
    production_factory: Callable[[], Any],
) -> None:
    """Verify config with nonexistent section returns error."""
    result: Result = cli_runner.invoke(
        cli_mod.cli, ["config", "--section", "nonexistent_section_that_does_not_exist"], obj=production_factory
    )

    assert result.exit_code != 0
    assert "not found" in result.stderr


@pytest.mark.os_agnostic
def test_when_config_is_invoked_with_mocked_data_it_displays_sections(
    cli_runner: CliRunner,
    config_cli_context: Callable[[dict[str, Any]], Callable[[], Any]],
) -> None:
    """Verify config displays sections from mocked configuration."""
    factory = config_cli_context(
        {
            "test_section": {
                "setting1": "value1",
                "setting2": 42,
            }
        }
    )

    result: Result = cli_runner.invoke(cli_mod.cli, ["config"], obj=factory)

    assert result.exit_code == 0
    assert "test_section" in result.output
    assert "setting1" in result.output
    assert "value1" in result.output


@pytest.mark.os_agnostic
def test_when_config_is_invoked_with_json_format_and_section_it_shows_section(
    cli_runner: CliRunner,
    config_cli_context: Callable[[dict[str, Any]], Callable[[], Any]],
) -> None:
    """Verify JSON format displays specific section content."""
    factory = config_cli_context(
        {
            "email": {
                "smtp_hosts": ["smtp.test.com:587"],
                "from_address": "test@example.com",
            }
        }
    )

    result: Result = cli_runner.invoke(cli_mod.cli, ["config", "--format", "json", "--section", "email"], obj=factory)

    assert result.exit_code == 0
    assert "email" in result.output
    assert "smtp_hosts" in result.output
    assert "smtp.test.com:587" in result.output


@pytest.mark.os_agnostic
def test_when_config_is_invoked_with_json_format_and_nonexistent_section_it_fails(
    cli_runner: CliRunner,
    config_cli_context: Callable[[dict[str, Any]], Callable[[], Any]],
) -> None:
    """Verify JSON format with nonexistent section returns error."""
    factory = config_cli_context(
        {
            "email": {
                "smtp_hosts": ["smtp.test.com:587"],
            }
        }
    )

    result: Result = cli_runner.invoke(
        cli_mod.cli, ["config", "--format", "json", "--section", "nonexistent"], obj=factory
    )

    assert result.exit_code != 0
    assert "not found" in result.stderr


@pytest.mark.os_agnostic
def test_when_config_is_invoked_with_section_showing_complex_values(
    cli_runner: CliRunner,
    config_cli_context: Callable[[dict[str, Any]], Callable[[], Any]],
) -> None:
    """Verify human format with section containing lists and dicts."""
    factory = config_cli_context(
        {
            "email": {
                "smtp_hosts": ["smtp1.test.com:587", "smtp2.test.com:587"],
                "from_address": "test@example.com",
                "metadata": {"key1": "value1", "key2": "value2"},
                "timeout": 60.0,
            }
        }
    )

    result: Result = cli_runner.invoke(cli_mod.cli, ["config", "--section", "email"], obj=factory)

    assert result.exit_code == 0
    assert "[email]" in result.output
    assert "smtp_hosts" in result.output
    assert "smtp1.test.com:587" in result.output
    assert "smtp2.test.com:587" in result.output
    assert "metadata" in result.output
    assert '"test@example.com"' in result.output
    assert "60.0" in result.output


@pytest.mark.os_agnostic
def test_when_config_shows_all_sections_with_complex_values(
    cli_runner: CliRunner,
    config_cli_context: Callable[[dict[str, Any]], Callable[[], Any]],
) -> None:
    """Verify human format showing all sections with lists and dicts."""
    factory = config_cli_context(
        {
            "email": {
                "smtp_hosts": ["smtp.test.com:587"],
                "tags": {"environment": "test", "version": "1.0"},
            },
            "logging": {
                "level": "DEBUG",
                "handlers": ["console", "file"],
            },
        }
    )

    result: Result = cli_runner.invoke(cli_mod.cli, ["config"], obj=factory)

    assert result.exit_code == 0
    assert "[email]" in result.output
    assert "[logging]" in result.output
    assert "smtp_hosts" in result.output
    assert "handlers" in result.output
    assert "tags" in result.output


@pytest.mark.os_agnostic
def test_when_config_deploy_is_invoked_without_target_it_fails(
    cli_runner: CliRunner,
    production_factory: Callable[[], Any],
) -> None:
    """Verify config-deploy without --target option fails."""
    result: Result = cli_runner.invoke(cli_mod.cli, ["config-deploy"], obj=production_factory)

    assert result.exit_code != 0
    assert "Missing option" in result.output or "required" in result.output.lower()


@pytest.mark.os_agnostic
def test_when_config_deploy_is_invoked_it_deploys_configuration(
    cli_runner: CliRunner,
    tmp_path: Any,
    inject_deploy_configuration: Callable[[Callable[..., list[Path]]], Callable[[], Any]],
) -> None:
    """Verify config-deploy creates configuration files."""
    deployed_path = tmp_path / "config.toml"
    deployed_path.touch()

    def mock_deploy(
        *,
        targets: Any,
        force: bool = False,
        profile: str | None = None,
        set_permissions: bool = True,
        dir_mode: int | None = None,
        file_mode: int | None = None,
    ) -> list[Path]:
        return [deployed_path]

    factory = inject_deploy_configuration(mock_deploy)

    result: Result = cli_runner.invoke(cli_mod.cli, ["config-deploy", "--target", "user"], obj=factory)

    assert result.exit_code == 0
    assert "Configuration deployed successfully" in result.output
    assert str(deployed_path) in result.output


@pytest.mark.os_agnostic
def test_when_config_deploy_finds_no_files_to_create_it_informs_user(
    cli_runner: CliRunner,
    inject_deploy_configuration: Callable[[Callable[..., list[Path]]], Callable[[], Any]],
) -> None:
    """Verify config-deploy reports when no files are created."""

    def mock_deploy(
        *,
        targets: Any,
        force: bool = False,
        profile: str | None = None,
        set_permissions: bool = True,
        dir_mode: int | None = None,
        file_mode: int | None = None,
    ) -> list[Path]:
        return []

    factory = inject_deploy_configuration(mock_deploy)

    result: Result = cli_runner.invoke(cli_mod.cli, ["config-deploy", "--target", "user"], obj=factory)

    assert result.exit_code == 0
    assert "No files were created" in result.output
    assert "--force" in result.output


@pytest.mark.os_agnostic
def test_when_config_deploy_encounters_permission_error_it_handles_gracefully(
    cli_runner: CliRunner,
    inject_deploy_configuration: Callable[[Callable[..., list[Path]]], Callable[[], Any]],
) -> None:
    """Verify config-deploy handles PermissionError gracefully."""

    def mock_deploy(
        *,
        targets: Any,
        force: bool = False,
        profile: str | None = None,
        set_permissions: bool = True,
        dir_mode: int | None = None,
        file_mode: int | None = None,
    ) -> list[Any]:
        raise PermissionError("Permission denied")

    factory = inject_deploy_configuration(mock_deploy)

    result: Result = cli_runner.invoke(cli_mod.cli, ["config-deploy", "--target", "app"], obj=factory)

    assert result.exit_code != 0
    assert "Permission denied" in result.stderr
    assert "sudo" in result.stderr.lower()


@pytest.mark.os_agnostic
def test_when_config_deploy_supports_multiple_targets(
    cli_runner: CliRunner,
    tmp_path: Any,
    inject_deploy_configuration: Callable[[Callable[..., list[Path]]], Callable[[], Any]],
) -> None:
    """Verify config-deploy accepts multiple --target options."""
    from fake_winreg.domain.enums import DeployTarget

    path1 = tmp_path / "config1.toml"
    path2 = tmp_path / "config2.toml"
    path1.touch()
    path2.touch()

    def mock_deploy(
        *,
        targets: Any,
        force: bool = False,
        profile: str | None = None,
        set_permissions: bool = True,
        dir_mode: int | None = None,
        file_mode: int | None = None,
    ) -> list[Path]:
        target_values = [t.value if isinstance(t, DeployTarget) else t for t in targets]
        assert len(target_values) == 2
        assert "user" in target_values
        assert "host" in target_values
        return [path1, path2]

    factory = inject_deploy_configuration(mock_deploy)

    result: Result = cli_runner.invoke(
        cli_mod.cli, ["config-deploy", "--target", "user", "--target", "host"], obj=factory
    )

    assert result.exit_code == 0
    assert str(path1) in result.output
    assert str(path2) in result.output


@pytest.mark.os_agnostic
def test_when_config_deploy_is_invoked_with_profile_it_passes_profile(
    cli_runner: CliRunner,
    tmp_path: Any,
    inject_deploy_with_profile_capture: Callable[[Path, list[str | None]], Callable[[], Any]],
) -> None:
    """Verify config-deploy passes profile to deploy_configuration."""
    deployed_path = tmp_path / "config.toml"
    deployed_path.touch()
    captured_profile: list[str | None] = []

    factory = inject_deploy_with_profile_capture(deployed_path, captured_profile)

    result: Result = cli_runner.invoke(
        cli_mod.cli, ["config-deploy", "--target", "user", "--profile", "production"], obj=factory
    )

    assert result.exit_code == 0
    assert captured_profile == ["production"]
    assert "(profile: production)" in result.output


@pytest.mark.os_agnostic
def test_when_config_is_invoked_with_profile_it_passes_profile_to_get_config(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config_with_profile_capture: Callable[[Config, list[str | None]], Callable[[], Any]],
) -> None:
    """Verify config command passes --profile to get_config."""
    captured_profiles: list[str | None] = []
    config = config_factory({"test_section": {"key": "value"}})

    factory = inject_config_with_profile_capture(config, captured_profiles)

    result: Result = cli_runner.invoke(cli_mod.cli, ["config", "--profile", "staging"], obj=factory)

    assert result.exit_code == 0
    assert "staging" in captured_profiles


@pytest.mark.os_agnostic
def test_when_config_is_invoked_without_profile_it_passes_none(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config_with_profile_capture: Callable[[Config, list[str | None]], Callable[[], Any]],
) -> None:
    """Verify config command passes None when no --profile specified."""
    captured_profiles: list[str | None] = []
    config = config_factory({"test_section": {"key": "value"}})

    factory = inject_config_with_profile_capture(config, captured_profiles)

    result: Result = cli_runner.invoke(cli_mod.cli, ["config"], obj=factory)

    assert result.exit_code == 0
    assert None in captured_profiles


@pytest.mark.os_agnostic
def test_when_config_deploy_is_invoked_without_profile_it_passes_none(
    cli_runner: CliRunner,
    tmp_path: Any,
    inject_deploy_with_profile_capture: Callable[[Path, list[str | None]], Callable[[], Any]],
) -> None:
    """Verify config-deploy passes None when no --profile specified."""
    deployed_path = tmp_path / "config.toml"
    deployed_path.touch()
    captured_profiles: list[str | None] = []

    factory = inject_deploy_with_profile_capture(deployed_path, captured_profiles)

    result: Result = cli_runner.invoke(cli_mod.cli, ["config-deploy", "--target", "user"], obj=factory)

    assert result.exit_code == 0
    assert captured_profiles == [None]
    assert "(profile:" not in result.output


# ======================== Config Display Redaction Tests ========================


@pytest.mark.os_agnostic
def test_when_config_displays_human_format_it_redacts_password(
    cli_runner: CliRunner,
    config_cli_context: Callable[[dict[str, Any]], Callable[[], Any]],
) -> None:
    """Human-readable output must redact sensitive keys like smtp_password."""
    factory = config_cli_context(
        {
            "email": {
                "smtp_password": "super_secret_123",
                "from_address": "test@example.com",
            }
        }
    )

    result: Result = cli_runner.invoke(cli_mod.cli, ["config"], obj=factory)

    assert result.exit_code == 0
    assert "super_secret_123" not in result.output
    assert "***REDACTED***" in result.output
    assert "from_address" in result.output
    assert "test@example.com" in result.output


@pytest.mark.os_agnostic
def test_when_config_displays_json_format_it_redacts_password(
    cli_runner: CliRunner,
    config_cli_context: Callable[[dict[str, Any]], Callable[[], Any]],
) -> None:
    """JSON output must redact sensitive keys like smtp_password."""
    factory = config_cli_context(
        {
            "email": {
                "smtp_password": "super_secret_123",
                "from_address": "test@example.com",
            }
        }
    )

    result: Result = cli_runner.invoke(cli_mod.cli, ["config", "--format", "json"], obj=factory)

    assert result.exit_code == 0
    assert "super_secret_123" not in result.stdout
    assert "***REDACTED***" in result.stdout
    assert "from_address" in result.stdout


@pytest.mark.os_agnostic
def test_when_config_displays_non_sensitive_values_it_shows_them(
    cli_runner: CliRunner,
    config_cli_context: Callable[[dict[str, Any]], Callable[[], Any]],
) -> None:
    """Non-sensitive keys must show their real values, not be redacted."""
    factory = config_cli_context(
        {
            "logging": {
                "level": "DEBUG",
                "service": "my_app",
            }
        }
    )

    result: Result = cli_runner.invoke(cli_mod.cli, ["config"], obj=factory)

    assert result.exit_code == 0
    assert "DEBUG" in result.output
    assert "my_app" in result.output
    assert "***REDACTED***" not in result.output


@pytest.mark.os_agnostic
def test_when_config_displays_token_and_secret_keys_it_redacts_them(
    cli_runner: CliRunner,
    config_cli_context: Callable[[dict[str, Any]], Callable[[], Any]],
) -> None:
    """Keys containing 'token', 'secret', or 'credential' must be redacted."""
    factory = config_cli_context(
        {
            "auth": {
                "api_token": "tok_abc123",
                "client_secret": "sec_xyz789",
                "username": "admin",
            }
        }
    )

    result: Result = cli_runner.invoke(cli_mod.cli, ["config"], obj=factory)

    assert result.exit_code == 0
    assert "tok_abc123" not in result.output
    assert "sec_xyz789" not in result.output
    assert "admin" in result.output


@pytest.mark.os_agnostic
def test_when_config_displays_password_in_list_of_dicts_it_redacts(
    cli_runner: CliRunner,
    config_cli_context: Callable[[dict[str, Any]], Callable[[], Any]],
) -> None:
    """Sensitive keys inside dicts nested in lists must be redacted."""
    factory = config_cli_context(
        {
            "connections": {
                "servers": [
                    {"host": "smtp.example.com", "password": "secret123"},
                    {"host": "backup.example.com", "password": "secret456"},
                ],
                "name": "production",
            }
        }
    )

    result: Result = cli_runner.invoke(cli_mod.cli, ["config", "--format", "json"], obj=factory)

    assert result.exit_code == 0
    assert "secret123" not in result.stdout
    assert "secret456" not in result.stdout
    assert "smtp.example.com" in result.stdout
    assert "REDACTED" in result.stdout


@pytest.mark.os_agnostic
def test_when_config_generate_examples_is_invoked_it_creates_files(
    cli_runner: CliRunner,
    tmp_path: Any,
    monkeypatch: pytest.MonkeyPatch,
    production_factory: Callable[[], Any],
) -> None:
    """Verify config-generate-examples creates files in the target directory."""
    created_file = tmp_path / "example.toml"
    created_file.touch()

    def mock_generate_examples(
        destination: str | Path, *, slug: str, vendor: str, app: str, force: bool = False, platform: str | None = None
    ) -> list[Path]:
        return [created_file]

    monkeypatch.setattr("fake_winreg.adapters.cli.commands.config.generate_examples", mock_generate_examples)

    result: Result = cli_runner.invoke(
        cli_mod.cli,
        ["config-generate-examples", "--destination", str(tmp_path)],
        obj=production_factory,
    )

    assert result.exit_code == 0
    assert "Generated 1 example file(s)" in result.output
    assert str(created_file) in result.output


@pytest.mark.os_agnostic
def test_when_config_generate_examples_has_no_files_it_informs_user(
    cli_runner: CliRunner,
    tmp_path: Any,
    monkeypatch: pytest.MonkeyPatch,
    production_factory: Callable[[], Any],
) -> None:
    """Verify config-generate-examples reports when all files already exist."""

    def mock_generate_examples(
        destination: str | Path, *, slug: str, vendor: str, app: str, force: bool = False, platform: str | None = None
    ) -> list[Path]:
        return []

    monkeypatch.setattr("fake_winreg.adapters.cli.commands.config.generate_examples", mock_generate_examples)

    result: Result = cli_runner.invoke(
        cli_mod.cli,
        ["config-generate-examples", "--destination", str(tmp_path)],
        obj=production_factory,
    )

    assert result.exit_code == 0
    assert "No files generated" in result.output
    assert "--force" in result.output


@pytest.mark.os_agnostic
def test_when_config_generate_examples_missing_destination_it_fails(
    cli_runner: CliRunner,
    production_factory: Callable[[], Any],
) -> None:
    """Verify config-generate-examples without --destination fails."""
    result: Result = cli_runner.invoke(cli_mod.cli, ["config-generate-examples"], obj=production_factory)

    assert result.exit_code != 0
    assert "Missing option" in result.output or "required" in result.output.lower()


@pytest.mark.os_agnostic
def test_when_config_generate_examples_with_force_it_passes_force_flag(
    cli_runner: CliRunner,
    tmp_path: Any,
    monkeypatch: pytest.MonkeyPatch,
    production_factory: Callable[[], Any],
) -> None:
    """Verify config-generate-examples passes --force flag to generate_examples."""
    captured_force: list[bool] = []
    created_file = tmp_path / "example.toml"
    created_file.touch()

    def mock_generate_examples(
        destination: str | Path, *, slug: str, vendor: str, app: str, force: bool = False, platform: str | None = None
    ) -> list[Path]:
        captured_force.append(force)
        return [created_file]

    monkeypatch.setattr("fake_winreg.adapters.cli.commands.config.generate_examples", mock_generate_examples)

    result: Result = cli_runner.invoke(
        cli_mod.cli,
        ["config-generate-examples", "--destination", str(tmp_path), "--force"],
        obj=production_factory,
    )

    assert result.exit_code == 0
    assert captured_force == [True]


@pytest.mark.os_agnostic
def test_when_config_generate_examples_without_force_it_defaults_to_false(
    cli_runner: CliRunner,
    tmp_path: Any,
    monkeypatch: pytest.MonkeyPatch,
    production_factory: Callable[[], Any],
) -> None:
    """Verify config-generate-examples defaults force=False."""
    captured_force: list[bool] = []
    created_file = tmp_path / "example.toml"
    created_file.touch()

    def mock_generate_examples(
        destination: str | Path, *, slug: str, vendor: str, app: str, force: bool = False, platform: str | None = None
    ) -> list[Path]:
        captured_force.append(force)
        return [created_file]

    monkeypatch.setattr("fake_winreg.adapters.cli.commands.config.generate_examples", mock_generate_examples)

    result: Result = cli_runner.invoke(
        cli_mod.cli,
        ["config-generate-examples", "--destination", str(tmp_path)],
        obj=production_factory,
    )

    assert result.exit_code == 0
    assert captured_force == [False]


@pytest.mark.os_agnostic
def test_when_config_generate_examples_encounters_error_it_exits_with_general_error(
    cli_runner: CliRunner,
    tmp_path: Any,
    monkeypatch: pytest.MonkeyPatch,
    production_factory: Callable[[], Any],
) -> None:
    """Verify config-generate-examples handles exceptions gracefully."""

    def mock_generate_examples(
        destination: str | Path, *, slug: str, vendor: str, app: str, force: bool = False, platform: str | None = None
    ) -> list[Path]:
        raise OSError("Disk full")

    monkeypatch.setattr("fake_winreg.adapters.cli.commands.config.generate_examples", mock_generate_examples)

    result: Result = cli_runner.invoke(
        cli_mod.cli,
        ["config-generate-examples", "--destination", str(tmp_path)],
        obj=production_factory,
    )

    assert result.exit_code == 1  # GENERAL_ERROR
    assert "Disk full" in result.stderr


@pytest.mark.os_agnostic
def test_when_config_generate_examples_it_passes_correct_metadata(
    cli_runner: CliRunner,
    tmp_path: Any,
    monkeypatch: pytest.MonkeyPatch,
    production_factory: Callable[[], Any],
) -> None:
    """Verify config-generate-examples passes correct slug, vendor, app from __init__conf__."""
    from fake_winreg import __init__conf__

    captured_params: list[dict[str, Any]] = []
    created_file = tmp_path / "example.toml"
    created_file.touch()

    def mock_generate_examples(
        destination: str | Path, *, slug: str, vendor: str, app: str, force: bool = False, platform: str | None = None
    ) -> list[Path]:
        captured_params.append({"slug": slug, "vendor": vendor, "app": app, "destination": str(destination)})
        return [created_file]

    monkeypatch.setattr("fake_winreg.adapters.cli.commands.config.generate_examples", mock_generate_examples)

    result: Result = cli_runner.invoke(
        cli_mod.cli,
        ["config-generate-examples", "--destination", str(tmp_path)],
        obj=production_factory,
    )

    assert result.exit_code == 0
    assert len(captured_params) == 1
    assert captured_params[0]["slug"] == __init__conf__.LAYEREDCONF_SLUG
    assert captured_params[0]["vendor"] == __init__conf__.LAYEREDCONF_VENDOR
    assert captured_params[0]["app"] == __init__conf__.LAYEREDCONF_APP
    assert captured_params[0]["destination"] == str(tmp_path)


@pytest.mark.os_agnostic
def test_when_config_generate_examples_creates_multiple_files_it_lists_all(
    cli_runner: CliRunner,
    tmp_path: Any,
    monkeypatch: pytest.MonkeyPatch,
    production_factory: Callable[[], Any],
) -> None:
    """Verify config-generate-examples lists all created files."""
    file1 = tmp_path / "config.toml"
    file2 = tmp_path / "config.d" / "50-email.toml"
    file1.touch()
    file2.parent.mkdir(parents=True)
    file2.touch()

    def mock_generate_examples(
        destination: str | Path, *, slug: str, vendor: str, app: str, force: bool = False, platform: str | None = None
    ) -> list[Path]:
        return [file1, file2]

    monkeypatch.setattr("fake_winreg.adapters.cli.commands.config.generate_examples", mock_generate_examples)

    result: Result = cli_runner.invoke(
        cli_mod.cli,
        ["config-generate-examples", "--destination", str(tmp_path)],
        obj=production_factory,
    )

    assert result.exit_code == 0
    assert "Generated 2 example file(s)" in result.output
    assert str(file1) in result.output
    assert str(file2) in result.output


# ======================== --set override preservation ========================


@pytest.mark.os_agnostic
def test_when_config_subcommand_profile_reloads_it_preserves_root_set_overrides(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    monkeypatch: pytest.MonkeyPatch,
    clear_config_cache: None,
    production_factory: Callable[[], Any],
) -> None:
    """Root --set overrides must be reapplied when config --profile reloads config.

    When a user invokes:
        cli --set section.key=override config --profile test

    The subcommand-level profile triggers a config reload. The root-level
    --set overrides must be reapplied to the new config.
    """
    base_config = config_factory({"section": {"key": "original"}})

    # get_config is called twice: first in root.py, second in config.py (profile reload)
    call_count = {"value": 0}

    def mock_get_config(*, profile: str | None = None, **_kwargs: Any) -> Config:
        call_count["value"] += 1
        return base_config

    monkeypatch.setattr(config_mod, "get_config", mock_get_config)

    result: Result = cli_runner.invoke(
        cli_mod.cli,
        ["--set", "section.key=overridden", "config", "--profile", "test", "--format", "json"],
        obj=production_factory,
    )

    assert result.exit_code == 0
    # Override was applied (verify in output)
    assert "overridden" in result.stdout
    # Original value should not appear
    assert '"original"' not in result.stdout


@pytest.mark.os_agnostic
def test_when_config_subcommand_has_no_profile_it_uses_stored_config_with_overrides(
    cli_runner: CliRunner,
    config_cli_context: Callable[[dict[str, Any]], Callable[[], Any]],
) -> None:
    """Without subcommand --profile, config uses already-overridden config from context."""
    factory = config_cli_context({"section": {"key": "original"}})

    result: Result = cli_runner.invoke(
        cli_mod.cli,
        ["--set", "section.key=overridden", "config", "--format", "json"],
        obj=factory,
    )

    assert result.exit_code == 0
    assert "overridden" in result.stdout
    assert '"original"' not in result.stdout
