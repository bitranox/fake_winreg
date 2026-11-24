"""CLI command to export demo registry files to the current directory."""

from __future__ import annotations

import logging
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

import lib_log_rich.runtime
import rich_click as click

from fake_winreg.adapters.persistence.convert import copy_backend
from fake_winreg.adapters.persistence.json_io import export_json
from fake_winreg.adapters.persistence.reg_io import export_reg
from fake_winreg.adapters.persistence.sqlite_backend import SqliteBackend
from fake_winreg.domain.api import use_backend
from fake_winreg.domain.enums import RegistryFormat
from fake_winreg.domain.memory_backend import InMemoryBackend
from fake_winreg.domain.test_registries import (
    get_minimal_windows11_testregistry,
    get_minimal_windows_testregistry,
    get_minimal_wine_testregistry,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

from .. import safe_console
from ..constants import click_context_settings

logger = logging.getLogger(__name__)

#: The file extension each demo file gets, in the order the files are written. SQLite files
#: are named ``.db``, the extension the converter also reads as SQLite.
_EXTENSION_BY_FORMAT: Final[Mapping[RegistryFormat, str]] = MappingProxyType(
    {RegistryFormat.JSON: ".json", RegistryFormat.REG: ".reg", RegistryFormat.SQLITE: ".db"}
)


def _write_json(path: Path, _source: InMemoryBackend) -> None:
    export_json(path)


def _write_reg(path: Path, _source: InMemoryBackend) -> None:
    export_reg(path)


def _write_sqlite(path: Path, source: InMemoryBackend) -> None:
    # One transaction for the whole copy: committing every write costs a disk sync each.
    with SqliteBackend(path) as db_backend, db_backend.bulk():
        copy_backend(source, db_backend)


#: The writer for each format. Both tables must cover every RegistryFormat member (checked
#: below at import), so a new format fails loudly instead of being written by the wrong code.
_WRITER_BY_FORMAT: Final[Mapping[RegistryFormat, Callable[[Path, InMemoryBackend], None]]] = MappingProxyType(
    {RegistryFormat.JSON: _write_json, RegistryFormat.REG: _write_reg, RegistryFormat.SQLITE: _write_sqlite}
)

if set(_WRITER_BY_FORMAT) != set(RegistryFormat) or set(_EXTENSION_BY_FORMAT) != set(RegistryFormat):
    raise RuntimeError("demo_registries: every RegistryFormat needs a writer and an extension")


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
        builders = {
            "windows10": get_minimal_windows_testregistry,
            "windows11": get_minimal_windows11_testregistry,
            "wine": get_minimal_wine_testregistry,
        }

        for name, builder in builders.items():
            backend = InMemoryBackend(builder())
            use_backend(backend)
            for fmt, extension in _EXTENSION_BY_FORMAT.items():
                filename = f"{name}{extension}"
                _WRITER_BY_FORMAT[fmt](Path(filename), backend)
                safe_console.echo(f"Created {filename}")

        # Restore default backend
        use_backend(InMemoryBackend())


__all__ = ["cli_export_demo_registries"]
