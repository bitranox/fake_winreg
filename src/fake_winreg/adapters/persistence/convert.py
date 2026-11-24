"""Stream-convert registries between formats without loading into memory.

Supports SQLite (.db/.sqlite/.sqlite3), JSON (.json), and .reg file formats.
Uses the backend interface to stream key-by-key for memory efficiency.
"""

from __future__ import annotations

import errno
import os
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from fake_winreg.domain.api import get_backend, use_backend
from fake_winreg.domain.constants import hive_name_hashed_by_int
from fake_winreg.domain.enums import RegistryFormat
from fake_winreg.domain.memory_backend import InMemoryBackend

from .json_backend import JsonBackend
from .json_io import export_json, import_json
from .reg_io import export_reg, import_reg
from .sqlite_backend import SqliteBackend

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from fake_winreg.application.ports import RegistryBackend
    from fake_winreg.domain.registry import FakeRegistryKey


# The file formats, each with the function that writes the active backend to
# such a file and the one that reads such a file into it. SQLite has neither:
# it is a backend itself and is converted by streaming key by key.
_EXPORTERS: Final[Mapping[RegistryFormat, Callable[[Path], None]]] = MappingProxyType(
    {RegistryFormat.JSON: export_json, RegistryFormat.REG: export_reg}
)
_IMPORTERS: Final[Mapping[RegistryFormat, Callable[[Path], None]]] = MappingProxyType(
    {RegistryFormat.JSON: import_json, RegistryFormat.REG: import_reg}
)

_FORMAT_BY_SUFFIX: Final[Mapping[str, RegistryFormat]] = MappingProxyType(
    {
        ".db": RegistryFormat.SQLITE,
        ".sqlite": RegistryFormat.SQLITE,
        ".sqlite3": RegistryFormat.SQLITE,
        ".json": RegistryFormat.JSON,
        ".reg": RegistryFormat.REG,
    }
)


def convert_registry(source: str | Path, target: str | Path) -> int:
    """Stream-convert a registry between formats.

    Auto-detects format by file extension:
      .db, .sqlite, .sqlite3 -> SQLite
      .json                  -> JSON
      .reg                   -> Windows Registry Editor format

    Returns the number of keys converted.

    Raises:
        ValueError: If the file extension is not recognized.
        FileNotFoundError: If *source* does not exist.
        IsADirectoryError: If *source* is a directory.
    """
    source = Path(source)
    target = Path(target)
    source_fmt = _detect_format(source)
    target_fmt = _detect_format(target)
    _require_existing_source(source)

    # Save and restore the active backend after conversion
    previous_backend = get_backend()
    try:
        return _do_convert(source, source_fmt, target, target_fmt)
    finally:
        use_backend(previous_backend)


def _require_existing_source(source: Path) -> None:
    """Refuse a missing source, or a directory, before any backend is opened.

    Opening one would not fail: SqliteBackend creates an empty database and
    JsonBackend starts empty for a missing file, so the conversion "succeeded"
    with only the empty hives, and a SQLite source or target file was left
    behind. A directory reached SQLite as "unable to open database file" but
    open() as IsADirectoryError. The errors have the shape open() raises, so
    every format exits the same way.

    Raises:
        IsADirectoryError: If *source* is a directory.
        FileNotFoundError: If *source* does not exist.
    """
    if source.is_dir():
        raise IsADirectoryError(errno.EISDIR, os.strerror(errno.EISDIR), str(source))
    if not source.exists():
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), str(source))


def _do_convert(source: Path, source_fmt: RegistryFormat, target: Path, target_fmt: RegistryFormat) -> int:
    """Perform the actual conversion, choosing the most memory-efficient path."""
    if source_fmt is RegistryFormat.SQLITE and target_fmt is RegistryFormat.SQLITE:
        return _convert_sqlite_to_sqlite(source, target)
    if target_fmt is RegistryFormat.SQLITE:
        return _import_into_sqlite(source, source_fmt, target)
    if source_fmt is RegistryFormat.SQLITE:
        return _export_from_sqlite(source, target, target_fmt)
    return _convert_via_loaded_backend(source, source_fmt, target, target_fmt)


def _convert_sqlite_to_sqlite(source: Path, target: Path) -> int:
    """Stream a SQLite registry into another SQLite registry key by key."""
    with SqliteBackend(source) as source_backend, SqliteBackend(target) as target_backend, target_backend.bulk():
        return copy_backend(source_backend, target_backend)


def _import_into_sqlite(source: Path, source_fmt: RegistryFormat, target: Path) -> int:
    """Import a .reg (streaming) or JSON (in-memory) file directly into a SqliteBackend.

    The whole import is one transaction: one commit instead of one per key and
    value. A failed import leaves an existing target as it was; a target that
    did not exist is left created, holding only the empty hives, because
    SqliteBackend creates the file and its schema before the import starts.
    """
    importer = _IMPORTERS[source_fmt]
    with SqliteBackend(target) as target_backend:
        use_backend(target_backend)
        with target_backend.bulk():
            importer(source)
        return _count_keys(target_backend)


def _export_from_sqlite(source: Path, target: Path, target_fmt: RegistryFormat) -> int:
    """Export a SqliteBackend (streaming) to a JSON or .reg file."""
    exporter = _EXPORTERS[target_fmt]
    with SqliteBackend(source) as source_backend:
        use_backend(source_backend)
        exporter(target)
        return _count_keys(source_backend)


def _convert_via_loaded_backend(
    source: Path, source_fmt: RegistryFormat, target: Path, target_fmt: RegistryFormat
) -> int:
    """Convert between .reg and JSON by loading the source fully, then exporting it.

    A .reg source is imported into an InMemoryBackend; a JSON source is loaded
    by a JsonBackend (it must fit in memory). Re-exporting to the same format
    normalizes the file.

    Raises:
        ValueError: If the format pair is not a .reg/JSON combination.
    """
    exporter = _EXPORTERS.get(target_fmt)
    if source_fmt not in _IMPORTERS or exporter is None:
        raise ValueError(f"Unsupported conversion: {source_fmt.value} \u2192 {target_fmt.value}")
    backend = _load_source_backend(source, source_fmt)
    exporter(target)
    return _count_keys(backend)


def _load_source_backend(source: Path, source_fmt: RegistryFormat) -> RegistryBackend:
    """Activate a backend holding *source*: JsonBackend for JSON, InMemoryBackend for .reg."""
    if source_fmt is RegistryFormat.JSON:
        json_backend = JsonBackend(source)
        use_backend(json_backend)
        return json_backend
    mem_backend = InMemoryBackend()
    use_backend(mem_backend)
    _IMPORTERS[source_fmt](source)
    return mem_backend


def copy_backend(source: RegistryBackend, target: RegistryBackend) -> int:
    """Copy every key and value of *source* into *target*, key by key, and return the key count.

    Keys and values are written in the order *source* enumerates them, one key's
    values at a time, so memory holds one key's listing rather than the tree.
    Run it inside ``target.bulk()`` when the target is a SqliteBackend, or each
    write commits on its own.
    """
    count = 0
    for hive_int in sorted(hive_name_hashed_by_int):
        source_hive = source.get_hive(hive_int)
        target_hive = target.get_hive(hive_int)
        count += _stream_key_recursive(source, target, source_hive, target_hive)
    return count


def _stream_key_recursive(
    source: RegistryBackend,
    target: RegistryBackend,
    source_key: FakeRegistryKey,
    target_key: FakeRegistryKey,
) -> int:
    """Recursively stream keys and values from source to target."""
    count = 1
    for entry in source.enum_values(source_key):
        target.set_value(target_key, entry.name, entry.data, entry.value_type)

    for subkey_name in source.enum_keys(source_key):
        child_src = source.get_key(source_key, subkey_name)
        child_tgt = target.create_key(target_key, subkey_name)
        count += _stream_key_recursive(source, target, child_src, child_tgt)

    return count


def _count_keys(backend: RegistryBackend) -> int:
    """Count total keys in a backend by walking all hives."""
    count = 0
    for hive_int in sorted(hive_name_hashed_by_int):
        hive = backend.get_hive(hive_int)
        count += _count_keys_recursive(backend, hive)
    return count


def _count_keys_recursive(backend: RegistryBackend, key: FakeRegistryKey) -> int:
    """Recursively count keys."""
    count = 1
    for subkey_name in backend.enum_keys(key):
        child = backend.get_key(key, subkey_name)
        count += _count_keys_recursive(backend, child)
    return count


def _detect_format(path: Path) -> RegistryFormat:
    """Detect registry format from file extension.

    >>> _detect_format(Path("hive.SQLITE3"))
    <RegistryFormat.SQLITE: 'sqlite'>
    """
    registry_format = _FORMAT_BY_SUFFIX.get(path.suffix.lower())
    if registry_format is None:
        # Built from the table, so the message cannot omit an accepted extension.
        supported = ", ".join(_FORMAT_BY_SUFFIX)
        raise ValueError(f"Unknown registry format for '{path.name}'. Supported extensions: {supported}")
    return registry_format


__all__ = ["convert_registry", "copy_backend"]
