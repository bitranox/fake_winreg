"""Import/export functions for JSON registry snapshots.

These functions work with the currently active backend, allowing data
to be loaded from or saved to JSON files regardless of which backend
implementation is in use.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import orjson

from fake_winreg.application.ports import RegistryBackend
from fake_winreg.domain.api import _get_backend  # pyright: ignore[reportPrivateUsage]
from fake_winreg.domain.constants import hive_name_hashed_by_int
from fake_winreg.domain.registry import FakeRegistryKey
from fake_winreg.domain.serialization import _encode_value  # pyright: ignore[reportPrivateUsage]
from fake_winreg.domain.types import RegData

_HIVE_NAME_TO_INT: dict[str, int] = {v: k for k, v in hive_name_hashed_by_int.items()}


def import_json(path: str | Path) -> None:
    """Load JSON file data into the currently active backend.

    Walks the deserialized tree structure and calls ``create_key`` and
    ``set_value`` on the active backend for every key and value found.
    This works with any backend implementation (memory, SQLite, etc.).

    >>> import tempfile, os, orjson as _oj
    >>> p = os.path.join(tempfile.mkdtemp(), "import_test.json")
    >>> _ = open(p, "wb").write(_oj.dumps({"hives": {}}))
    >>> import_json(p)
    """
    file_path = Path(path)
    raw = file_path.read_bytes()
    data = orjson.loads(raw)

    hives_raw = data.get("hives", {})
    if not isinstance(hives_raw, dict):
        return
    hives_data = cast(dict[str, Any], hives_raw)

    backend = _get_backend()

    for hive_name, hive_dict in hives_data.items():
        hive_int = _HIVE_NAME_TO_INT.get(hive_name)
        if hive_int is None or not isinstance(hive_dict, dict):
            continue
        hive_key = backend.get_hive(hive_int)
        _import_key_recursive(backend, hive_key, cast(dict[str, Any], hive_dict))


def _import_key_recursive(backend: RegistryBackend, parent_key: FakeRegistryKey, data: dict[str, Any]) -> None:
    """Walk a key dict and create subkeys/values in the backend."""
    values_data = data.get("values", {})
    if isinstance(values_data, dict):
        values_dict = cast(dict[str, Any], values_data)
        for vname, vdict in values_dict.items():
            if not isinstance(vdict, dict):
                continue
            typed_vdict = cast(dict[str, Any], vdict)
            value = _decode_import_value(typed_vdict.get("data"))
            raw_type: object = typed_vdict.get("type", 1)
            value_type: int = raw_type if isinstance(raw_type, int) else 1
            backend.set_value(parent_key, str(vname), value, value_type)

    keys_data = data.get("keys", {})
    if isinstance(keys_data, dict):
        keys_dict = cast(dict[str, Any], keys_data)
        for sname, sdict in keys_dict.items():
            if not isinstance(sdict, dict):
                continue
            child_key = backend.create_key(parent_key, str(sname))
            _import_key_recursive(backend, child_key, cast(dict[str, Any], sdict))


def _decode_import_value(data: object) -> RegData:
    """Decode a JSON value back to a registry data type."""
    import base64

    if isinstance(data, dict):
        typed_dict = cast(dict[str, Any], data)
        if "_base64" in typed_dict:
            return base64.b64decode(typed_dict["_base64"])
        return str(typed_dict)
    if isinstance(data, list):
        return [str(item) for item in cast(list[object], data)]
    if data is None or isinstance(data, (str, int, bytes)):
        return data
    return str(data)


def export_json(path: str | Path) -> None:
    """Export the currently active backend's state to a JSON file.

    Walks all hives using ``enum_keys`` recursively, collects values
    via ``enum_values``, builds a dict structure, and writes JSON.

    >>> import tempfile, os
    >>> p = os.path.join(tempfile.mkdtemp(), "export_test.json")
    >>> export_json(p)
    >>> assert os.path.exists(p)
    """
    backend = _get_backend()
    hives: dict[str, object] = {}

    for hive_int, hive_name in hive_name_hashed_by_int.items():
        try:
            hive_key = backend.get_hive(hive_int)
        except OSError:
            continue
        hives[hive_name] = _export_key_recursive(backend, hive_key)

    data = {"hives": hives}
    raw = orjson.dumps(data, option=orjson.OPT_INDENT_2)
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(raw)


def _export_key_recursive(backend: RegistryBackend, key: FakeRegistryKey) -> dict[str, object]:
    """Recursively build a dict from the backend's key tree."""
    _num_subkeys, _num_values, last_modified_ns = backend.query_info(key)

    values: dict[str, object] = {}
    for vname, vdata, vtype in backend.enum_values(key):
        values[vname] = {
            "data": _encode_value(vdata),
            "type": vtype,
        }

    keys: dict[str, object] = {}
    for sname in backend.enum_keys(key):
        child_key = backend.get_key(key, sname)
        keys[sname] = _export_key_recursive(backend, child_key)

    return {
        "last_modified_ns": last_modified_ns,
        "values": values,
        "keys": keys,
    }


__all__ = ["import_json", "export_json"]
