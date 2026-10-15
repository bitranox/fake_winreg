"""Stream-convert registries between formats without loading into memory.

Supports SQLite (.db/.sqlite), JSON (.json), and .reg file formats.
Uses the backend interface to stream key-by-key for memory efficiency.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from fake_winreg.domain.api import _get_backend, use_backend  # pyright: ignore[reportPrivateUsage]
from fake_winreg.domain.constants import hive_name_hashed_by_int
from fake_winreg.domain.memory_backend import InMemoryBackend

from .json_backend import JsonBackend
from .json_io import export_json, import_json
from .reg_io import export_reg, import_reg
from .sqlite_backend import SqliteBackend

if TYPE_CHECKING:
    from collections.abc import Callable

    from fake_winreg.application.ports import RegistryBackend
    from fake_winreg.domain.registry import FakeRegistryKey


_EXPORTERS: dict[str, Callable[[Path], None]] = {"json": export_json, "reg": export_reg}


def convert_registry(source: str | Path, target: str | Path) -> int:
    """Stream-convert a registry between formats.

    Auto-detects format by file extension:
      .db, .sqlite → SQLite
      .json        → JSON
      .reg         → Windows Registry Editor format

    Returns the number of keys converted.

    Raises:
        ValueError: If the file extension is not recognized.
    """
    source = Path(source)
    target = Path(target)
    source_fmt = _detect_format(source)
    target_fmt = _detect_format(target)

    # Save and restore the active backend after conversion
    previous_backend = _get_backend()
    try:
        return _do_convert(source, source_fmt, target, target_fmt)
    finally:
        use_backend(previous_backend)  # type: ignore[arg-type]


def _do_convert(source: Path, source_fmt: str, target: Path, target_fmt: str) -> int:
    """Perform the actual conversion, choosing the most memory-efficient path."""
    if source_fmt == target_fmt and source_fmt == "sqlite":
        return _convert_sqlite_to_sqlite(source, target)
    if target_fmt == "sqlite":
        return _import_into_sqlite(source, source_fmt, target)
    if source_fmt == "sqlite":
        return _export_from_sqlite(source, target, target_fmt)
    return _convert_via_loaded_backend(source, source_fmt, target, target_fmt)


def _convert_sqlite_to_sqlite(source: Path, target: Path) -> int:
    """Stream a SQLite registry into another SQLite registry key by key."""
    source_backend = SqliteBackend(source)
    target_backend = SqliteBackend(target)
    try:
        return _stream_backend_to_backend(source_backend, target_backend)
    finally:
        source_backend.close()
        target_backend.close()


def _import_into_sqlite(source: Path, source_fmt: str, target: Path) -> int:
    """Import a .reg (streaming) or JSON (in-memory) file directly into a SqliteBackend."""
    target_backend = SqliteBackend(target)
    use_backend(target_backend)
    if source_fmt == "reg":
        import_reg(source)
    elif source_fmt == "json":
        import_json(source)
    count = _count_keys(target_backend)
    target_backend.close()
    return count


def _export_from_sqlite(source: Path, target: Path, target_fmt: str) -> int:
    """Export a SqliteBackend (streaming) to a JSON or .reg file."""
    source_backend = SqliteBackend(source)
    use_backend(source_backend)
    if target_fmt == "json":
        export_json(target)
    elif target_fmt == "reg":
        export_reg(target)
    count = _count_keys(source_backend)
    source_backend.close()
    return count


def _convert_via_loaded_backend(source: Path, source_fmt: str, target: Path, target_fmt: str) -> int:
    """Convert between .reg and JSON by loading the source fully, then exporting it.

    A .reg source is imported into an InMemoryBackend; a JSON source is loaded
    by a JsonBackend (it must fit in memory). Re-exporting to the same format
    normalizes the file.

    Raises:
        ValueError: If the format pair is not a .reg/JSON combination.
    """
    exporter = _EXPORTERS.get(target_fmt)
    if source_fmt not in ("reg", "json") or exporter is None:
        raise ValueError(f"Unsupported conversion: {source_fmt} → {target_fmt}")
    backend = _load_source_backend(source, source_fmt)
    exporter(target)
    return _count_keys(backend)


def _load_source_backend(source: Path, source_fmt: str) -> RegistryBackend:
    """Activate a backend holding *source*: JsonBackend for JSON, InMemoryBackend for .reg."""
    if source_fmt == "json":
        json_backend = JsonBackend(source)
        use_backend(json_backend)
        return json_backend
    mem_backend = InMemoryBackend()
    use_backend(mem_backend)
    import_reg(source)
    return mem_backend


def _stream_backend_to_backend(source: RegistryBackend, target: RegistryBackend) -> int:
    """Stream all keys and values from source to target backend, key by key."""
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
    # Copy values
    for vname, vdata, vtype in source.enum_values(source_key):
        target.set_value(target_key, vname, vdata, vtype)

    # Recurse into subkeys
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


def _detect_format(path: Path) -> str:
    """Detect registry format from file extension."""
    suffix = path.suffix.lower()
    if suffix in (".db", ".sqlite", ".sqlite3"):
        return "sqlite"
    if suffix == ".json":
        return "json"
    if suffix == ".reg":
        return "reg"
    raise ValueError(f"Unknown registry format for '{path.name}'. Supported extensions: .db, .sqlite, .json, .reg")


__all__ = ["convert_registry"]
