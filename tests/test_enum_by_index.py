"""EnumKey/EnumValue by index: never stale after a mutation, and linear over a whole walk."""

from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING

import pytest

from fake_winreg.adapters.persistence.json_backend import JsonBackend
from fake_winreg.domain import api
from fake_winreg.domain.constants import HKEY_CURRENT_USER, REG_SZ
from fake_winreg.domain.memory_backend import InMemoryBackend
from fake_winreg.domain.registry import FakeRegistryKey, set_fake_reg_key, set_fake_reg_value

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from fake_winreg.domain.handles import PyHKEY


def _all_subkeys(handle: PyHKEY) -> list[str]:
    names: list[str] = []
    index = 0
    while True:
        try:
            names.append(api.EnumKey(handle, index))
        except OSError:
            return names
        index += 1


def _all_values(handle: PyHKEY) -> list[tuple[object, ...]]:
    entries: list[tuple[object, ...]] = []
    index = 0
    while True:
        try:
            entries.append(api.EnumValue(handle, index))
        except OSError:
            return entries
        index += 1


@pytest.fixture
def root() -> PyHKEY:
    api.use_backend(InMemoryBackend())
    return api.CreateKey(HKEY_CURRENT_USER, "Root")


@pytest.mark.os_agnostic
def test_enum_key_follows_add_delete_and_re_add(root: PyHKEY) -> None:
    for name in ("a", "b", "c"):
        api.CreateKey(root, name)
    assert _all_subkeys(root) == ["a", "b", "c"]
    api.DeleteKey(root, "b")
    assert _all_subkeys(root) == ["a", "c"]
    api.CreateKey(root, "b")
    assert _all_subkeys(root) == ["a", "c", "b"]


@pytest.mark.os_agnostic
def test_enum_value_follows_add_delete_re_add_and_overwrite(root: PyHKEY) -> None:
    for name in ("a", "b", "c"):
        api.SetValueEx(root, name, 0, REG_SZ, name)
    assert [e[0] for e in _all_values(root)] == ["a", "b", "c"]
    api.DeleteValue(root, "b")
    api.SetValueEx(root, "b", 0, REG_SZ, "again")
    api.SetValueEx(root, "a", 0, REG_SZ, "changed")
    assert _all_values(root) == [("a", "changed", REG_SZ), ("c", "c", REG_SZ), ("b", "again", REG_SZ)]


@pytest.mark.os_agnostic
def test_enum_value_returns_a_plain_tuple(root: PyHKEY) -> None:
    api.SetValueEx(root, "v", 0, REG_SZ, "x")
    entry = api.EnumValue(root, 0)
    assert type(entry) is tuple
    assert repr(entry) == "('v', 'x', 1)"
    info = api.QueryInfoKey(root)
    assert type(info) is tuple
    assert info[:2] == (0, 1)


@pytest.mark.os_agnostic
def test_enum_past_the_end_raises_winerror_259(root: PyHKEY) -> None:
    api.CreateKey(root, "only")
    api.SetValueEx(root, "only", 0, REG_SZ, "x")
    for call in (api.EnumKey, api.EnumValue):
        with pytest.raises(OSError, match="WinError 259") as excinfo:
            call(root, 1)
        assert getattr(excinfo.value, "winerror", None) == 259


@pytest.mark.os_agnostic
def test_a_negative_index_counts_from_the_end_as_before(root: PyHKEY) -> None:
    for name in ("a", "b"):
        api.CreateKey(root, name)
        api.SetValueEx(root, name, 0, REG_SZ, name)
    assert api.EnumKey(root, -1) == "b"
    assert api.EnumValue(root, -2) == ("a", "a", REG_SZ)


def _key(handle: PyHKEY) -> FakeRegistryKey:
    return handle.handle


_MAP_MUTATIONS: dict[str, Callable[[FakeRegistryKey], None]] = {
    "pop": lambda k: k.subkeys.pop("a") and None,
    "popitem": lambda k: k.subkeys.popitem() and None,
    "setdefault": lambda k: k.subkeys.setdefault("z", FakeRegistryKey()) and None,
    "update": lambda k: k.subkeys.update({"y": FakeRegistryKey()}),
    "clear": lambda k: k.subkeys.clear(),
    "delitem": lambda k: k.subkeys.__delitem__("b"),
    "set_fake_reg_key": lambda k: set_fake_reg_key(k, "w") and None,
}


@pytest.mark.os_agnostic
@pytest.mark.parametrize("mutation", sorted(_MAP_MUTATIONS))
def test_every_mapping_mutation_drops_the_name_snapshot(root: PyHKEY, mutation: str) -> None:
    for name in ("a", "b"):
        api.CreateKey(root, name)
    assert _all_subkeys(root) == ["a", "b"]
    key = _key(root)
    _MAP_MUTATIONS[mutation](key)
    assert _all_subkeys(root) == list(key.subkeys)


@pytest.mark.os_agnostic
def test_values_written_by_registry_helpers_are_seen(root: PyHKEY) -> None:
    api.SetValueEx(root, "a", 0, REG_SZ, "a")
    assert len(_all_values(root)) == 1
    set_fake_reg_value(_key(root), sub_key="", value_name="b", value="b")
    _key(root).values.pop("a")
    assert _all_values(root) == [("b", "b", REG_SZ)]


@pytest.mark.os_agnostic
def test_load_key_mutations_are_seen(root: PyHKEY, tmp_path: Path) -> None:
    api.CreateKey(root, "Target")
    target = api.OpenKey(root, "Target")
    api.CreateKey(target, "old")
    assert _all_subkeys(target) == ["old"]
    document: dict[str, object] = {"values": {"v": {"data": "x"}}, "keys": {"old": {}, "new": {}}}
    path = tmp_path / "k.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    api.LoadKey(root, "Target", str(path))
    assert _all_subkeys(target) == ["old", "new"]
    assert _all_values(target) == [("v", "x", 1)]


@pytest.mark.os_agnostic
@pytest.mark.parametrize("attribute", ["subkeys", "values"])
def test_child_maps_cannot_be_rebound(attribute: str) -> None:
    # A plain dict put in their place would skip the snapshot invalidation.
    with pytest.raises(AttributeError):
        setattr(FakeRegistryKey(), attribute, {})


@pytest.mark.os_agnostic
def test_json_backend_enumerates_by_index_and_sees_deletes(tmp_path: Path) -> None:
    backend = JsonBackend(tmp_path / "r.json")
    api.use_backend(backend)
    root = api.CreateKey(HKEY_CURRENT_USER, "Root")
    for name in ("a", "b", "c"):
        api.CreateKey(root, name)
        api.SetValueEx(root, name, 0, REG_SZ, name)
    api.DeleteKey(root, "a")
    api.DeleteValue(root, "c")
    assert _all_subkeys(root) == ["b", "c"]
    assert backend.subkey_name_at(root.handle, 0) == "b"
    assert backend.value_at(root.handle, 1).name == "b"
    with pytest.raises(IndexError):
        backend.value_at(root.handle, 2)


def _best_walk_seconds(count: int) -> float:
    api.use_backend(InMemoryBackend())
    root = api.CreateKey(HKEY_CURRENT_USER, "Big")
    key = root.handle
    for i in range(count):
        set_fake_reg_key(key, f"k{i:06d}")
        set_fake_reg_value(key, sub_key="", value_name=f"v{i:06d}", value="x")
    best = float("inf")
    for _ in range(5):
        start = time.perf_counter()
        for i in range(count):
            api.EnumKey(root, i)
            api.EnumValue(root, i)
        best = min(best, time.perf_counter() - start)
    return best


@pytest.mark.os_agnostic
def test_a_full_walk_by_index_grows_linearly() -> None:
    # Warm the code path first so the small run does not pay one-off costs.
    _best_walk_seconds(50)
    small = _best_walk_seconds(2000)
    large = _best_walk_seconds(16000)
    # Linear is ~8x; rebuilding the name and value lists per call measured ~90x at 1000 -> 8000.
    assert large / small < 20, f"2000 -> {small:.4f}s, 16000 -> {large:.4f}s ({large / small:.1f}x)"
