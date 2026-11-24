"""Core registry data structures and operations.

Provides the in-memory representation of a Windows registry: hives, keys,
and values, plus functions to create and retrieve them.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Iterator, MutableMapping
from typing import TYPE_CHECKING, TypeVar

from .constants import (
    HKEY_CLASSES_ROOT,
    HKEY_CURRENT_CONFIG,
    HKEY_CURRENT_USER,
    HKEY_DYN_DATA,
    HKEY_LOCAL_MACHINE,
    HKEY_PERFORMANCE_DATA,
    HKEY_USERS,
    KEY_READ,
    REG_SZ,
)

if TYPE_CHECKING:
    from collections.abc import ItemsView, KeysView, ValuesView

    from .types import RegData

_V = TypeVar("_V")

# One lock for every ChildMap rather than one per map: a registry holds two
# maps per key, so per-map locks would add two lock objects per key. Writers
# hold it for a single dict operation, so sharing it costs no real contention.
# Re-entrant because ChildMap.item_at calls name_at while holding it.
_WRITE_LOCK = threading.RLock()


class ChildMap(MutableMapping[str, _V]):
    """Insertion-ordered name -> child mapping that can answer "the n-th name" cheaply.

    ``EnumKey``/``EnumValue`` ask for children by position, one call per index.
    Building a fresh name list per call made a full enumeration quadratic, so
    the map keeps one ordered name snapshot and drops it whenever the set or
    order of names changes (adding or removing a name; replacing the child of
    an existing name keeps its position and keeps the snapshot).
    It is a ``MutableMapping`` over a private dict rather than a ``dict``
    subclass: the mixin ``pop``/``popitem``/``setdefault``/``update`` all route
    through ``__setitem__``/``__delitem__``, so no mutating path can skip the
    invalidation (a ``dict`` subclass would have to re-implement every C-level
    mutator and would still miss ``dict.__setitem__(m, ...)`` calls).

    Thread safety: writers and snapshot builds hold one module-wide lock, so a
    snapshot built from the old names can never be stored after a writer has
    dropped it; reading an existing snapshot takes no lock.

    Example:
        >>> children: ChildMap[int] = ChildMap()
        >>> children["a"] = 1
        >>> children["b"] = 2
        >>> children.name_at(1)
        'b'
        >>> del children["a"]
        >>> children.name_at(0), children.item_at(0)
        ('b', 2)
        >>> children.name_at(1)
        Traceback (most recent call last):
            ...
        IndexError: list index out of range
    """

    __slots__ = ("_data", "_names")

    def __init__(self) -> None:
        self._data: dict[str, _V] = {}
        self._names: list[str] | None = None

    def __getitem__(self, name: str) -> _V:
        return self._data[name]

    def __setitem__(self, name: str, child: _V) -> None:
        # Replacing the child of an existing name keeps its position, so the
        # snapshot stays valid; dropping it anyway made an enumerate-and-
        # replace walk quadratic. The new-or-existing test must sit under the
        # same lock as the write, or a concurrent delete between the two
        # re-adds the name at the end with the snapshot still in place.
        with _WRITE_LOCK:
            is_new = name not in self._data
            self._data[name] = child
            if is_new:
                self._names = None

    def __delitem__(self, name: str) -> None:
        with _WRITE_LOCK:
            del self._data[name]
            self._names = None

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __contains__(self, name: object) -> bool:
        return name in self._data

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._data!r})"

    def clear(self) -> None:
        """Remove every child (one dict clear instead of the mixin's popitem loop)."""
        with _WRITE_LOCK:
            self._data.clear()
            self._names = None

    def get_or_add(self, name: str, child: _V) -> _V:
        """Return the child stored under *name*, first storing *child* there if *name* is absent.

        Atomic, unlike the mixin ``setdefault`` (look up, then store): two
        threads creating the same name both get the one child that was stored,
        so neither goes on writing into an orphan.

        Args:
            name: Child name.
            child: Child to store when *name* is absent.

        Returns:
            The child now stored under *name*.

        Example:
            >>> children: ChildMap[int] = ChildMap()
            >>> children.get_or_add("a", 1), children.get_or_add("a", 2)
            (1, 1)
        """
        with _WRITE_LOCK:
            if name in self._data:
                return self._data[name]
            self._data[name] = child
            self._names = None
            return child

    def keys(self) -> KeysView[str]:
        """Return a live read-only view of the child names in insertion order."""
        return self._data.keys()

    def values(self) -> ValuesView[_V]:
        """Return a live read-only view of the children in insertion order."""
        return self._data.values()

    def items(self) -> ItemsView[str, _V]:
        """Return a live read-only view of ``(name, child)`` pairs in insertion order."""
        return self._data.items()

    def name_at(self, index: int) -> str:
        """Return the name at *index* in insertion order (list indexing rules).

        Args:
            index: Position to read; negative values count from the end, as
                they did when callers indexed ``list(map)`` directly.

        Returns:
            The child name at that position.

        Raises:
            IndexError: If *index* is out of range.
        """
        names = self._names
        if names is None:
            # Build and store under the writers' lock: built outside it, a
            # writer could drop the snapshot between the build and the store,
            # and the stale list would then be served until the next mutation.
            with _WRITE_LOCK:
                names = self._names
                if names is None:
                    names = list(self._data)
                    self._names = names
        return names[index]

    def item_at(self, index: int) -> _V:
        """Return the child at *index* in insertion order (see :meth:`name_at`).

        A name deleted by another thread between the position lookup and the
        child lookup is never reported as ``KeyError``: the lookup is repeated
        once with writers held off, so the answer is the child now at *index*
        or ``IndexError``.

        Raises:
            IndexError: If *index* is out of range.
        """
        try:
            return self._data[self.name_at(index)]
        except KeyError:
            pass
        # The delete that removed the name has finished (it held the lock) and
        # dropped the snapshot, so name_at here reads a fresh one; the lock is
        # re-entrant and keeps writers out until the child is read.
        with _WRITE_LOCK:
            return self._data[self.name_at(index)]


class FakeRegistry:
    """Container for the entire fake Windows registry."""

    def __init__(self) -> None:
        self.hive: dict[int, FakeRegistryKey] = {}
        self.hive[HKEY_CLASSES_ROOT] = set_fake_reg_key(FakeRegistryKey(), "HKEY_CLASSES_ROOT")
        self.hive[HKEY_CURRENT_CONFIG] = set_fake_reg_key(FakeRegistryKey(), "HKEY_CURRENT_CONFIG")
        self.hive[HKEY_CURRENT_USER] = set_fake_reg_key(FakeRegistryKey(), "HKEY_CURRENT_USER")
        self.hive[HKEY_DYN_DATA] = set_fake_reg_key(FakeRegistryKey(), "HKEY_DYN_DATA")
        self.hive[HKEY_LOCAL_MACHINE] = set_fake_reg_key(FakeRegistryKey(), "HKEY_LOCAL_MACHINE")
        self.hive[HKEY_PERFORMANCE_DATA] = set_fake_reg_key(FakeRegistryKey(), "HKEY_PERFORMANCE_DATA")
        self.hive[HKEY_USERS] = set_fake_reg_key(FakeRegistryKey(), "HKEY_USERS")


class FakeRegistryKey:
    """Represents a single registry key (folder) in the fake registry.

    >>> fake_reg_root = FakeRegistryKey()
    """

    def __init__(self) -> None:
        self.full_key: str = ""
        self.parent_fake_registry_key: FakeRegistryKey | None = None
        self._subkeys: ChildMap[FakeRegistryKey] = ChildMap()
        self._values: ChildMap[FakeRegistryValue] = ChildMap()
        self.last_modified_ns: int = 0

    # Read-only attributes: rebinding them to a plain dict would bypass the
    # ChildMap snapshot invalidation that index-based enumeration relies on.
    @property
    def subkeys(self) -> ChildMap[FakeRegistryKey]:
        """Child keys by name, in insertion order."""
        return self._subkeys

    @property
    def values(self) -> ChildMap[FakeRegistryValue]:
        """Values of this key by name, in insertion order."""
        return self._values


class FakeRegistryValue:
    """Represents a single registry value (data item) within a key.

    >>> fake_reg_value = FakeRegistryValue()
    """

    def __init__(self) -> None:
        self.full_key: str = ""
        self.value_name: str = ""
        self.value: RegData = None
        self.value_type: int = REG_SZ
        self.access: int = KEY_READ
        self.last_modified_ns: int | None = None


def set_fake_reg_key(
    fake_reg_key: FakeRegistryKey,
    sub_key: str | None = None,
    last_modified_ns: int | None = None,
) -> FakeRegistryKey:
    r"""Create a registry key if it does not already exist.

    Automatically creates intermediate parent keys as needed.

    >>> fake_reg_root = FakeRegistryKey()
    >>> key = set_fake_reg_key(fake_reg_key=fake_reg_root, sub_key='HKEY_LOCAL_MACHINE')
    >>> assert key.full_key == 'HKEY_LOCAL_MACHINE'
    >>> result = set_fake_reg_key(
    ...     fake_reg_key=fake_reg_root,
    ...     sub_key=r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT',
    ... )
    >>> assert result.full_key == r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT'
    """
    if last_modified_ns is None:
        last_modified_ns = get_windows_timestamp_now()

    key_parts_full = fake_reg_key.full_key.split("\\")
    key_parts_sub = sub_key.split("\\") if sub_key else []

    data = fake_reg_key
    for key_part in key_parts_sub:
        key_parts_full.append(key_part)
        child = data.subkeys.get(key_part)
        if child is None:
            # Fill the key in before publishing it: a thread enumerating or
            # opening it in between would otherwise see an empty full_key.
            # get_or_add keeps the one child a racing creator stored first.
            new_child = FakeRegistryKey()
            new_child.full_key = "\\".join(key_parts_full).strip("\\")
            new_child.last_modified_ns = last_modified_ns
            new_child.parent_fake_registry_key = data
            child = data.subkeys.get_or_add(key_part, new_child)
        data = child

    return data


def get_fake_reg_key(fake_reg_key: FakeRegistryKey, sub_key: str) -> FakeRegistryKey:
    r"""Retrieve an existing registry key by path.

    Raises FileNotFoundError if the key does not exist.

    >>> fake_reg_root = FakeRegistryKey()
    >>> _ = set_fake_reg_key(fake_reg_key=fake_reg_root,
    ...     sub_key=r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT')

    >>> result = get_fake_reg_key(fake_reg_key=fake_reg_root,
    ...     sub_key=r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT')
    >>> assert result.full_key == r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT'

    >>> get_fake_reg_key(  # doctest: +ELLIPSIS
    ...     fake_reg_key=fake_reg_root,
    ...     sub_key=r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\non_existing',
    ... )
    Traceback (most recent call last):
        ...
    FileNotFoundError: subkey not found, ...
    """
    current_fake_reg_key = fake_reg_key
    if sub_key:
        key_parts = sub_key.split("\\")
        for key_part in key_parts:
            try:
                current_fake_reg_key = current_fake_reg_key.subkeys[key_part]
            except KeyError:
                raise FileNotFoundError(f'subkey not found, key="{current_fake_reg_key.full_key}", subkey="{key_part}"')
    return current_fake_reg_key


def set_fake_reg_value(
    fake_reg_key: FakeRegistryKey,
    *,
    sub_key: str,
    value_name: str,
    value: bytes | str | list[str] | int | None,
    value_type: int = REG_SZ,
    last_modified_ns: int | None = None,
) -> FakeRegistryValue:
    r"""Set a registry value, creating parent keys on the fly if needed.

    >>> fake_reg_root = FakeRegistryKey()
    >>> fake_reg_key = set_fake_reg_key(
    ...     fake_reg_key=fake_reg_root,
    ...     sub_key=r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT',
    ... )
    >>> fake_reg_value = set_fake_reg_value(
    ...     fake_reg_key, sub_key='', value_name='CurrentBuild', value='18363', value_type=REG_SZ
    ... )
    >>> assert fake_reg_value.full_key == r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT'
    >>> assert fake_reg_value.value_name == 'CurrentBuild'
    >>> assert fake_reg_value.value == '18363'
    >>> assert fake_reg_value.value_type == REG_SZ
    """
    if last_modified_ns is None:
        last_modified_ns = get_windows_timestamp_now()

    fake_reg_key = set_fake_reg_key(fake_reg_key=fake_reg_key, sub_key=sub_key, last_modified_ns=last_modified_ns)

    fake_reg_value = fake_reg_key.values.get(value_name)
    if fake_reg_value is None:
        # Fill the value in before publishing it: a thread enumerating the key
        # in between would otherwise read a value named "" holding None.
        new_value = FakeRegistryValue()
        new_value.full_key = fake_reg_key.full_key
        new_value.value_name = value_name
        new_value.value = value
        new_value.value_type = value_type
        new_value.last_modified_ns = last_modified_ns
        fake_reg_value = fake_reg_key.values.get_or_add(value_name, new_value)
        if fake_reg_value is new_value:
            return new_value
    # An existing value (or one a racing writer stored first) is updated in
    # place, so a caller holding it sees the new data: last writer wins.
    fake_reg_value.value = value
    fake_reg_value.value_type = value_type
    fake_reg_value.last_modified_ns = last_modified_ns
    return fake_reg_value


def get_windows_timestamp_now() -> int:
    """Return current time as Windows timestamp (100ns intervals since 1601-01-01).

    >>> assert get_windows_timestamp_now() > 10000
    """
    linux_timestamp_100ns = int(time.time() * 1e7)
    linux_windows_diff_100ns = int(11644473600 * 1e7)
    return linux_timestamp_100ns + linux_windows_diff_100ns


__all__ = [
    "ChildMap",
    "FakeRegistry",
    "FakeRegistryKey",
    "FakeRegistryValue",
    "get_fake_reg_key",
    "get_windows_timestamp_now",
    "set_fake_reg_key",
    "set_fake_reg_value",
]
