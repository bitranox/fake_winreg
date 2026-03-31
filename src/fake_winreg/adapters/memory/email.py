"""In-memory email adapters for testing.

Provides email functions that satisfy the same Protocols as production
adapters but perform no SMTP operations.

Contents:
    * :class:`CapturedEmail` - Typed record for captured send_email calls.
    * :class:`CapturedNotification` - Typed record for captured send_notification calls.
    * :class:`EmailSpy` - Captures email calls for test assertions.
    * :func:`load_email_config_from_dict_in_memory` - In-memory config loader.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..email.sender import EmailConfig
from ..email.validation import validate_recipients


@dataclass(frozen=True, slots=True)
class CapturedEmail:
    """Typed record of a captured send_email call."""

    config: EmailConfig
    recipients: str | Sequence[str] | None
    subject: str
    body: str
    body_html: str
    from_address: str | None
    attachments: list[Path] | None


@dataclass(frozen=True, slots=True)
class CapturedNotification:
    """Typed record of a captured send_notification call."""

    config: EmailConfig
    recipients: str | Sequence[str] | None
    subject: str
    message: str
    from_address: str | None


@dataclass
class EmailSpy:
    """Captures email operations for test assertions.

    Each test should create its own EmailSpy instance to avoid cross-test pollution.
    The spy's send methods match the Protocol signatures expected by AppServices.

    Attributes:
        sent_emails: List of captured send_email calls.
        sent_notifications: List of captured send_notification calls.
        should_fail: When True, send operations return False to simulate failure.
        raise_exception: When set, send operations raise this exception.

    Example:
        >>> spy = EmailSpy()
        >>> config = EmailConfig(smtp_hosts=["smtp.test.com:587"])
        >>> spy.send_email(config=config, recipients="test@example.com", subject="Hi", body="Hello")
        True
        >>> len(spy.sent_emails)
        1
    """

    sent_emails: list[CapturedEmail] = field(default_factory=lambda: [])
    sent_notifications: list[CapturedNotification] = field(default_factory=lambda: [])
    should_fail: bool = False
    raise_exception: Exception | None = None

    def clear(self) -> None:
        """Reset captured data for next test."""
        self.sent_emails.clear()
        self.sent_notifications.clear()
        self.raise_exception = None

    def send_email(
        self,
        *,
        config: EmailConfig,
        recipients: str | Sequence[str] | None = None,
        subject: str,
        body: str = "",
        body_html: str = "",
        from_address: str | None = None,
        attachments: Sequence[Path] | None = None,
    ) -> bool:
        """Record the call and return success/failure based on spy state.

        Args:
            config: Email configuration (captured for assertions).
            recipients: Recipient addresses to validate and capture.
            subject: Email subject line.
            body: Plain text body.
            body_html: HTML body.
            from_address: Sender address override.
            attachments: File paths to attach.

        Returns:
            False if should_fail is True, otherwise True.

        Raises:
            InvalidRecipientError: When recipients have invalid email format.
            Exception: If raise_exception is set, raises that exception.
        """
        validate_recipients(recipients)
        self.sent_emails.append(
            CapturedEmail(
                config=config,
                recipients=recipients,
                subject=subject,
                body=body,
                body_html=body_html,
                from_address=from_address,
                attachments=list(attachments) if attachments else None,
            )
        )
        if self.raise_exception is not None:
            raise self.raise_exception
        return not self.should_fail

    def send_notification(
        self,
        *,
        config: EmailConfig,
        recipients: str | Sequence[str] | None = None,
        subject: str,
        message: str,
        from_address: str | None = None,
    ) -> bool:
        """Record the call and return success/failure based on spy state.

        Args:
            config: Email configuration (captured for assertions).
            recipients: Recipient addresses to validate and capture.
            subject: Notification subject line.
            message: Notification message body.
            from_address: Sender address override.

        Returns:
            False if should_fail is True, otherwise True.

        Raises:
            InvalidRecipientError: When recipients have invalid email format.
            Exception: If raise_exception is set, raises that exception.
        """
        validate_recipients(recipients)
        self.sent_notifications.append(
            CapturedNotification(
                config=config,
                recipients=recipients,
                subject=subject,
                message=message,
                from_address=from_address,
            )
        )
        if self.raise_exception is not None:
            raise self.raise_exception
        return not self.should_fail


def load_email_config_from_dict_in_memory(
    config_dict: Mapping[str, Any],
) -> EmailConfig:
    """Parse email config from dict using the real Pydantic model."""
    email_raw = config_dict.get("email", {})
    return EmailConfig.model_validate(email_raw if email_raw else {})


__all__ = [
    "CapturedEmail",
    "CapturedNotification",
    "EmailSpy",
    "load_email_config_from_dict_in_memory",
]
