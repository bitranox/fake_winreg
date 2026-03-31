"""CLI command for converting registries between formats.

Supports dd-style syntax: ``fake-winreg convert if=source.db of=target.reg``
"""

from __future__ import annotations

import logging

import lib_log_rich.runtime
import rich_click as click

from ..constants import CLICK_CONTEXT_SETTINGS

logger = logging.getLogger(__name__)


@click.command("convert", context_settings=CLICK_CONTEXT_SETTINGS)
@click.argument("args", nargs=-1, required=True)
def cli_convert(args: tuple[str, ...]) -> None:
    """Convert registry between formats (dd-style syntax).

    \b
    Usage:
      fake-winreg convert if=source.db of=target.reg
      fake-winreg convert if=export.reg of=registry.db
      fake-winreg convert if=registry.db of=snapshot.json

    \b
    Supported formats (detected by extension):
      .db, .sqlite  SQLite database
      .json         JSON file
      .reg          Windows Registry Editor format
    """
    source = None
    target = None

    for arg in args:
        if arg.startswith("if="):
            source = arg[3:]
        elif arg.startswith("of="):
            target = arg[3:]
        else:
            raise click.UsageError(f"Unknown argument: {arg!r}. Use if=SOURCE and of=TARGET.")

    if not source:
        raise click.UsageError("Missing source file. Use if=SOURCE.")
    if not target:
        raise click.UsageError("Missing target file. Use of=TARGET.")

    from fake_winreg.adapters.persistence.convert import convert_registry

    with lib_log_rich.runtime.bind(job_id="cli-convert", extra={"command": "convert"}):
        logger.info("Converting %s → %s", source, target)
        try:
            count = convert_registry(source, target)
        except ValueError as exc:
            raise click.UsageError(str(exc)) from exc
        click.echo(f"Converted {count} keys: {source} → {target}")


__all__ = ["cli_convert"]
