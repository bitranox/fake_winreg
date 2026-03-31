"""Pure conversion between FakeRegistry and plain dicts.

No I/O — just data transformation. Used by JSON and .reg import/export adapters.
"""

from __future__ import annotations

import base64
from typing import Any, cast

from .constants import (
    hive_name_hashed_by_int,
)
from .registry import (
    FakeRegistry,
    FakeRegistryKey,
    FakeRegistryValue,
)
from .types import RegData

_HIVE_NAME_TO_INT: dict[str, int] = {v: k for k, v in hive_name_hashed_by_int.items()}


def registry_to_dict(registry: FakeRegistry) -> dict[str, object]:
    """Serialize a FakeRegistry to a JSON-compatible dict.

    >>> from fake_winreg.domain.test_registries import get_minimal_windows_testregistry
    >>> reg = get_minimal_windows_testregistry()
    >>> data = registry_to_dict(reg)
    >>> assert "hives" in data
    >>> assert "HKEY_LOCAL_MACHINE" in data["hives"]
    """
    hives: dict[str, object] = {}
    for hive_int, hive_key in registry.hive.items():
        hive_name = hive_name_hashed_by_int.get(hive_int, str(hive_int))  # type: ignore[arg-type]
        hives[hive_name] = _key_to_dict(hive_key)
    return {"hives": hives}


def dict_to_registry(data: dict[str, object]) -> FakeRegistry:
    """Deserialize a dict into a FakeRegistry, rebuilding parent pointers.

    >>> from fake_winreg.domain.test_registries import get_minimal_windows_testregistry
    >>> reg = get_minimal_windows_testregistry()
    >>> data = registry_to_dict(reg)
    >>> reg2 = dict_to_registry(data)
    >>> assert list(reg2.hive.keys()) == list(reg.hive.keys())
    """
    registry = FakeRegistry()
    hives_raw = data.get("hives", {})
    if not isinstance(hives_raw, dict):
        return registry
    hives_data = cast(dict[str, Any], hives_raw)

    for hive_name, hive_dict in hives_data.items():
        hive_int = _HIVE_NAME_TO_INT.get(hive_name)
        if hive_int is None or not isinstance(hive_dict, dict):
            continue
        root_key = registry.hive[hive_int]
        _populate_key_from_dict(root_key, cast(dict[str, object], hive_dict), hive_name, parent=None)

    return registry


def _key_to_dict(key: FakeRegistryKey) -> dict[str, object]:
    """Recursively convert a FakeRegistryKey to a dict."""
    values: dict[str, object] = {}
    for vname, fval in key.values.items():
        values[vname] = {
            "data": _encode_value(fval.value),
            "type": fval.value_type,
            "last_modified_ns": fval.last_modified_ns,
        }

    keys: dict[str, object] = {}
    for sname, skey in key.subkeys.items():
        keys[sname] = _key_to_dict(skey)

    return {
        "last_modified_ns": key.last_modified_ns,
        "values": values,
        "keys": keys,
    }


def _populate_key_from_dict(
    key: FakeRegistryKey,
    data: dict[str, object],
    full_key: str,
    parent: FakeRegistryKey | None,
) -> None:
    """Populate a FakeRegistryKey from dict data, recursively building children."""
    key.full_key = full_key
    key.parent_fake_registry_key = parent

    last_mod = data.get("last_modified_ns", 0)
    key.last_modified_ns = last_mod if isinstance(last_mod, int) else 0

    values_data = data.get("values", {})
    if isinstance(values_data, dict):
        for vname, vdict in cast(dict[str, Any], values_data).items():
            if not isinstance(vdict, dict):
                continue
            vdict_typed = cast(dict[str, object], vdict)
            fval = FakeRegistryValue()
            fval.full_key = full_key
            fval.value_name = str(vname)
            fval.value = _decode_value(vdict_typed.get("data"))
            vtype = vdict_typed.get("type", 1)
            fval.value_type = vtype if isinstance(vtype, int) else 1
            last_mod_val = vdict_typed.get("last_modified_ns")
            fval.last_modified_ns = last_mod_val if isinstance(last_mod_val, int) else 0
            key.values[str(vname)] = fval

    keys_data = data.get("keys", {})
    if isinstance(keys_data, dict):
        for sname, sdict in cast(dict[str, Any], keys_data).items():
            if not isinstance(sdict, dict):
                continue
            child = FakeRegistryKey()
            sname_str = str(sname)
            child_full = f"{full_key}\\{sname_str}" if full_key else sname_str
            _populate_key_from_dict(child, cast(dict[str, object], sdict), child_full, parent=key)
            key.subkeys[sname_str] = child


def _encode_value(value: RegData) -> object:
    """Encode a registry value for JSON serialization.

    bytes are base64-encoded with a marker dict. Everything else is native JSON.
    """
    if isinstance(value, bytes):
        return {"_base64": base64.b64encode(value).decode("ascii")}
    return value


def _decode_value(data: object) -> RegData:
    """Decode a registry value from a deserialized dict."""
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


__all__ = [
    "dict_to_registry",
    "registry_to_dict",
]
