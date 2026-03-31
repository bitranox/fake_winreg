"""Port behavioral contract tests — verify in-memory adapter implementations.

Tests exercise in-memory adapters only - production adapters are tested
via CLI integration tests. Static type conformance is enforced by pyright.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from lib_layered_config import Config

from fake_winreg.adapters.email.sender import EmailConfig
from fake_winreg.adapters.memory import (
    EmailSpy,
    get_config_in_memory,
    get_default_config_path_in_memory,
    init_logging_in_memory,
    load_email_config_from_dict_in_memory,
)

if TYPE_CHECKING:
    from fake_winreg.application.ports import (
        GetConfig,
        GetDefaultConfigPath,
        InitLogging,
        LoadEmailConfigFromDict,
        SendEmail,
        SendNotification,
    )


# ======================== In-Memory Adapter Contract Tests ========================


@pytest.fixture
def get_config_impl() -> GetConfig:
    """Provide in-memory GetConfig implementation."""
    return get_config_in_memory


@pytest.fixture
def get_default_config_path_impl() -> GetDefaultConfigPath:
    """Provide in-memory GetDefaultConfigPath implementation."""
    return get_default_config_path_in_memory


@pytest.fixture
def send_email_impl() -> SendEmail:
    """Provide in-memory SendEmail implementation."""
    spy = EmailSpy()
    return spy.send_email


@pytest.fixture
def send_notification_impl() -> SendNotification:
    """Provide in-memory SendNotification implementation."""
    spy = EmailSpy()
    return spy.send_notification


@pytest.fixture
def load_email_config_impl() -> LoadEmailConfigFromDict:
    """Provide in-memory LoadEmailConfigFromDict implementation."""
    return load_email_config_from_dict_in_memory


@pytest.fixture
def init_logging_impl() -> InitLogging:
    """Provide in-memory InitLogging implementation."""
    return init_logging_in_memory


@pytest.mark.os_agnostic
def test_get_config_returns_config_with_dict(get_config_impl: GetConfig) -> None:
    """GetConfig must return a Config whose as_dict() yields a dict."""
    config = get_config_impl()
    assert isinstance(config, Config)
    assert isinstance(config.as_dict(), dict)


@pytest.mark.os_agnostic
def test_get_default_config_path_returns_toml_path(get_default_config_path_impl: GetDefaultConfigPath) -> None:
    """GetDefaultConfigPath must return a Path ending in .toml."""
    path = get_default_config_path_impl()
    assert isinstance(path, Path)
    assert path.suffix == ".toml"


@pytest.mark.os_agnostic
def test_send_email_returns_bool_with_valid_config(send_email_impl: SendEmail) -> None:
    """SendEmail must return a bool when called with a valid EmailConfig."""
    config = EmailConfig(smtp_hosts=["smtp.test.com:587"], from_address="a@b.com")
    result = send_email_impl(
        config=config,
        recipients=["test@example.com"],
        subject="Contract test",
        body="Hello",
    )
    assert isinstance(result, bool)


@pytest.mark.os_agnostic
def test_send_notification_returns_bool_with_valid_config(send_notification_impl: SendNotification) -> None:
    """SendNotification must return a bool when called with a valid EmailConfig."""
    config = EmailConfig(smtp_hosts=["smtp.test.com:587"], from_address="a@b.com")
    result = send_notification_impl(
        config=config,
        recipients=["test@example.com"],
        subject="Contract test",
        message="Hello",
    )
    assert isinstance(result, bool)


@pytest.mark.os_agnostic
def test_load_email_config_returns_email_config(load_email_config_impl: LoadEmailConfigFromDict) -> None:
    """LoadEmailConfigFromDict must return an EmailConfig from a valid dict."""
    result = load_email_config_impl(
        {
            "email": {
                "smtp_hosts": ["smtp.test.com:587"],
                "from_address": "test@example.com",
            }
        }
    )
    assert isinstance(result, EmailConfig)


@pytest.mark.os_agnostic
def test_load_email_config_accepts_empty_dict(load_email_config_impl: LoadEmailConfigFromDict) -> None:
    """LoadEmailConfigFromDict must accept an empty dict without raising."""
    result = load_email_config_impl({})
    assert isinstance(result, EmailConfig)


@pytest.mark.os_agnostic
def test_init_logging_does_not_raise(init_logging_impl: InitLogging) -> None:
    """InitLogging must not raise when called with a Config."""
    config = Config({}, {})
    init_logging_impl(config)


# ======================== Composition Wiring Tests ========================


@pytest.mark.os_agnostic
def test_build_production_returns_fully_populated_app_services() -> None:
    """build_production() must return AppServices with all fields populated."""
    from fake_winreg.composition import AppServices, build_production

    services = build_production()
    assert isinstance(services, AppServices)
    for field_obj in services.__dataclass_fields__:
        assert getattr(services, field_obj) is not None


@pytest.mark.os_agnostic
def test_build_testing_returns_fully_populated_app_services() -> None:
    """build_testing() must return AppServices with all in-memory implementations."""
    from fake_winreg.composition import AppServices, build_testing

    services = build_testing()
    assert isinstance(services, AppServices)
    for field_obj in services.__dataclass_fields__:
        assert getattr(services, field_obj) is not None


@pytest.mark.os_agnostic
def test_build_production_services_are_callable() -> None:
    """All services from build_production() must be callable."""
    from fake_winreg.composition import build_production

    services = build_production()
    for field_name in services.__dataclass_fields__:
        assert callable(getattr(services, field_name))


@pytest.mark.os_agnostic
def test_build_testing_services_are_callable() -> None:
    """All services from build_testing() must be callable."""
    from fake_winreg.composition import build_testing

    services = build_testing()
    for field_name in services.__dataclass_fields__:
        assert callable(getattr(services, field_name))
