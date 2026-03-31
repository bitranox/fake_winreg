"""CLI command implementations.

Collects all subcommand functions and re-exports them for registration
with the root CLI group.

Contents:
    * Info commands from :mod:`.info`
    * Config commands from :mod:`.config`
    * Email commands from :mod:`.email` (subpackage)
    * Logging commands from :mod:`.logging`
"""

from __future__ import annotations

from .config import cli_config, cli_config_deploy, cli_config_generate_examples
from .convert import cli_convert
from .email import cli_send_email, cli_send_notification
from .info import cli_info
from .logging import cli_logdemo

__all__ = [
    "cli_config",
    "cli_config_deploy",
    "cli_config_generate_examples",
    "cli_convert",
    "cli_info",
    "cli_logdemo",
    "cli_send_email",
    "cli_send_notification",
]
