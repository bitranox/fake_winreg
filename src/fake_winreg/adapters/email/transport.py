"""SMTP email transport functions.

Provides the send_email and send_notification functions that handle
SMTP communication via btx_lib_mail.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from pathlib import Path

from btx_lib_mail.lib_mail import send as btx_send

from fake_winreg.domain.errors import ConfigurationError, DeliveryError

from .config import EmailConfig
from .validation import validate_recipients

logger = logging.getLogger(__name__)

# Keywords that may indicate sensitive data in exception messages
_SENSITIVE_KEYWORDS = frozenset(
    {
        "api_key",
        "auth",
        "bearer",
        "credential",
        "key",
        "login",
        "password",
        "secret",
        "token",
    }
)


def _sanitize_exception_message(exc: Exception) -> str:
    """Sanitize exception message to prevent credential exposure.

    Returns a generic message when the original exception text contains
    keywords suggesting sensitive data (passwords, credentials, tokens).
    The full exception is preserved in the chain for DEBUG-level logging.

    Args:
        exc: The exception to sanitize.

    Returns:
        Sanitized message safe for user display.

    Example:
        >>> class FakeExc(Exception): pass
        >>> _sanitize_exception_message(FakeExc("Connection failed"))
        'Connection failed'
        >>> _sanitize_exception_message(FakeExc("Auth password rejected"))
        'Email delivery failed. Check SMTP configuration.'
    """
    message = str(exc).lower()
    if any(keyword in message for keyword in _SENSITIVE_KEYWORDS):
        return "Email delivery failed. Check SMTP configuration."
    return str(exc)


def _build_credentials(config: EmailConfig) -> tuple[str, str] | None:
    """Return (username, password) tuple when both are set, else None."""
    if config.smtp_username is not None and config.smtp_password is not None:
        return (config.smtp_username, config.smtp_password)
    return None


def _resolve_sender(config: EmailConfig, from_address: str | None) -> str:
    """Determine the sender address from override or config default.

    Args:
        config: Email configuration with optional default from_address.
        from_address: Explicit override, or None to use config default.

    Returns:
        Resolved sender address.

    Raises:
        ValueError: When neither override nor config provides a from_address.
    """
    sender = from_address if from_address is not None else config.from_address
    if sender is None:
        raise ValueError("No from_address configured and no override provided")
    return sender


def _resolve_recipients(
    config: EmailConfig,
    recipients: str | Sequence[str] | None,
) -> list[str]:
    """Normalize recipients from override or config default.

    Args:
        config: Email configuration with optional default recipients.
        recipients: Single address, sequence of addresses, or None for config default.

    Returns:
        Non-empty list of recipient addresses.

    Raises:
        ValueError: When no recipients are available from either source.
        InvalidRecipientError: When a runtime recipient has invalid email format.
    """
    if recipients is not None:
        recipient_list = [recipients] if isinstance(recipients, str) else list(recipients)
        # Validate runtime recipients (config recipients validated by Pydantic)
        validate_recipients(recipient_list)
    else:
        recipient_list = list(config.recipients)

    if not recipient_list:
        raise ValueError("No recipients configured and no override provided")
    return recipient_list


def _validate_smtp_hosts(config: EmailConfig) -> None:
    """Ensure at least one SMTP host is configured.

    Args:
        config: Email configuration to validate.

    Raises:
        ConfigurationError: When smtp_hosts is empty.
    """
    if not config.smtp_hosts:
        raise ConfigurationError("No SMTP hosts configured (email.smtp_hosts is empty)")


def send_email(
    *,
    config: EmailConfig,
    recipients: str | Sequence[str] | None = None,
    subject: str,
    body: str = "",
    body_html: str = "",
    from_address: str | None = None,
    attachments: Sequence[Path] | None = None,
) -> bool:
    """Send an email using configured SMTP settings.

    Provides the primary email-sending interface that integrates with
    application configuration while exposing a clean, typed API.

    Args:
        config: Email configuration containing SMTP settings and defaults.
        recipients: Single recipient address, sequence of addresses, or None to use
            config.recipients. When provided, replaces config recipients entirely.
        subject: Email subject line (UTF-8 supported).
        body: Plain-text email body.
        body_html: HTML email body (optional, sent as multipart with plain text).
        from_address: Override sender address. Uses config.from_address when None.
        attachments: Optional sequence of file paths to attach.

    Returns:
        True when delivery succeeds; False if the underlying transport
        reports partial failure without raising. Most failures raise
        exceptions rather than returning False.

    Raises:
        ValueError: No from_address configured and no override provided,
            or no recipients configured and no override provided.
        ConfigurationError: No SMTP hosts configured.
        FileNotFoundError: Required attachment missing and config.raise_on_missing_attachments
            is True.
        DeliveryError: All SMTP hosts failed for a recipient.

    Side Effects:
        Sends email via SMTP. Logs send attempts at INFO level and failures
        at ERROR level.
    """
    sender = _resolve_sender(config, from_address)
    _validate_smtp_hosts(config)
    recipient_list = _resolve_recipients(config, recipients)

    logger.info(
        "Sending email",
        extra={
            "sender": sender,
            "recipients": recipient_list,
            "subject": subject,
            "has_html": bool(body_html),
            "attachment_count": len(attachments) if attachments else 0,
        },
    )

    try:
        result = btx_send(
            mail_from=sender,
            mail_recipients=recipient_list,
            mail_subject=subject,
            mail_body=body,
            mail_body_html=body_html,
            smtphosts=config.smtp_hosts,
            attachment_file_paths=attachments,
            credentials=_build_credentials(config),
            use_starttls=config.use_starttls,
            timeout=config.timeout,
            attachment_allowed_extensions=config.attachment_allowed_extensions,
            attachment_blocked_extensions=config.attachment_blocked_extensions,
            attachment_allowed_directories=config.attachment_allowed_directories,
            attachment_blocked_directories=config.attachment_blocked_directories,
            attachment_max_size_bytes=config.attachment_max_size_bytes,
            attachment_allow_symlinks=config.attachment_allow_symlinks,
            attachment_raise_on_security_violation=config.attachment_raise_on_security_violation,
            raise_on_missing_attachments=config.raise_on_missing_attachments,
            raise_on_invalid_recipient=config.raise_on_invalid_recipient,
        )
    except RuntimeError as exc:
        logger.debug("SMTP delivery failed", exc_info=True)
        raise DeliveryError(_sanitize_exception_message(exc)) from exc

    if result:
        logger.info(
            "Email sent successfully",
            extra={"sender": sender, "recipients": recipient_list},
        )
    else:
        logger.warning(
            "Email send returned failure",
            extra={"sender": sender, "recipients": recipient_list},
        )

    return result


def send_notification(
    *,
    config: EmailConfig,
    recipients: str | Sequence[str] | None = None,
    subject: str,
    message: str,
    from_address: str | None = None,
) -> bool:
    """Send a simple plain-text notification email.

    Convenience wrapper for the common case of sending simple notifications
    without HTML or attachments.

    Args:
        config: Email configuration containing SMTP settings.
        recipients: Single recipient address, sequence of addresses, or None to use
            config.recipients. When provided, replaces config recipients entirely.
        subject: Email subject line.
        message: Plain-text notification message.
        from_address: Override sender address. Uses config.from_address when None.

    Returns:
        True when delivery succeeds; False if the underlying transport
        reports partial failure without raising.

    Raises:
        ValueError: No recipients configured and no override provided.
        ConfigurationError: No SMTP hosts configured.
        DeliveryError: All SMTP hosts failed for a recipient.

    Side Effects:
        Sends email via SMTP. Logs send attempts.
    """
    return send_email(
        config=config,
        recipients=recipients,
        subject=subject,
        body=message,
        from_address=from_address,
    )


__all__ = [
    "send_email",
    "send_notification",
]
