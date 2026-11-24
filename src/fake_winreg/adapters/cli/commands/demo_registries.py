"""CLI command to export demo registry files to the current directory."""

from __future__ import annotations

import logging
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

import lib_log_rich.runtime
import rich_click as click

from fake_winreg.adapters.persistence.reg_io import export_reg
from fake_winreg.domain.api import use_backend
from fake_winreg.domain.enums import RegistryFormat
from fake_winreg.domain.memory_backend import InMemoryBackend
from fake_winreg.domain.test_registries import (
    get_minimal_windows11_testregistry,
    get_minimal_windows_testregistry,
    get_minimal_wine_testregistry,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

from .. import safe_console
from ..constants import click_context_settings

logger = logging.getLogger(__name__)

#: The file extension each demo file gets, in the order the files are written. SQLite files
#: are named ``.db``, the extension the converter also reads as SQLite.
_EXTENSION_BY_FORMAT: Final[Mapping[RegistryFormat, str]] = MappingProxyType(
    {RegistryFormat.JSON: ".json", RegistryFormat.REG: ".reg", RegistryFormat.SQLITE: ".db"}
)


@click.command("export-demo-registries", context_settings=click_context_settings())
def cli_export_demo_registries() -> None:
    """Export demo registry files (Windows 10, Windows 11, Wine) to the current directory.

    \b
    Creates 9 files:
      windows10.json, windows10.reg, windows10.db
      windows11.json, windows11.reg, windows11.db
      wine.json, wine.reg, wine.db
    """
    with lib_log_rich.runtime.bind(job_id="cli-export-demo", extra={"command": "export-demo-registries"}):
        # Deferred: convert, json_io and sqlite_backend pull in orjson/sqlite3 - keep those out
        # of `--help` and every other subcommand's path; only this command's db-export needs them.
        from fake_winreg.adapters.persistence.convert import copy_backend  # noqa: PLC0415
        from fake_winreg.adapters.persistence.json_io import export_json  # noqa: PLC0415
        from fake_winreg.adapters.persistence.sqlite_backend import SqliteBackend  # noqa: PLC0415

        builders = {
            "windows10": get_minimal_windows_testregistry,
            "windows11": get_minimal_windows11_testregistry,
            "wine": get_minimal_wine_testregistry,
        }

        for name, builder in builders.items():
            registry = builder()
            backend = InMemoryBackend(registry)
            use_backend(backend)

            for fmt, extension in _EXTENSION_BY_FORMAT.items():
                filename = f"{name}{extension}"
                path = Path(filename)

                if fmt is RegistryFormat.JSON:
                    export_json(path)
                elif fmt is RegistryFormat.REG:
                    export_reg(path)
                else:  # RegistryFormat.SQLITE, the one member left
                    # One transaction for the whole copy: committing every write costs a disk sync each.
                    with SqliteBackend(path) as db_backend, db_backend.bulk():
                        copy_backend(backend, db_backend)

                safe_console.echo(f"Created {filename}")

        # Restore default backend
        use_backend(InMemoryBackend())


__all__ = ["cli_export_demo_registries"]
