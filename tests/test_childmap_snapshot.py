"""ChildMap's ordered name snapshot under concurrency and overwrite, and CreateKey's hive-root rule.

The interleaving tests pause a real ``name_at``/``item_at`` call with a
per-thread trace function at the exact point the race needs, so they are
deterministic: no sleep decides whether the race happens.
"""

from __future__ import annotations

import os
import sys
import threading
import time
from typing import TYPE_CHECKING, TypeAlias

import pytest

from fake_winreg.adapters.persistence.sqlite_backend import SqliteBackend
from fake_winreg.domain import api
from fake_winreg.domain.constants import HKEY_CURRENT_USER, REG_SZ, hive_name_hashed_by_int
from fake_winreg.domain.memory_backend import InMemoryBackend
from fake_winreg.domain.registry import ChildMap, FakeRegistryValue

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path
    from types import FrameType

    from fake_winreg.application.ports import RegistryBackend
    from fake_winreg.domain.handles import PyHKEY

    # The shape sys.settrace takes: a tracer returns the tracer for the frame's events.
    _Tracer: TypeAlias = "Callable[[FrameType, str, object], _Tracer | None]"


def _names(children: ChildMap[int]) -> list[str]:
    """Every name ``name_at`` reports for the map's current length, read index by index as EnumKey does."""
    return [children.name_at(index) for index in range(len(children))]


class _PauseAfterSnapshotBuild:
    """Run ``name_at`` in a thread and hold it after the snapshot is built, before it is stored.

    The trigger is the first line event in ``name_at`` with a non-None local
    ``names``: that is the freshly built list or tuple, one statement before
    it is written to the map.
    """

    def __init__(self, children: ChildMap[int]) -> None:
        self.children = children
        self.paused = threading.Event()
        self.resume = threading.Event()
        self._fired = False

    def run(self) -> None:
        previous = sys.gettrace()
        sys.settrace(self._on_call)
        try:
            self.children.name_at(0)
        finally:
            sys.settrace(previous)

    def _on_call(self, frame: FrameType, event: str, arg: object) -> _Tracer | None:
        del event, arg
        return self._on_line if frame.f_code.co_name == "name_at" else None

    def _on_line(self, frame: FrameType, event: str, arg: object) -> _Tracer:
        del arg
        if event == "line" and not self._fired and frame.f_locals.get("names") is not None:
            self._fired = True
            self.paused.set()
            self.resume.wait(5)
        return self._on_line


@pytest.mark.os_agnostic
def test_a_mutation_racing_a_snapshot_build_is_not_lost() -> None:
    children: ChildMap[int] = ChildMap()
    children["a"] = 1
    gate = _PauseAfterSnapshotBuild(children)
    reader = threading.Thread(target=gate.run)
    reader.start()
    assert gate.paused.wait(5), "the reader never reached the snapshot store"
    writer = threading.Thread(target=children.__setitem__, args=("b", 2))
    writer.start()
    # A map without writer exclusion lets the writer finish now; one with it
    # holds the writer until the reader has stored its snapshot.
    writer.join(0.2)
    gate.resume.set()
    reader.join(5)
    writer.join(5)
    assert _names(children) == ["a", "b"]


class _DeleteWhenNameAtReturnsToItemAt:
    """Delete the name ``name_at`` hands back to ``item_at``, once, before ``item_at`` reads it."""

    def __init__(self, children: ChildMap[FakeRegistryValue]) -> None:
        self.children = children
        self.fired = False

    def _on_call(self, frame: FrameType, event: str, arg: object) -> _Tracer | None:
        del event, arg
        return self._on_event if frame.f_code.co_name == "name_at" else None

    def _on_event(self, frame: FrameType, event: str, arg: object) -> _Tracer:
        caller = frame.f_back
        if event == "return" and not self.fired and caller is not None and caller.f_code.co_name == "item_at":
            self.fired = True
            assert isinstance(arg, str)
            del self.children[arg]
        return self._on_event

    def call(self, action: Callable[[], object]) -> object:
        previous = sys.gettrace()
        sys.settrace(self._on_call)
        try:
            return action()
        finally:
            sys.settrace(previous)


def _value_map(*names: str) -> ChildMap[FakeRegistryValue]:
    children: ChildMap[FakeRegistryValue] = ChildMap()
    for name in names:
        value = FakeRegistryValue()
        value.value_name = name
        children[name] = value
    return children


@pytest.mark.os_agnostic
def test_item_at_past_the_shrunk_end_raises_index_error_not_key_error() -> None:
    children = _value_map("a", "b", "c")
    hook = _DeleteWhenNameAtReturnsToItemAt(children)
    with pytest.raises(IndexError):
        hook.call(lambda: children.item_at(2))
    assert hook.fired


@pytest.mark.os_agnostic
def test_item_at_returns_the_child_now_at_that_index_when_its_name_was_deleted() -> None:
    children = _value_map("a", "b", "c")
    hook = _DeleteWhenNameAtReturnsToItemAt(children)
    item = hook.call(lambda: children.item_at(0))
    assert hook.fired
    assert isinstance(item, FakeRegistryValue)
    assert item.value_name == "b"


@pytest.fixture
def root() -> PyHKEY:
    api.use_backend(InMemoryBackend())
    return api.CreateKey(HKEY_CURRENT_USER, "Root")


@pytest.mark.os_agnostic
def test_enum_value_maps_a_name_deleted_mid_lookup_to_winerror_259(root: PyHKEY) -> None:
    for name in ("a", "b"):
        api.SetValueEx(root, name, 0, REG_SZ, name)
    hook = _DeleteWhenNameAtReturnsToItemAt(root.handle.values)
    with pytest.raises(OSError, match="WinError 259") as excinfo:
        hook.call(lambda: api.EnumValue(root, 1))
    assert hook.fired
    assert getattr(excinfo.value, "winerror", None) == 259


def _value_name_at(handle: PyHKEY, index: int) -> str:
    return api.EnumValue(handle, index)[0]


_NAME_AT: tuple[Callable[[PyHKEY, int], str], ...] = (api.EnumKey, _value_name_at)


def _check_one(
    name_at: Callable[[PyHKEY, int], str], handle: PyHKEY, index: int, universe: frozenset[str]
) -> str | None:
    """Return ``"end"`` past the last child, a description of a wrong answer, or None when it is fine."""
    try:
        name = name_at(handle, index)
    except OSError as exc:
        return "end" if getattr(exc, "winerror", None) == 259 else f"{index}: {exc!r}"
    except (KeyError, IndexError) as exc:
        return f"{index}: {exc!r}"
    return None if name in universe else f"{index}: unknown name {name!r}"


def _enumerate(name_at: Callable[[PyHKEY, int], str], handle: PyHKEY, universe: frozenset[str]) -> str | None:
    """Walk one enumeration; return a description of the first wrong answer, else None."""
    for index in range(len(universe) + 2):
        outcome = _check_one(name_at, handle, index, universe)
        if outcome is not None:
            return None if outcome == "end" else outcome
    return None


def _toggle_children(handle: PyHKEY, names: list[str]) -> None:
    """Create every name (key and value), delete them all again, and repeat."""
    for step in range(1500):
        name = names[step % len(names)]
        if (step // len(names)) % 2 == 0:
            api.CreateKey(handle, name)
            api.SetValueEx(handle, name, 0, REG_SZ, name)
        else:
            api.DeleteKey(handle, name)
            api.DeleteValue(handle, name)


@pytest.mark.os_agnostic
def test_concurrent_enumeration_and_mutation_stays_consistent(root: PyHKEY) -> None:
    writer_names = [[f"w{w}_{i}" for i in range(16)] for w in range(2)]
    universe = frozenset(name for names in writer_names for name in names)
    stop = threading.Event()
    problems: list[str] = []

    def read() -> None:
        while not stop.is_set():
            walks = (_enumerate(name_at, root, universe) for name_at in _NAME_AT)
            problems.extend(problem for problem in walks if problem is not None)

    previous_interval = sys.getswitchinterval()
    sys.setswitchinterval(1e-5)
    try:
        readers = [threading.Thread(target=read) for _ in range(2)]
        writers = [threading.Thread(target=_toggle_children, args=(root, names)) for names in writer_names]
        for thread in readers + writers:
            thread.start()
        for thread in writers:
            thread.join(10)
        stop.set()
        for thread in readers:
            thread.join(10)
    finally:
        sys.setswitchinterval(previous_interval)

    assert problems == []
    key = root.handle
    assert [api.EnumKey(root, i) for i in range(len(key.subkeys))] == list(key.subkeys)
    assert [api.EnumValue(root, i)[0] for i in range(len(key.values))] == list(key.values)


@pytest.mark.os_agnostic
def test_replacing_a_child_keeps_its_position_and_shows_the_new_child() -> None:
    children: ChildMap[int] = ChildMap()
    for index, name in enumerate(("a", "b", "c")):
        children[name] = index
    assert _names(children) == ["a", "b", "c"]
    children["b"] = 99
    assert _names(children) == ["a", "b", "c"]
    assert children.item_at(1) == 99
    children["d"] = 3
    assert _names(children) == ["a", "b", "c", "d"]


def _best_overwrite_walk_seconds(count: int) -> float:
    children: ChildMap[FakeRegistryValue] = ChildMap()
    for index in range(count):
        children[f"v{index:06d}"] = FakeRegistryValue()
    best = float("inf")
    for _ in range(3):
        start = time.perf_counter()
        for index in range(count):
            children[children.name_at(index)] = FakeRegistryValue()
        best = min(best, time.perf_counter() - start)
    return best


@pytest.mark.os_agnostic
def test_an_enumerate_and_overwrite_walk_grows_linearly() -> None:
    _best_overwrite_walk_seconds(50)
    small = _best_overwrite_walk_seconds(1000)
    large = _best_overwrite_walk_seconds(8000)
    # Linear is ~8x; dropping the snapshot on every overwrite measured ~62x.
    assert large / small < 20, f"1000 -> {small:.4f}s, 8000 -> {large:.4f}s ({large / small:.1f}x)"


def _memory_backend(_tmp_path: Path) -> RegistryBackend:
    return InMemoryBackend()


def _sqlite_backend(tmp_path: Path) -> RegistryBackend:
    return SqliteBackend(os.fspath(tmp_path / "registry.db"))


_BACKENDS: dict[str, Callable[[Path], RegistryBackend]] = {"memory": _memory_backend, "sqlite": _sqlite_backend}


@pytest.mark.os_agnostic
@pytest.mark.parametrize("backend", sorted(_BACKENDS))
@pytest.mark.parametrize("sub_key", ["", None])
def test_create_key_with_no_sub_key_opens_every_hive_root(backend: str, sub_key: str | None, tmp_path: Path) -> None:
    api.use_backend(_BACKENDS[backend](tmp_path))
    for hive, name in hive_name_hashed_by_int.items():
        assert api.CreateKey(hive, sub_key).handle.full_key == name


@pytest.mark.os_agnostic
@pytest.mark.parametrize("backend", sorted(_BACKENDS))
@pytest.mark.parametrize("sub_key", ["", None])
def test_create_key_with_no_sub_key_refuses_a_subkey_with_winerror_1010(
    backend: str, sub_key: str | None, tmp_path: Path
) -> None:
    # Neither backend marks a hive root structurally (the in-memory hive root
    # has an anonymous parent, every SQLite key has none), so this pins the
    # rule on both.
    api.use_backend(_BACKENDS[backend](tmp_path))
    for hive in hive_name_hashed_by_int:
        child = api.CreateKey(hive, "Child")
        with pytest.raises(OSError, match=r"^\[WinError 1010\] The configuration registry key is invalid$") as excinfo:
            api.CreateKey(child, sub_key)
        assert type(excinfo.value) is OSError
        assert getattr(excinfo.value, "winerror", None) == 1010
