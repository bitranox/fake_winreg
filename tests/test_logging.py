"""Tests for the logging configuration model.

LoggingConfigModel validation is tested here. The init_logging function
is tested via CLI integration tests in test_cli_core.py.
"""

from __future__ import annotations

import pytest

from fake_winreg.adapters.logging.setup import LoggingConfigModel


@pytest.mark.os_agnostic
def test_logging_config_model_allows_extra_fields() -> None:
    """Extra fields pass through for lib_log_rich RuntimeConfig."""
    parsed = LoggingConfigModel.model_validate({"service": "test", "environment": "dev", "custom_field": "value"})

    assert parsed.service == "test"
    assert parsed.environment == "dev"
    extra = parsed.model_dump(exclude={"service", "environment"}, exclude_none=True)
    assert extra == {"custom_field": "value"}


@pytest.mark.os_agnostic
def test_logging_config_model_defaults() -> None:
    """Empty input produces sensible defaults."""
    parsed = LoggingConfigModel.model_validate({})

    assert parsed.service is None
    assert parsed.environment == "prod"
