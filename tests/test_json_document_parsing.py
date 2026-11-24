"""Pin how every reader of a JSON registry document treats malformed shapes.

Four routes read the same document shape: ``dict_to_registry`` (and through it
``JsonBackend``), ``import_json`` and ``LoadKey``.  The tests here fix what each
route does with a missing, mistyped or unknown field, so that parsing the
document once at the boundary cannot quietly change what any route accepts.
"""

from __future__ import annotations

import binascii
import json
from typing import TYPE_CHECKING

import orjson
import pytest

from fake_winreg.adapters.persistence.json_backend import JsonBackend
from fake_winreg.adapters.persistence.json_io import import_json
from fake_winreg.domain import api
from fake_winreg.domain.constants import HKEY_CURRENT_USER, HKEY_LOCAL_MACHINE, hive_name_hashed_by_int
from fake_winreg.domain.memory_backend import InMemoryBackend
from fake_winreg.domain.serialization import dict_to_registry

if TYPE_CHECKING:
    from pathlib import Path

    from fake_winreg.domain.registry import FakeRegistry, FakeRegistryKey

_HKLM = "HKEY_LOCAL_MACHINE"


def _hklm_with(key_body: object) -> dict[str, object]:
    return {"hives": {_HKLM: key_body}}


def _value_doc(value_body: object) -> dict[str, object]:
    return _hklm_with({"values": {"v": value_body}})


def _only_value(registry: FakeRegistry) -> tuple[object, int, object]:
    value = registry.hive[HKEY_LOCAL_MACHINE].values["v"]
    return value.value, value.value_type, value.last_modified_ns


def _imported_hklm(tmp_path: Path, document: object) -> FakeRegistryKey:
    path = tmp_path / "doc.json"
    path.write_bytes(orjson.dumps(document))
    backend = InMemoryBackend()
    api.use_backend(backend)
    import_json(path)
    return backend.registry.hive[HKEY_LOCAL_MACHINE]


def _all_hives_empty(registry: FakeRegistry) -> bool:
    return all(not hive.subkeys and not hive.values for hive in registry.hive.values())


# ---------------------------------------------------------------------------
# Top-level document shape
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
@pytest.mark.parametrize("document", [{}, {"hives": []}, {"hives": "x"}, {"hives": None}, {"other": 1}])
def test_dict_to_registry_without_a_hives_object_gives_an_empty_registry(document: dict[str, object]) -> None:
    registry = dict_to_registry(document)
    assert _all_hives_empty(registry)
    assert set(registry.hive) == set(hive_name_hashed_by_int)


@pytest.mark.os_agnostic
def test_dict_to_registry_skips_unknown_hive_names_and_non_object_hives() -> None:
    registry = dict_to_registry(
        {"hives": {"HKEY_NOPE": {"values": {"v": {"data": "x"}}}, _HKLM: [1, 2], "HKEY_CURRENT_USER": "str"}}
    )
    assert _all_hives_empty(registry)


@pytest.mark.os_agnostic
@pytest.mark.parametrize("document", [[], None, "text", 3])
def test_json_backend_with_a_non_object_document_raises_attribute_error(tmp_path: Path, document: object) -> None:
    path = tmp_path / "reg.json"
    path.write_bytes(orjson.dumps(document))
    with pytest.raises(AttributeError):
        JsonBackend(path)


@pytest.mark.os_agnostic
@pytest.mark.parametrize("document", [[], None, "text", 3])
def test_import_json_with_a_non_object_document_raises_attribute_error(tmp_path: Path, document: object) -> None:
    with pytest.raises(AttributeError):
        _imported_hklm(tmp_path, document)


@pytest.mark.os_agnostic
@pytest.mark.parametrize("document", [{"hives": []}, {}, {"hives": {"HKEY_NOPE": {}}}, {"hives": {_HKLM: 5}}])
def test_import_json_ignores_documents_without_usable_hives(tmp_path: Path, document: object) -> None:
    hklm = _imported_hklm(tmp_path, document)
    assert not hklm.subkeys
    assert not hklm.values


# ---------------------------------------------------------------------------
# Key fields
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
@pytest.mark.parametrize(
    ("raw", "expected"),
    [(None, 0), ("12", 0), (1.5, 0), ([], 0), (42, 42), (True, True)],
)
def test_key_last_modified_ns_keeps_ints_and_bools_and_zeroes_the_rest(raw: object, expected: int) -> None:
    body: dict[str, object] = {} if raw is None else {"last_modified_ns": raw}
    registry = dict_to_registry(_hklm_with({"keys": {"Sub": body}}))
    sub = registry.hive[HKEY_LOCAL_MACHINE].subkeys["Sub"]
    assert sub.last_modified_ns == expected
    assert type(sub.last_modified_ns) is type(expected)


@pytest.mark.os_agnostic
def test_a_hive_body_overwrites_the_root_key_timestamp_with_zero_when_missing() -> None:
    registry = dict_to_registry(_hklm_with({}))
    assert registry.hive[HKEY_LOCAL_MACHINE].last_modified_ns == 0
    assert registry.hive[HKEY_CURRENT_USER].last_modified_ns != 0


@pytest.mark.os_agnostic
@pytest.mark.parametrize("values", [[], "x", 5, None])
def test_non_object_values_and_keys_are_ignored(values: object) -> None:
    registry = dict_to_registry(_hklm_with({"values": values, "keys": values}))
    assert _all_hives_empty(registry)


@pytest.mark.os_agnostic
def test_non_object_value_and_subkey_entries_are_skipped_others_kept() -> None:
    registry = dict_to_registry(
        _hklm_with({"values": {"bad": 1, "good": {"data": "x"}}, "keys": {"bad": [], "good": {}}})
    )
    hklm = registry.hive[HKEY_LOCAL_MACHINE]
    assert list(hklm.values) == ["good"]
    assert list(hklm.subkeys) == ["good"]


@pytest.mark.os_agnostic
def test_parsed_tree_has_full_keys_parents_and_value_full_keys() -> None:
    registry = dict_to_registry(_hklm_with({"keys": {"A": {"keys": {"B": {"values": {"n": {"data": 1}}}}}}}))
    hklm = registry.hive[HKEY_LOCAL_MACHINE]
    a = hklm.subkeys["A"]
    b = a.subkeys["B"]
    assert hklm.full_key == _HKLM
    assert hklm.parent_fake_registry_key is None
    assert a.full_key == rf"{_HKLM}\A"
    assert a.parent_fake_registry_key is hklm
    assert b.full_key == rf"{_HKLM}\A\B"
    assert b.parent_fake_registry_key is a
    assert b.values["n"].full_key == b.full_key
    assert b.values["n"].value_name == "n"


@pytest.mark.os_agnostic
def test_a_backslash_in_a_subkey_name_stays_one_key_in_dict_to_registry() -> None:
    registry = dict_to_registry(_hklm_with({"keys": {"a\\b": {}}}))
    assert list(registry.hive[HKEY_LOCAL_MACHINE].subkeys) == ["a\\b"]


@pytest.mark.os_agnostic
def test_non_str_names_from_python_callers_are_str_ed_and_later_entries_win() -> None:
    body: dict[object, object] = {1: {"data": "first"}, "1": {"data": "second"}}
    registry = dict_to_registry(_hklm_with({"values": body, "keys": {2: {}}}))
    hklm = registry.hive[HKEY_LOCAL_MACHINE]
    assert hklm.values["1"].value == "second"
    assert list(hklm.subkeys) == ["2"]


# ---------------------------------------------------------------------------
# Value fields
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
@pytest.mark.parametrize(
    ("raw", "expected"),
    [(None, 1), ("4", 1), (4.0, 1), ([], 1), (4, 4), (-1, -1), (True, True)],
)
def test_value_type_keeps_ints_and_bools_and_defaults_the_rest_to_one(raw: object, expected: int) -> None:
    body: dict[str, object] = {"data": "x"} if raw is None else {"data": "x", "type": raw}
    _data, value_type, _ts = _only_value(dict_to_registry(_value_doc(body)))
    assert value_type == expected
    assert type(value_type) is type(expected)


@pytest.mark.os_agnostic
@pytest.mark.parametrize(("raw", "expected"), [(None, 0), ("1", 0), (3, 3), (True, True)])
def test_value_last_modified_ns_keeps_ints_and_zeroes_the_rest(raw: object, expected: int) -> None:
    body: dict[str, object] = {"data": "x"} if raw is None else {"data": "x", "last_modified_ns": raw}
    _data, _type, last_modified = _only_value(dict_to_registry(_value_doc(body)))
    assert last_modified == expected
    assert type(last_modified) is type(expected)


@pytest.mark.os_agnostic
@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ({"_base64": "AP8="}, b"\x00\xff"),
        ({"_base64": "AP8=", "extra": 1}, b"\x00\xff"),
        ({"other": 1}, "{'other': 1}"),
        ({}, "{}"),
        ([1, None, "a", [2], {"k": 1}], ["1", "None", "a", "[2]", "{'k': 1}"]),
        ([], []),
        (None, None),
        ("text", "text"),
        (7, 7),
        (True, True),
        (1.5, "1.5"),
    ],
)
def test_value_data_decoding(raw: object, expected: object) -> None:
    data, _type, _ts = _only_value(dict_to_registry(_value_doc({"data": raw})))
    assert data == expected
    assert type(data) is type(expected)


@pytest.mark.os_agnostic
def test_missing_data_decodes_to_none() -> None:
    data, value_type, _ts = _only_value(dict_to_registry(_value_doc({})))
    assert data is None
    assert value_type == 1


@pytest.mark.os_agnostic
def test_a_non_string_base64_payload_raises_type_error() -> None:
    with pytest.raises(TypeError):
        dict_to_registry(_value_doc({"data": {"_base64": 123}}))


@pytest.mark.os_agnostic
def test_an_invalid_base64_payload_raises_binascii_error() -> None:
    with pytest.raises(binascii.Error):
        dict_to_registry(_value_doc({"data": {"_base64": "A"}}))


# ---------------------------------------------------------------------------
# import_json: same decoding, its own key handling
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_import_json_decodes_values_like_dict_to_registry(tmp_path: Path) -> None:
    hklm = _imported_hklm(
        tmp_path,
        _hklm_with(
            {
                "values": {
                    "b": {"data": {"_base64": "AP8="}, "type": 3},
                    "d": {"data": {"x": 1}},
                    "l": {"data": [1, None]},
                    "f": {"data": 1.5, "type": "4"},
                    "t": {"data": "x", "type": True},
                    "skip": 5,
                },
                "keys": {"skip": [], "Sub": {"values": {"n": {"data": None}}}},
            }
        ),
    )
    got = {name: (v.value, v.value_type) for name, v in hklm.values.items()}
    assert got == {
        "b": (b"\x00\xff", 3),
        "d": ("{'x': 1}", 1),
        "l": (["1", "None"], 1),
        "f": ("1.5", 1),
        "t": ("x", True),
    }
    assert list(hklm.subkeys) == ["Sub"]
    assert hklm.subkeys["Sub"].values["n"].value is None


@pytest.mark.os_agnostic
def test_import_json_ignores_document_timestamps(tmp_path: Path) -> None:
    hklm = _imported_hklm(
        tmp_path, _hklm_with({"keys": {"Sub": {"last_modified_ns": 5, "values": {"v": {"last_modified_ns": 6}}}}})
    )
    sub = hklm.subkeys["Sub"]
    assert sub.last_modified_ns != 5
    assert sub.values["v"].last_modified_ns != 6


@pytest.mark.os_agnostic
def test_import_json_splits_a_backslash_subkey_name_into_nested_keys(tmp_path: Path) -> None:
    hklm = _imported_hklm(tmp_path, _hklm_with({"keys": {"a\\b": {"values": {"v": {"data": "x"}}}}}))
    assert list(hklm.subkeys) == ["a"]
    assert hklm.subkeys["a"].subkeys["b"].values["v"].value == "x"


@pytest.mark.os_agnostic
def test_import_json_raises_on_a_bad_base64_payload(tmp_path: Path) -> None:
    with pytest.raises(binascii.Error):
        _imported_hklm(tmp_path, _value_doc({"data": {"_base64": "A"}}))


# ---------------------------------------------------------------------------
# LoadKey: grafts a key document into an existing key
# ---------------------------------------------------------------------------


def _load_into_fresh(tmp_path: Path, document: object, *, prepare: dict[str, object] | None = None) -> FakeRegistryKey:
    backend = InMemoryBackend()
    api.use_backend(backend)
    target = api.CreateKey(HKEY_LOCAL_MACHINE, r"SOFTWARE\Target")
    if prepare is not None:
        api.SetValueEx(target, "old", 0, 1, "kept")
        api.CreateKey(target, "Same")
        api.SetValueEx(api.OpenKey(target, "Same"), "inner", 0, 1, "gone")
    path = tmp_path / "key.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    api.LoadKey(HKEY_LOCAL_MACHINE, r"SOFTWARE\Target", str(path))
    return backend.registry.hive[HKEY_LOCAL_MACHINE].subkeys["SOFTWARE"].subkeys["Target"]


@pytest.mark.os_agnostic
def test_load_key_merges_values_and_replaces_same_named_subkeys(tmp_path: Path) -> None:
    target = _load_into_fresh(
        tmp_path,
        {"values": {"new": {"data": "n"}, "bad": 1}, "keys": {"Same": {}, "bad": "x"}},
        prepare={},
    )
    assert target.values["old"].value == "kept"
    assert target.values["new"].value == "n"
    assert "bad" not in target.values
    assert list(target.subkeys) == ["Same"]
    assert not target.subkeys["Same"].values
    assert target.subkeys["Same"].parent_fake_registry_key is target
    assert target.last_modified_ns == 0
    assert target.full_key == r"HKEY_LOCAL_MACHINE\SOFTWARE\Target"


@pytest.mark.os_agnostic
@pytest.mark.parametrize("document", [[], None, "x"])
def test_load_key_with_a_non_object_document_raises_attribute_error_after_creating_the_key(
    tmp_path: Path, document: object
) -> None:
    backend = InMemoryBackend()
    api.use_backend(backend)
    path = tmp_path / "key.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(AttributeError):
        api.LoadKey(HKEY_LOCAL_MACHINE, r"SOFTWARE\Made", str(path))
    assert "Made" in backend.registry.hive[HKEY_LOCAL_MACHINE].subkeys["SOFTWARE"].subkeys
