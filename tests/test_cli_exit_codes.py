"""Exit code integration tests."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from click.testing import CliRunner, Result
from lib_layered_config import Config

from fake_winreg.adapters import cli as cli_mod

if TYPE_CHECKING:
    from conftest import EmailCliContext


@pytest.mark.os_agnostic
def test_when_config_section_is_invalid_it_exits_with_code_22(
    cli_runner: CliRunner,
    production_factory: Callable[[], Any],
) -> None:
    """Config --section with nonexistent section must exit with INVALID_ARGUMENT (22)."""
    result: Result = cli_runner.invoke(
        cli_mod.cli, ["config", "--section", "nonexistent_section_that_does_not_exist"], obj=production_factory
    )

    assert result.exit_code == 22
    assert "not found" in result.stderr


@pytest.mark.os_agnostic
def test_when_config_deploy_has_permission_error_it_exits_with_code_13(
    cli_runner: CliRunner,
    inject_deploy_configuration: Callable[[Callable[..., list[Path]]], Callable[[], Any]],
) -> None:
    """Config-deploy PermissionError must exit with PERMISSION_DENIED (13)."""

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

    assert result.exit_code == 13
    assert "Permission denied" in result.stderr


@pytest.mark.os_agnostic
def test_when_config_deploy_has_generic_error_it_exits_with_code_1(
    cli_runner: CliRunner,
    inject_deploy_configuration: Callable[[Callable[..., list[Path]]], Callable[[], Any]],
) -> None:
    """Config-deploy generic Exception must exit with GENERAL_ERROR (1)."""

    def mock_deploy(
        *,
        targets: Any,
        force: bool = False,
        profile: str | None = None,
        set_permissions: bool = True,
        dir_mode: int | None = None,
        file_mode: int | None = None,
    ) -> list[Any]:
        raise OSError("Disk full")

    factory = inject_deploy_configuration(mock_deploy)

    result: Result = cli_runner.invoke(cli_mod.cli, ["config-deploy", "--target", "user"], obj=factory)

    assert result.exit_code == 1
    assert "Disk full" in result.stderr


@pytest.mark.os_agnostic
def test_when_email_has_no_smtp_hosts_it_exits_with_code_78(
    cli_runner: CliRunner,
    config_factory: Callable[[dict[str, Any]], Config],
    inject_config: Callable[[Config], Callable[[], Any]],
) -> None:
    """Send-email with no SMTP hosts configured must exit with CONFIG_ERROR (78)."""
    factory = inject_config(config_factory({"email": {}}))

    result: Result = cli_runner.invoke(
        cli_mod.cli,
        ["send-email", "--to", "a@b.com", "--subject", "x", "--body", "y"],
        obj=factory,
    )

    assert result.exit_code == 78
    assert "No SMTP hosts configured" in result.output


@pytest.mark.os_agnostic
def test_when_email_smtp_fails_it_exits_with_code_69(
    cli_runner: CliRunner,
    email_cli_context: Callable[[dict[str, Any]], EmailCliContext],
) -> None:
    """Send-email failure must exit with SMTP_FAILURE (69)."""
    ctx = email_cli_context({"smtp_hosts": ["smtp.test.com:587"], "from_address": "sender@test.com"})
    ctx.spy.should_fail = True

    result: Result = cli_runner.invoke(
        cli_mod.cli,
        ["send-email", "--to", "a@b.com", "--subject", "x", "--body", "y"],
        obj=ctx.factory,
    )

    assert result.exit_code == 69
    assert "failed" in (result.output + (result.stderr or "")).lower()


@pytest.mark.os_agnostic
def test_when_email_send_returns_false_it_exits_with_code_69(
    cli_runner: CliRunner,
    email_cli_context: Callable[[dict[str, Any]], EmailCliContext],
) -> None:
    """Send-email returning False must exit with SMTP_FAILURE (69)."""
    ctx = email_cli_context({"smtp_hosts": ["smtp.test.com:587"], "from_address": "sender@test.com"})
    ctx.spy.should_fail = True

    result: Result = cli_runner.invoke(
        cli_mod.cli,
        ["send-email", "--to", "a@b.com", "--subject", "x", "--body", "y"],
        obj=ctx.factory,
    )

    assert result.exit_code == 69
    assert "sending failed" in (result.output + (result.stderr or "")).lower()


@pytest.mark.os_agnostic
def test_when_email_has_unexpected_error_it_exits_with_code_1(
    cli_runner: CliRunner,
    email_cli_context: Callable[[dict[str, Any]], EmailCliContext],
) -> None:
    """Send-email unexpected Exception must exit with GENERAL_ERROR (1)."""
    ctx = email_cli_context({"smtp_hosts": ["smtp.test.com:587"], "from_address": "sender@test.com"})
    ctx.spy.raise_exception = TypeError("unexpected type error")

    result: Result = cli_runner.invoke(
        cli_mod.cli,
        ["send-email", "--to", "a@b.com", "--subject", "x", "--body", "y"],
        obj=ctx.factory,
    )

    assert result.exit_code == 1
    assert "unexpected type error" in (result.output + (result.stderr or ""))
