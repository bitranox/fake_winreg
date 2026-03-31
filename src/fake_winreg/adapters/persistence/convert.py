"""Stream-convert registries between formats without loading into memory.

Supports SQLite (.db/.sqlite), JSON (.json), and .reg file formats.
Uses the backend interface to stream key-by-key for memory efficiency.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from fake_winreg.application.ports import RegistryBackend
from fake_winreg.domain.api import _get_backend, use_backend  # pyright: ignore[reportPrivateUsage]
from fake_winreg.domain.constants import hive_name_hashed_by_int
from fake_winreg.domain.registry import FakeRegistryKey

from .json_io import export_json, import_json
from .reg_io import export_reg, import_reg
from .sqlite_backend import SqliteBackend


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
        # SQLite → SQLite: stream key by key
        source_backend = SqliteBackend(source)
        target_backend = SqliteBackend(target)
        try:
            return _stream_backend_to_backend(source_backend, target_backend)
        finally:
            source_backend.close()
            target_backend.close()

    if target_fmt == "sqlite":
        # Import directly into SqliteBackend (streaming for .reg, in-memory for .json)
        target_backend = SqliteBackend(target)
        use_backend(target_backend)  # type: ignore[arg-type]
        if source_fmt == "reg":
            import_reg(source)
        elif source_fmt == "json":
            import_json(source)
        count = _count_keys(target_backend)
        target_backend.close()
        return count

    if source_fmt == "sqlite":
        # Export from SqliteBackend (streaming)
        source_backend = SqliteBackend(source)
        use_backend(source_backend)  # type: ignore[arg-type]
        if target_fmt == "json":
            export_json(target)
        elif target_fmt == "reg":
            export_reg(target)
        count = _count_keys(source_backend)
        source_backend.close()
        return count

    if source_fmt == "reg" and target_fmt == "json":
        # .reg → JSON: import .reg into temp SQLite, then export JSON
        with tempfile.TemporaryDirectory() as td:
            tmp_db = Path(td) / "temp.db"
            tmp_backend = SqliteBackend(tmp_db)
            use_backend(tmp_backend)  # type: ignore[arg-type]
            import_reg(source)
            export_json(target)
            count = _count_keys(tmp_backend)
            tmp_backend.close()
            return count

    if source_fmt == "reg" and target_fmt == "reg":
        # .reg → .reg: import into temp SQLite, then export
        with tempfile.TemporaryDirectory() as td:
            tmp_db = Path(td) / "temp.db"
            tmp_backend = SqliteBackend(tmp_db)
            use_backend(tmp_backend)  # type: ignore[arg-type]
            import_reg(source)
            export_reg(target)
            count = _count_keys(tmp_backend)
            tmp_backend.close()
            return count

    if source_fmt == "json" and target_fmt == "reg":
        # JSON → .reg: load JSON (must fit in memory), export as .reg
        from .json_backend import JsonBackend

        json_backend = JsonBackend(source)
        use_backend(json_backend)  # type: ignore[arg-type]
        export_reg(target)
        return _count_keys(json_backend)

    if source_fmt == "json" and target_fmt == "json":
        # JSON → JSON: load and re-export (normalize format)
        from .json_backend import JsonBackend

        json_backend = JsonBackend(source)
        use_backend(json_backend)  # type: ignore[arg-type]
        export_json(target)
        return _count_keys(json_backend)

    raise ValueError(f"Unsupported conversion: {source_fmt} → {target_fmt}")


def _stream_backend_to_backend(source: RegistryBackend, target: RegistryBackend) -> int:
    """Stream all keys and values from source to target backend, key by key."""
    count = 0
    for hive_int in hive_name_hashed_by_int:
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
    for hive_int in hive_name_hashed_by_int:
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
