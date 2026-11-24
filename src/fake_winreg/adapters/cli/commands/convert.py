"""CLI command for converting registries between formats.

Supports dd-style syntax: ``fake-winreg convert if=source.db of=target.reg``
"""

from __future__ import annotations

import logging
from pathlib import Path

import lib_log_rich.runtime
import rich_click as click

from .. import safe_console
from ..constants import click_context_settings
from ..typed_click import argument

logger = logging.getLogger(__name__)


@click.command("convert", context_settings=click_context_settings())
@argument("args", nargs=-1, required=True)
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
    source: str | None = None
    target: str | None = None

    for arg in args:
        if arg.startswith("if="):
            source = arg[3:]
        elif arg.startswith("of="):
            target = arg[3:]
        else:
            raise click.UsageError(f"Unknown argument: {arg!r}. Use if=SOURCE and of=TARGET.")

    # Checked as text before becoming a Path: Path("") is ".", so an empty if= or of= would
    # otherwise pass as the current directory instead of being refused as missing.
    if not source:
        raise click.UsageError("Missing source file. Use if=SOURCE.")
    if not target:
        raise click.UsageError("Missing target file. Use of=TARGET.")
    source_path = Path(source)
    target_path = Path(target)

    # Deferred: persistence.convert pulls in sqlite_backend/json_io/reg_io (and their
    # orjson/sqlite3 deps) - keep them out of `--help` and every other subcommand's path.
    from fake_winreg.adapters.persistence.convert import convert_registry  # noqa: PLC0415

    with lib_log_rich.runtime.bind(job_id="cli-convert", extra={"command": "convert"}):
        logger.info("Converting %s \u2192 %s", source, target)
        try:
            count = convert_registry(source_path, target_path)
        except ValueError as exc:
            raise click.UsageError(str(exc)) from exc
        # The paths as typed, not str(Path), which would drop a leading "./" or a trailing "/".
        safe_console.echo(f"Converted {count} keys: {source} \u2192 {target}")


__all__ = ["cli_convert"]
