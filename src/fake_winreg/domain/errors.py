"""Domain-specific exceptions for typed error handling at boundaries."""

from __future__ import annotations


class ConfigurationError(Exception):
    """Missing, invalid, or incomplete configuration.

    Raised when required configuration values are absent, malformed, or
    logically inconsistent. Typically caught at CLI boundaries to provide
    user-friendly error messages.

    Example:
        >>> from fake_winreg.domain.errors import ConfigurationError
        >>> err = ConfigurationError("No SMTP hosts configured")
        >>> str(err)
        'No SMTP hosts configured'
    """


class DeliveryError(Exception):
    """Email/notification delivery failed at SMTP level.

    Raised when all configured SMTP hosts fail to accept the message.
    Contains details about the delivery failure for logging and user feedback.

    Example:
        >>> from fake_winreg.domain.errors import DeliveryError
        >>> err = DeliveryError("Connection refused by smtp.example.com:587")
        >>> str(err)
        'Connection refused by smtp.example.com:587'
    """


class InvalidRecipientError(ValueError):
    """Email address validation failure.

    Raised when a recipient address fails RFC 5321/5322 validation.
    Inherits from ValueError so existing ``except ValueError`` handlers
    continue to catch it during the migration period.

    Example:
        >>> from fake_winreg.domain.errors import InvalidRecipientError
        >>> err = InvalidRecipientError("Invalid email: not-an-email")
        >>> str(err)
        'Invalid email: not-an-email'
        >>> isinstance(err, ValueError)
        True
    """


__all__ = [
    "ConfigurationError",
    "DeliveryError",
    "InvalidRecipientError",
]
