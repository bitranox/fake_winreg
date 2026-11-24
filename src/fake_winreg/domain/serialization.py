"""Pure conversion between FakeRegistry, typed dicts and parsed document records.

No I/O - just data transformation. Used by the JSON import/export adapters,
``JsonBackend`` and ``SaveKey``/``LoadKey``.

A JSON registry document is decoded by the caller (orjson or json) and parsed
here exactly once into frozen records (:class:`KeyRecord`, :class:`ValueRecord`,
...).  Every reader then walks the records instead of re-checking raw dicts.
The parser is deliberately lenient, because documents written by older
versions or by hand must keep loading: entries that are not JSON objects are
skipped, a missing or non-integer ``type`` becomes ``1`` (REG_SZ), a missing or
non-integer timestamp becomes ``0``, and unknown hive names are ignored.
"""

from __future__ import annotations

import base64
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, TypedDict, cast

from .constants import hive_int_by_name, hive_name_hashed_by_int
from .registry import (
    FakeRegistry,
    FakeRegistryKey,
    FakeRegistryValue,
)

if TYPE_CHECKING:
    from .types import RegData


class Base64Marker(TypedDict):
    """Marker for base64-encoded bytes in JSON serialization."""

    _base64: str


class SnapshotValueDict(TypedDict):
    """A value as ``export_json`` writes it (no per-value timestamp)."""

    data: object
    type: int


class ValueDict(SnapshotValueDict):
    """Serialized registry value."""

    last_modified_ns: int | None


class KeyDict(TypedDict):
    """Serialized registry key."""

    last_modified_ns: int
    values: dict[str, ValueDict]
    keys: dict[str, KeyDict]


class SnapshotKeyDict(TypedDict):
    """A key as ``export_json`` writes it (values without timestamps)."""

    last_modified_ns: int
    values: dict[str, SnapshotValueDict]
    keys: dict[str, SnapshotKeyDict]


class RegistryDict(TypedDict):
    """Top-level serialized registry structure."""

    hives: dict[str, KeyDict]


class SnapshotDict(TypedDict):
    """Top-level structure ``export_json`` writes."""

    hives: dict[str, SnapshotKeyDict]


@dataclass(frozen=True, slots=True)
class ValueRecord:
    """One value parsed from a JSON registry document."""

    name: str
    data: RegData
    value_type: int
    last_modified_ns: int


@dataclass(frozen=True, slots=True)
class SubkeyRecord:
    """A named child key parsed from a JSON registry document."""

    name: str
    key: KeyRecord


@dataclass(frozen=True, slots=True)
class KeyRecord:
    """One key body parsed from a JSON registry document, children in document order."""

    last_modified_ns: int
    values: tuple[ValueRecord, ...]
    subkeys: tuple[SubkeyRecord, ...]


@dataclass(frozen=True, slots=True)
class HiveRecord:
    """A known hive of a JSON registry document with its parsed body."""

    hive: int
    name: str
    key: KeyRecord


# ---------------------------------------------------------------------------
# Parsing a decoded JSON document (the boundary)
# ---------------------------------------------------------------------------


def parse_registry_document(document: object) -> tuple[HiveRecord, ...]:
    """Parse a decoded ``{"hives": {...}}`` document into hive records.

    Args:
        document: The decoded JSON document.

    Returns:
        One record per known hive whose body is an object, in document order;
        empty when ``hives`` is missing or not an object.

    Raises:
        AttributeError: If *document* is not a mapping (readers raised this
            from ``.get`` before the parser existed, so callers may catch it).
        TypeError: If a ``_base64`` payload is not a string or bytes.
        binascii.Error: If a ``_base64`` payload is not valid base64.

    Example:
        >>> [h.name for h in parse_registry_document({"hives": {"HKEY_USERS": {}, "HKEY_NOPE": {}}})]
        ['HKEY_USERS']
    """
    hives = _as_object_dict(_require_mapping(document).get("hives", {}))
    if hives is None:
        return ()
    records: list[HiveRecord] = []
    for name, body in hives.items():
        key_body = _as_object_dict(body)
        if not isinstance(name, str) or name not in hive_int_by_name or key_body is None:
            continue
        records.append(HiveRecord(hive=hive_int_by_name[name], name=name, key=_parse_key(key_body)))
    return tuple(records)


def parse_key_document(document: object) -> KeyRecord:
    """Parse a decoded key document (the shape ``SaveKey`` writes).

    Raises:
        AttributeError: If *document* is not a mapping.
        TypeError: If a ``_base64`` payload is not a string or bytes.
        binascii.Error: If a ``_base64`` payload is not valid base64.

    Example:
        >>> parse_key_document({"values": {"n": {"data": 1, "type": 4}}}).values[0].value_type
        4
    """
    return _parse_key(dict(_require_mapping(document)))


def _require_mapping(document: object) -> Mapping[object, object]:
    if not isinstance(document, Mapping):
        raise AttributeError(f"a registry document must be a JSON object, got {type(document).__name__}")
    return cast("Mapping[object, object]", document)


def _as_object_dict(raw: object) -> dict[object, object] | None:
    """Return *raw* as a dict of unknown content, or None when it is not a dict."""
    if isinstance(raw, dict):
        return cast("dict[object, object]", raw)
    return None


def _int_or(raw: object, default: int) -> int:
    # bool is an int subclass and was always kept as-is; preserve that.
    return raw if isinstance(raw, int) else default


def _parse_key(body: dict[object, object]) -> KeyRecord:
    # Keyword order is evaluation order: values decode before subkeys, so a bad
    # payload raises the same error the old values-then-keys walk raised.
    return KeyRecord(
        last_modified_ns=_int_or(body.get("last_modified_ns", 0), 0),
        values=_parse_values(body.get("values", {})),
        subkeys=_parse_subkeys(body.get("keys", {})),
    )


def _parse_values(raw: object) -> tuple[ValueRecord, ...]:
    entries = _as_object_dict(raw)
    if entries is None:
        return ()
    records: list[ValueRecord] = []
    for name, body in entries.items():
        value_body = _as_object_dict(body)
        if value_body is None:
            continue
        records.append(
            ValueRecord(
                name=str(name),
                data=decode_value(value_body.get("data")),
                value_type=_int_or(value_body.get("type", 1), 1),
                last_modified_ns=_int_or(value_body.get("last_modified_ns"), 0),
            )
        )
    return tuple(records)


def _parse_subkeys(raw: object) -> tuple[SubkeyRecord, ...]:
    entries = _as_object_dict(raw)
    if entries is None:
        return ()
    records: list[SubkeyRecord] = []
    for name, body in entries.items():
        key_body = _as_object_dict(body)
        if key_body is None:
            continue
        records.append(SubkeyRecord(name=str(name), key=_parse_key(key_body)))
    return tuple(records)


def decode_value(data: object) -> RegData:
    """Decode one value's ``data`` field from a decoded JSON document.

    A ``{"_base64": ...}`` object becomes bytes, any other object its ``str()``,
    a list a list of ``str()``-ed items; None, str, int and bytes pass through
    and everything else (floats, ...) becomes its ``str()``.

    Raises:
        TypeError: If a ``_base64`` payload is not a string or bytes-like.
        binascii.Error: If a ``_base64`` payload is not valid base64.

    Example:
        >>> decode_value({"_base64": "AP8="}), decode_value([1, "a"]), decode_value(1.5)
        (b'\\x00\\xff', ['1', 'a'], '1.5')
    """
    marker = _as_object_dict(data)
    if marker is not None:
        if "_base64" in marker:
            return _decode_base64(marker["_base64"])
        return str(data)
    if isinstance(data, list):
        return [str(item) for item in cast("list[object]", data)]
    if data is None or isinstance(data, (str, int, bytes)):
        return data
    return str(data)


def _decode_base64(payload: object) -> bytes:
    if isinstance(payload, (str, bytes, bytearray)):
        return base64.b64decode(payload)
    if isinstance(payload, memoryview):
        return base64.b64decode(payload.tobytes())
    # The same refusal base64.b64decode itself raises for a non-string payload.
    raise TypeError(f"argument should be a bytes-like object or ASCII string, not {type(payload).__name__!r}")


# ---------------------------------------------------------------------------
# Records -> FakeRegistry
# ---------------------------------------------------------------------------


def dict_to_registry(document: object) -> FakeRegistry:
    """Build a FakeRegistry from a decoded JSON registry document.

    Args:
        document: The decoded document (see :func:`parse_registry_document`).

    Returns:
        A new registry; hives the document does not name stay empty.

    Raises:
        AttributeError: If *document* is not a mapping.

    Example:
        >>> from fake_winreg.domain.test_registries import get_minimal_windows_testregistry
        >>> reg = get_minimal_windows_testregistry()
        >>> data = registry_to_dict(reg)
        >>> reg2 = dict_to_registry(data)
        >>> assert list(reg2.hive.keys()) == list(reg.hive.keys())
    """
    registry = FakeRegistry()
    for hive in parse_registry_document(document):
        populate_key(registry.hive[hive.hive], hive.key, full_key=hive.name, parent=None)
    return registry


def populate_key(
    key: FakeRegistryKey,
    record: KeyRecord,
    *,
    full_key: str,
    parent: FakeRegistryKey | None,
) -> None:
    """Graft a parsed key record onto *key*, recursively building its children.

    Values are merged into the existing ones; a child with the name of an
    existing subkey replaces that subkey.

    Args:
        key: The key to fill in place.
        record: The parsed key body.
        full_key: The full path to give *key* (children derive theirs from it).
        parent: The parent to link *key* to.
    """
    key.full_key = full_key
    key.parent_fake_registry_key = parent
    key.last_modified_ns = record.last_modified_ns

    for value in record.values:
        fval = FakeRegistryValue()
        fval.full_key = full_key
        fval.value_name = value.name
        fval.value = value.data
        fval.value_type = value.value_type
        fval.last_modified_ns = value.last_modified_ns
        key.values[value.name] = fval

    for sub in record.subkeys:
        child = FakeRegistryKey()
        child_full = f"{full_key}\\{sub.name}" if full_key else sub.name
        populate_key(child, sub.key, full_key=child_full, parent=key)
        key.subkeys[sub.name] = child


# ---------------------------------------------------------------------------
# FakeRegistry -> typed dicts
# ---------------------------------------------------------------------------


def registry_to_dict(registry: FakeRegistry) -> RegistryDict:
    """Serialize a FakeRegistry to a JSON-compatible dict.

    >>> from fake_winreg.domain.test_registries import get_minimal_windows_testregistry
    >>> reg = get_minimal_windows_testregistry()
    >>> data = registry_to_dict(reg)
    >>> assert "hives" in data
    >>> assert "HKEY_LOCAL_MACHINE" in data["hives"]
    """
    hives: dict[str, KeyDict] = {}
    for hive_int, hive_key in sorted(registry.hive.items(), key=lambda kv: str(kv[0])):
        # The fallback keeps a hive added under a non-standard handle serialisable.
        hive_name = hive_name_hashed_by_int.get(hive_int, str(hive_int))
        hives[hive_name] = key_to_dict(hive_key)
    return RegistryDict(hives=hives)


def key_to_dict(key: FakeRegistryKey) -> KeyDict:
    """Recursively convert a FakeRegistryKey to a typed dict."""
    values: dict[str, ValueDict] = {}
    for vname, fval in key.values.items():
        values[vname] = ValueDict(
            data=encode_value(fval.value),
            type=fval.value_type,
            last_modified_ns=fval.last_modified_ns,
        )

    keys: dict[str, KeyDict] = {}
    for sname, skey in key.subkeys.items():
        keys[sname] = key_to_dict(skey)

    return KeyDict(
        last_modified_ns=key.last_modified_ns,
        values=values,
        keys=keys,
    )


def encode_value(value: RegData) -> object:
    """Encode a registry value for JSON serialization.

    bytes are base64-encoded with a Base64Marker. Everything else is native JSON.

    Example:
        >>> encode_value(b"\\x00\\xff"), encode_value("x")
        ({'_base64': 'AP8='}, 'x')
    """
    if isinstance(value, bytes):
        return Base64Marker(_base64=base64.b64encode(value).decode("ascii"))
    return value


__all__ = [
    "Base64Marker",
    "HiveRecord",
    "KeyDict",
    "KeyRecord",
    "RegistryDict",
    "SnapshotDict",
    "SnapshotKeyDict",
    "SnapshotValueDict",
    "SubkeyRecord",
    "ValueDict",
    "ValueRecord",
    "decode_value",
    "dict_to_registry",
    "encode_value",
    "key_to_dict",
    "parse_key_document",
    "parse_registry_document",
    "populate_key",
    "registry_to_dict",
]
