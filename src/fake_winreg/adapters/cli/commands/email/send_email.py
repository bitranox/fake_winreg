"""Send email CLI command.

Provides the send-email command with HTML and attachment support.
"""

from __future__ import annotations

import functools
import logging
from pathlib import Path

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


def _log_send_email_start(
    recipients: list[str] | None,
    subject: str,
    body_html: str,
    attachments: tuple[str, ...],
) -> None:
    """Log the start of an email send operation.

    Args:
        recipients: Email recipients, or None when using config defaults.
        subject: Email subject.
        body_html: HTML body content.
        attachments: Attachment file paths.
    """
    logger.info(
        "Sending email",
        extra={
            "recipients": recipients,
            "subject": subject,
            "has_html": bool(body_html),
            "attachment_count": len(attachments) if attachments else 0,
        },
    )


@click.command("send-email", context_settings=CLICK_CONTEXT_SETTINGS)
@click.option(
    "--to",
    "recipients",
    multiple=True,
    required=False,
    help="Recipient email address (can specify multiple; uses config default if not specified)",
)
@click.option("--subject", required=True, help="Email subject line")
@click.option("--body", default="", help="Plain-text email body")
@click.option("--body-html", default="", help="HTML email body (sent as multipart with plain text)")
@click.option(
    "--from", "from_address", default=None, help="Override sender address (uses config default if not specified)"
)
@click.option(
    "--attachment",
    "attachments",
    multiple=True,
    type=click.Path(path_type=str),
    help="File to attach (can specify multiple)",
)
@smtp_config_options
@click.pass_context
def cli_send_email(
    ctx: click.Context,
    recipients: tuple[str, ...],
    subject: str,
    body: str,
    body_html: str,
    from_address: str | None,
    attachments: tuple[str, ...],
    smtp_hosts: tuple[str, ...],
    smtp_username: str | None,
    smtp_password: str | None,
    use_starttls: bool | None,
    timeout: float | None,
    raise_on_missing_attachments: bool | None,
    raise_on_invalid_recipient: bool | None,
) -> None:
    """Send an email using configured SMTP settings.

    Example:
        >>> from click.testing import CliRunner
        >>> runner = CliRunner()
        >>> # Real invocation tested in test_cli_email.py
    """
    cli_ctx = get_cli_context(ctx)
    resolved_recipients = list(recipients) if recipients else None
    extra = {"command": "send-email", "recipients": resolved_recipients, "subject": subject}

    with lib_log_rich.runtime.bind(job_id="cli-send-email", extra=extra):
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
        attachment_paths = [Path(p) for p in attachments] if attachments else None

        _log_send_email_start(resolved_recipients, subject, body_html, attachments)
        execute_with_email_error_handling(
            operation=functools.partial(
                cli_ctx.services.send_email,
                config=email_config,
                recipients=resolved_recipients,
                subject=subject,
                body=body,
                body_html=body_html,
                from_address=from_address,
                attachments=attachment_paths,
            ),
            recipients=resolved_recipients,
            message_type="Email",
            catches_file_not_found=True,
        )


__all__ = ["cli_send_email"]
