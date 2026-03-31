"""Domain error types: instantiation and message preservation."""

from __future__ import annotations

import pytest

from fake_winreg.domain.errors import (
    ConfigurationError,
    DeliveryError,
    InvalidRecipientError,
)


@pytest.mark.os_agnostic
def test_configuration_error_preserves_message() -> None:
    """Instantiation stores the message for display."""
    exc = ConfigurationError("SMTP hosts not configured")
    assert str(exc) == "SMTP hosts not configured"


@pytest.mark.os_agnostic
def test_delivery_error_preserves_message() -> None:
    """Instantiation stores the SMTP failure detail."""
    exc = DeliveryError("Connection refused on smtp.example.com:587")
    assert str(exc) == "Connection refused on smtp.example.com:587"


@pytest.mark.os_agnostic
def test_invalid_recipient_error_preserves_message() -> None:
    """Instantiation stores the validation detail."""
    exc = InvalidRecipientError("bad@@example.com")
    assert str(exc) == "bad@@example.com"


@pytest.mark.os_agnostic
def test_invalid_recipient_error_is_value_error() -> None:
    """InvalidRecipientError is a subclass of ValueError for backward compat."""
    with pytest.raises(ValueError, match="missing domain"):
        raise InvalidRecipientError("missing domain")
