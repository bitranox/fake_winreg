"""CLI package providing the command-line interface.

Re-exports all public symbols from submodules for convenient access.

Contents:
    * Click context helpers and traceback state management from :mod:`.context`
    * Root command group from :mod:`.root`
    * Entry point from :mod:`.main`
    * All command functions from :mod:`.commands`

System Role:
    Acts as the public facade for the CLI subsystem. Consumers import from here
    and remain insulated from internal module boundaries.
"""

from __future__ import annotations

from .commands import (
    cli_config,
    cli_config_deploy,
    cli_config_generate_examples,
    cli_convert,
    cli_export_demo_registries,
    cli_info,
    cli_logdemo,
)
from .constants import CLICK_CONTEXT_SETTINGS, TRACEBACK_SUMMARY_LIMIT, TRACEBACK_VERBOSE_LIMIT
from .context import (
    TracebackState,
    apply_traceback_preferences,
    restore_traceback_state,
    snapshot_traceback_state,
    store_cli_context,
)
from .main import main
from .root import cli

__all__ = [
    # Constants
    "CLICK_CONTEXT_SETTINGS",
    "TRACEBACK_SUMMARY_LIMIT",
    "TRACEBACK_VERBOSE_LIMIT",
    # Traceback management
    "TracebackState",
    "apply_traceback_preferences",
    "restore_traceback_state",
    "snapshot_traceback_state",
    # Context helpers
    "store_cli_context",
    # Root command
    "cli",
    # Entry point
    "main",
    # Commands
    "cli_config",
    "cli_config_deploy",
    "cli_config_generate_examples",
    "cli_convert",
    "cli_export_demo_registries",
    "cli_info",
    "cli_logdemo",
]
