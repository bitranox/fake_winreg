"""Email validation utilities shared between production and test adapters.

Provides recipient validation that raises domain exceptions (InvalidRecipientError)
rather than library-specific exceptions.
"""

from __future__ import annotations

from collections.abc import Sequence

from btx_lib_mail import validate_email_address

from fake_winreg.domain.errors import InvalidRecipientError


def validate_recipient(recipient: str) -> None:
    """Validate a single email address.

    Args:
        recipient: Email address to validate.

    Raises:
        InvalidRecipientError: When the email address is invalid.

    Example:
        >>> validate_recipient("valid@example.com")  # no exception
        >>> validate_recipient("invalid")  # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        ...
        InvalidRecipientError: Invalid recipient: invalid
    """
    try:
        validate_email_address(recipient)
    except ValueError as e:
        raise InvalidRecipientError(f"Invalid recipient: {recipient}") from e


def validate_recipients(recipients: str | Sequence[str] | None) -> None:
    """Validate runtime recipients.

    Config-level recipients are validated by Pydantic; this validates
    recipients provided at runtime (CLI args, function parameters).

    Args:
        recipients: Single address, sequence of addresses, or None (skip validation).

    Raises:
        InvalidRecipientError: When a recipient has invalid email format.

    Example:
        >>> validate_recipients(None)  # no-op
        >>> validate_recipients("test@example.com")  # single address
        >>> validate_recipients(["a@example.com", "b@example.com"])  # multiple
    """
    if recipients is None:
        return
    recipient_list = [recipients] if isinstance(recipients, str) else list(recipients)
    for recipient in recipient_list:
        validate_recipient(recipient)


__all__ = ["validate_recipient", "validate_recipients"]
