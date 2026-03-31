"""Send notification CLI command.

Provides the send-notification command for simple plain-text emails.
"""

from __future__ import annotations

import functools
import logging

import lib_log_rich.runtime
import rich_click as click
from pydantic import ValidationError

from ...constants import CLICK_CONTEXT_SETTINGS
from ...context import get_cli_context
from ._common import (
    apply_validated_overrides,
    execute_with_email_error_handling,
    filter_sentinels,
    handle_validation_error,
    load_and_validate_email_config,
    smtp_config_options,
)

logger = logging.getLogger(__name__)


@click.command("send-notification", context_settings=CLICK_CONTEXT_SETTINGS)
@click.option(
    "--to",
    "recipients",
    multiple=True,
    required=False,
    help="Recipient email address (can specify multiple; uses config default if not specified)",
)
@click.option("--subject", required=True, help="Notification subject line")
@click.option("--message", required=True, help="Notification message (plain text)")
@click.option(
    "--from", "from_address", default=None, help="Override sender address (uses config default if not specified)"
)
@smtp_config_options
@click.pass_context
def cli_send_notification(
    ctx: click.Context,
    recipients: tuple[str, ...],
    subject: str,
    message: str,
    from_address: str | None,
    smtp_hosts: tuple[str, ...],
    smtp_username: str | None,
    smtp_password: str | None,
    use_starttls: bool | None,
    timeout: float | None,
    raise_on_missing_attachments: bool | None,
    raise_on_invalid_recipient: bool | None,
) -> None:
    """Send a simple plain-text notification email.

    Example:
        >>> from click.testing import CliRunner
        >>> runner = CliRunner()
        >>> # Real invocation tested in test_cli_email.py
    """
    cli_ctx = get_cli_context(ctx)
    resolved_recipients = list(recipients) if recipients else None
    extra = {"command": "send-notification", "recipients": resolved_recipients, "subject": subject}

    with lib_log_rich.runtime.bind(job_id="cli-send-notification", extra=extra):
        email_config = load_and_validate_email_config(cli_ctx.config, cli_ctx.services.load_email_config_from_dict)
        overrides = filter_sentinels(
            smtp_hosts=smtp_hosts,
            smtp_username=smtp_username,
            smtp_password=smtp_password,
            use_starttls=use_starttls,
            timeout=timeout,
            raise_on_missing_attachments=raise_on_missing_attachments,
            raise_on_invalid_recipient=raise_on_invalid_recipient,
        )
        try:
            email_config = apply_validated_overrides(email_config, overrides)
        except ValidationError as exc:
            handle_validation_error(exc)
        logger.info("Sending notification", extra={"recipients": resolved_recipients, "subject": subject})
        execute_with_email_error_handling(
            operation=functools.partial(
                cli_ctx.services.send_notification,
                config=email_config,
                recipients=resolved_recipients,
                subject=subject,
                message=message,
                from_address=from_address,
            ),
            recipients=resolved_recipients,
            message_type="Notification",
        )


__all__ = ["cli_send_notification"]
