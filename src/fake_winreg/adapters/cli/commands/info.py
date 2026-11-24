"""CLI info command for displaying package metadata.

Contents:
    * :func:`cli_info` - Display package metadata.
"""

from __future__ import annotations

import logging

import lib_log_rich.runtime
import rich_click as click

from fake_winreg import __init__conf__

from ..constants import click_context_settings

logger = logging.getLogger(__name__)


@click.command("info", context_settings=click_context_settings())
def cli_info() -> None:
    """Print resolved metadata so users can inspect installation details."""
    with lib_log_rich.runtime.bind(job_id="cli-info", extra={"command": "info"}):
        logger.info("Displaying package information")
        __init__conf__.print_info()


__all__ = ["cli_info"]
