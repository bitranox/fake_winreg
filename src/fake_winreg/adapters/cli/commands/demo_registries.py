"""CLI command to export demo registry files to the current directory."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import lib_log_rich.runtime
import rich_click as click

if TYPE_CHECKING:
    from fake_winreg.adapters.persistence.sqlite_backend import SqliteBackend
    from fake_winreg.domain.memory_backend import InMemoryBackend

from ..constants import CLICK_CONTEXT_SETTINGS

logger = logging.getLogger(__name__)

_REGISTRIES = [
    ("windows10", "get_minimal_windows_testregistry"),
    ("wine", "get_minimal_wine_testregistry"),
]

_FORMATS = ["json", "reg", "db"]


@click.command("export-demo-registries", context_settings=CLICK_CONTEXT_SETTINGS)
def cli_export_demo_registries() -> None:
    """Export demo registry files (Windows 10, Wine) to the current directory.

    \b
    Creates 6 files:
      windows10.json, windows10.reg, windows10.db
      wine.json, wine.reg, wine.db

    Example:
        >>> from click.testing import CliRunner
        >>> import tempfile, os
        >>> runner = CliRunner()
        >>> with runner.isolated_filesystem():
        ...     result = runner.invoke(cli_export_demo_registries)
        ...     assert result.exit_code == 0
        ...     assert os.path.exists("windows10.json")
    """
    with lib_log_rich.runtime.bind(job_id="cli-export-demo", extra={"command": "export-demo-registries"}):
        from fake_winreg.adapters.persistence.json_io import export_json
        from fake_winreg.adapters.persistence.reg_io import export_reg
        from fake_winreg.adapters.persistence.sqlite_backend import SqliteBackend
        from fake_winreg.domain.api import use_backend
        from fake_winreg.domain.memory_backend import InMemoryBackend
        from fake_winreg.domain.test_registries import (
            get_minimal_windows_testregistry,
            get_minimal_wine_testregistry,
        )

        builders = {
            "windows10": get_minimal_windows_testregistry,
            "wine": get_minimal_wine_testregistry,
        }

        for name, builder in builders.items():
            registry = builder()
            backend = InMemoryBackend(registry)
            use_backend(backend)  # type: ignore[arg-type]

            for fmt in _FORMATS:
                filename = f"{name}.{fmt}"
                path = Path(filename)

                if fmt == "json":
                    export_json(path)
                elif fmt == "reg":
                    export_reg(path)
                elif fmt == "db":
                    db_backend = SqliteBackend(path)
                    _copy_registry_to_sqlite(backend, db_backend)
                    db_backend.close()

                click.echo(f"Created {filename}")

        # Restore default backend
        use_backend(InMemoryBackend())  # type: ignore[arg-type]


def _copy_registry_to_sqlite(source: InMemoryBackend, target: SqliteBackend) -> None:
    """Copy all keys and values from in-memory backend to SQLite."""
    from fake_winreg.domain.constants import hive_name_hashed_by_int

    for hive_int in sorted(hive_name_hashed_by_int):
        src_hive = source.get_hive(hive_int)
        tgt_hive = target.get_hive(hive_int)
        _copy_key_recursive(source, target, src_hive, tgt_hive)


def _copy_key_recursive(
    source: InMemoryBackend,
    target: SqliteBackend,
    src_key: object,
    tgt_key: object,
) -> None:
    """Recursively copy keys and values."""
    from fake_winreg.domain.registry import FakeRegistryKey

    if not isinstance(src_key, FakeRegistryKey) or not isinstance(tgt_key, FakeRegistryKey):
        return

    for vname, vdata, vtype in source.enum_values(src_key):
        target.set_value(tgt_key, vname, vdata, vtype)

    for subkey_name in source.enum_keys(src_key):
        child_src = source.get_key(src_key, subkey_name)
        child_tgt = target.create_key(tgt_key, subkey_name)
        _copy_key_recursive(source, target, child_src, child_tgt)


__all__ = ["cli_export_demo_registries"]
