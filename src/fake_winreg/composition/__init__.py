"""Composition root wiring adapters to application ports."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..adapters.config.deploy import deploy_configuration
from ..adapters.config.display import display_config

# Configuration services
from ..adapters.config.loader import get_config, get_default_config_path

# Email services
from ..adapters.email.sender import (
    load_email_config_from_dict,
    send_email,
    send_notification,
)

# Logging services
from ..adapters.logging.setup import init_logging

# Network adapter — wired into domain API
from ..adapters.network import is_computer_reachable
from ..domain.api import configure_network_resolver

configure_network_resolver(is_computer_reachable)

# Static conformance assertions — pyright verifies that each adapter function
# structurally satisfies its corresponding Protocol at type-check time.
if TYPE_CHECKING:
    from ..adapters.memory.email import EmailSpy
    from ..application.ports import (
        DeployConfiguration,
        DisplayConfig,
        GetConfig,
        GetDefaultConfigPath,
        InitLogging,
        LoadEmailConfigFromDict,
        SendEmail,
        SendNotification,
    )

    _assert_get_config: GetConfig = get_config
    _assert_get_default_config_path: GetDefaultConfigPath = get_default_config_path
    _assert_deploy_configuration: DeployConfiguration = deploy_configuration
    _assert_display_config: DisplayConfig = display_config
    _assert_send_email: SendEmail = send_email
    _assert_send_notification: SendNotification = send_notification
    _assert_load_email_config_from_dict: LoadEmailConfigFromDict = load_email_config_from_dict
    _assert_init_logging: InitLogging = init_logging


@dataclass(frozen=True, slots=True)
class AppServices:
    """Frozen container holding all application port implementations."""

    get_config: GetConfig
    get_default_config_path: GetDefaultConfigPath
    deploy_configuration: DeployConfiguration
    display_config: DisplayConfig
    send_email: SendEmail
    send_notification: SendNotification
    load_email_config_from_dict: LoadEmailConfigFromDict
    init_logging: InitLogging


def build_production() -> AppServices:
    """Wire production adapters into an AppServices container."""
    return AppServices(
        get_config=get_config,
        get_default_config_path=get_default_config_path,
        deploy_configuration=deploy_configuration,
        display_config=display_config,
        send_email=send_email,
        send_notification=send_notification,
        load_email_config_from_dict=load_email_config_from_dict,
        init_logging=init_logging,
    )


def build_testing(*, spy: EmailSpy | None = None) -> AppServices:
    """Wire in-memory adapters into an AppServices container.

    Args:
        spy: Optional EmailSpy instance for capturing email operations.
            When None, a fresh EmailSpy is created. Pass your own spy
            to assert on captured emails in tests.

    Returns:
        AppServices container with in-memory adapters.
    """
    from ..adapters.memory import (
        EmailSpy,
        deploy_configuration_in_memory,
        display_config_in_memory,
        get_config_in_memory,
        get_default_config_path_in_memory,
        init_logging_in_memory,
        load_email_config_from_dict_in_memory,
    )

    email_spy = spy if spy is not None else EmailSpy()

    return AppServices(
        get_config=get_config_in_memory,
        get_default_config_path=get_default_config_path_in_memory,
        deploy_configuration=deploy_configuration_in_memory,
        display_config=display_config_in_memory,
        send_email=email_spy.send_email,
        send_notification=email_spy.send_notification,
        load_email_config_from_dict=load_email_config_from_dict_in_memory,
        init_logging=init_logging_in_memory,
    )


__all__ = [
    # Configuration
    "get_config",
    "get_default_config_path",
    "deploy_configuration",
    "display_config",
    # Email
    "send_email",
    "send_notification",
    "load_email_config_from_dict",
    # Logging
    "init_logging",
    # Composition
    "AppServices",
    "build_production",
    "build_testing",
]
