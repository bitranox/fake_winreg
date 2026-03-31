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


__all__ = [
    "ConfigurationError",
]
