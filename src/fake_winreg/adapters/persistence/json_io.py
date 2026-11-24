"""Import/export functions for JSON registry snapshots.

These functions work with the currently active backend, allowing data
to be loaded from or saved to JSON files regardless of which backend
implementation is in use.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import orjson

from fake_winreg.domain.api import get_backend
from fake_winreg.domain.constants import hive_name_hashed_by_int
from fake_winreg.domain.serialization import (
    SnapshotDict,
    SnapshotKeyDict,
    SnapshotValueDict,
    encode_value,
    parse_registry_document,
)

if TYPE_CHECKING:
    from fake_winreg.application.ports import RegistryBackend
    from fake_winreg.domain.registry import FakeRegistryKey
    from fake_winreg.domain.serialization import KeyRecord


def import_json(path: str | Path) -> None:
    """Load JSON file data into the currently active backend.

    Parses the document once (see
    :func:`fake_winreg.domain.serialization.parse_registry_document`), then
    calls ``create_key`` and ``set_value`` on the active backend for every key
    and value found.  This works with any backend implementation (memory,
    SQLite, etc.).  Document timestamps are not imported: the backend stamps
    what it writes.

    >>> import tempfile, os, orjson as _oj
    >>> p = os.path.join(tempfile.mkdtemp(), "import_test.json")
    >>> _ = open(p, "wb").write(_oj.dumps({"hives": {}}))
    >>> import_json(p)
    """
    hives = parse_registry_document(orjson.loads(Path(path).read_bytes()))
    backend = get_backend()
    for hive in hives:
        _import_key(backend, backend.get_hive(hive.hive), hive.key)


def _import_key(backend: RegistryBackend, parent_key: FakeRegistryKey, record: KeyRecord) -> None:
    """Write one parsed key's values and subkeys into the backend."""
    for value in record.values:
        backend.set_value(parent_key, value.name, value.data, value.value_type)
    for sub in record.subkeys:
        child_key = backend.create_key(parent_key, sub.name)
        _import_key(backend, child_key, sub.key)


def export_json(path: str | Path) -> None:
    """Export the currently active backend's state to a JSON file.

    Walks all hives using ``enum_keys`` recursively, collects values
    via ``enum_values``, builds a dict structure, and writes JSON.

    >>> import tempfile, os
    >>> p = os.path.join(tempfile.mkdtemp(), "export_test.json")
    >>> export_json(p)
    >>> assert os.path.exists(p)
    """
    backend = get_backend()
    hives: dict[str, SnapshotKeyDict] = {}

    for hive_int, hive_name in sorted(hive_name_hashed_by_int.items(), key=lambda kv: kv[1]):
        try:
            hive_key = backend.get_hive(hive_int)
        except OSError:
            continue
        hives[hive_name] = _export_key_recursive(backend, hive_key)

    raw = orjson.dumps(SnapshotDict(hives=hives), option=orjson.OPT_INDENT_2)
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(raw)


def _export_key_recursive(backend: RegistryBackend, key: FakeRegistryKey) -> SnapshotKeyDict:
    """Recursively build the snapshot dict of the backend's key tree."""
    values: dict[str, SnapshotValueDict] = {}
    for entry in sorted(backend.enum_values(key), key=lambda e: e.name):
        values[entry.name] = SnapshotValueDict(data=encode_value(entry.data), type=entry.value_type)

    keys: dict[str, SnapshotKeyDict] = {}
    for sname in sorted(backend.enum_keys(key)):
        child_key = backend.get_key(key, sname)
        keys[sname] = _export_key_recursive(backend, child_key)

    return SnapshotKeyDict(
        last_modified_ns=backend.query_info(key).last_modified_ns,
        values=values,
        keys=keys,
    )


__all__ = ["export_json", "import_json"]
