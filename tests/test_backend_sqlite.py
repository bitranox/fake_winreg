"""Tests for the SQLite registry backend."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

import pytest

from fake_winreg.adapters.persistence.json_backend import JsonBackend
from fake_winreg.adapters.persistence.sqlite_backend import SqliteBackend
from fake_winreg.domain.constants import (
    HKEY_CURRENT_USER,
    HKEY_LOCAL_MACHINE,
    REG_BINARY,
    REG_DWORD,
    REG_MULTI_SZ,
    REG_NONE,
    REG_SZ,
)
from fake_winreg.domain.memory_backend import InMemoryBackend
from fake_winreg.domain.types import KeyInfo, ValueEntry

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from fake_winreg.application.ports import RegistryBackend
    from fake_winreg.domain.registry import FakeRegistryKey

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_backend(tmp_path: Path) -> SqliteBackend:
    return SqliteBackend(tmp_path / "test_registry.db")


# ---------------------------------------------------------------------------
# Hive tests
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_get_hive_returns_correct_root(tmp_path: Path) -> None:
    with _make_backend(tmp_path) as backend:
        hive = backend.get_hive(HKEY_LOCAL_MACHINE)
        assert hive.full_key == "HKEY_LOCAL_MACHINE"


@pytest.mark.os_agnostic
def test_get_hive_invalid_raises_os_error(tmp_path: Path) -> None:
    with _make_backend(tmp_path) as backend, pytest.raises(OSError, match="WinError 6"):
        backend.get_hive(999999)


# ---------------------------------------------------------------------------
# Key creation and retrieval
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_create_and_get_key(tmp_path: Path) -> None:
    with _make_backend(tmp_path) as backend:
        hive = backend.get_hive(HKEY_LOCAL_MACHINE)
        created = backend.create_key(hive, r"SOFTWARE\Microsoft\Windows")
        assert created.full_key == r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows"

        fetched = backend.get_key(hive, r"SOFTWARE\Microsoft\Windows")
        assert fetched.full_key == created.full_key


@pytest.mark.os_agnostic
def test_create_key_with_none_sub_key(tmp_path: Path) -> None:
    with _make_backend(tmp_path) as backend:
        hive = backend.get_hive(HKEY_CURRENT_USER)
        result = backend.create_key(hive, None)
        assert result.full_key == "HKEY_CURRENT_USER"


@pytest.mark.os_agnostic
def test_create_key_intermediate_parents(tmp_path: Path) -> None:
    with _make_backend(tmp_path) as backend:
        hive = backend.get_hive(HKEY_LOCAL_MACHINE)
        backend.create_key(hive, r"A\B\C")

        # Intermediate keys must also exist
        mid = backend.get_key(hive, "A")
        assert mid.full_key == r"HKEY_LOCAL_MACHINE\A"

        mid_b = backend.get_key(hive, r"A\B")
        assert mid_b.full_key == r"HKEY_LOCAL_MACHINE\A\B"


@pytest.mark.os_agnostic
def test_get_key_not_found_raises(tmp_path: Path) -> None:
    with _make_backend(tmp_path) as backend:
        hive = backend.get_hive(HKEY_LOCAL_MACHINE)
        with pytest.raises(FileNotFoundError, match="WinError 2"):
            backend.get_key(hive, "NonExistent")


# ---------------------------------------------------------------------------
# Key deletion
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_delete_leaf_key(tmp_path: Path) -> None:
    with _make_backend(tmp_path) as backend:
        hive = backend.get_hive(HKEY_LOCAL_MACHINE)
        backend.create_key(hive, r"A\B")

        key_a = backend.get_key(hive, "A")
        backend.delete_key(key_a, "B")

        with pytest.raises(FileNotFoundError):
            backend.get_key(hive, r"A\B")


@pytest.mark.os_agnostic
def test_delete_key_with_children_raises(tmp_path: Path) -> None:
    with _make_backend(tmp_path) as backend:
        hive = backend.get_hive(HKEY_LOCAL_MACHINE)
        backend.create_key(hive, r"A\B")

        with pytest.raises(PermissionError, match="WinError 5"):
            backend.delete_key(hive, "A")


@pytest.mark.os_agnostic
def test_delete_nonexistent_key_raises(tmp_path: Path) -> None:
    with _make_backend(tmp_path) as backend:
        hive = backend.get_hive(HKEY_LOCAL_MACHINE)
        with pytest.raises(FileNotFoundError, match="WinError 2"):
            backend.delete_key(hive, "Ghost")


@pytest.mark.os_agnostic
def test_delete_key_removes_associated_values(tmp_path: Path) -> None:
    with _make_backend(tmp_path) as backend:
        hive = backend.get_hive(HKEY_LOCAL_MACHINE)
        key = backend.create_key(hive, "Leaf")
        backend.set_value(key, "val", "data", REG_SZ)

        backend.delete_key(hive, "Leaf")

        # Recreate the key and verify value is gone
        key2 = backend.create_key(hive, "Leaf")
        assert backend.enum_values(key2) == []


# ---------------------------------------------------------------------------
# Values: set, get, delete
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_set_and_get_string_value(tmp_path: Path) -> None:
    with _make_backend(tmp_path) as backend:
        hive = backend.get_hive(HKEY_LOCAL_MACHINE)
        key = backend.create_key(hive, "TestKey")
        backend.set_value(key, "Name", "hello", REG_SZ)

        val = backend.get_value(key, "Name")
        assert val.value == "hello"
        assert val.value_type == REG_SZ
        assert val.value_name == "Name"
        assert val.full_key == key.full_key


@pytest.mark.os_agnostic
def test_set_and_get_int_value(tmp_path: Path) -> None:
    with _make_backend(tmp_path) as backend:
        hive = backend.get_hive(HKEY_LOCAL_MACHINE)
        key = backend.create_key(hive, "TestKey")
        backend.set_value(key, "Count", 42, REG_DWORD)

        val = backend.get_value(key, "Count")
        assert val.value == 42
        assert val.value_type == REG_DWORD


@pytest.mark.os_agnostic
def test_set_and_get_bytes_value(tmp_path: Path) -> None:
    with _make_backend(tmp_path) as backend:
        hive = backend.get_hive(HKEY_LOCAL_MACHINE)
        key = backend.create_key(hive, "TestKey")
        raw = b"\x00\x01\x02\xff"
        backend.set_value(key, "Binary", raw, REG_BINARY)

        val = backend.get_value(key, "Binary")
        assert val.value == raw
        assert val.value_type == REG_BINARY


@pytest.mark.os_agnostic
def test_set_and_get_multi_string_value(tmp_path: Path) -> None:
    with _make_backend(tmp_path) as backend:
        hive = backend.get_hive(HKEY_LOCAL_MACHINE)
        key = backend.create_key(hive, "TestKey")
        multi = ["alpha", "beta", "gamma"]
        backend.set_value(key, "List", multi, REG_MULTI_SZ)

        val = backend.get_value(key, "List")
        assert val.value == multi
        assert val.value_type == REG_MULTI_SZ


@pytest.mark.os_agnostic
def test_set_and_get_none_value(tmp_path: Path) -> None:
    with _make_backend(tmp_path) as backend:
        hive = backend.get_hive(HKEY_LOCAL_MACHINE)
        key = backend.create_key(hive, "TestKey")
        backend.set_value(key, "Empty", None, REG_NONE)

        val = backend.get_value(key, "Empty")
        assert val.value is None
        assert val.value_type == REG_NONE


@pytest.mark.os_agnostic
def test_get_value_not_found_raises(tmp_path: Path) -> None:
    with _make_backend(tmp_path) as backend:
        hive = backend.get_hive(HKEY_LOCAL_MACHINE)
        key = backend.create_key(hive, "TestKey")
        with pytest.raises(FileNotFoundError, match="WinError 2"):
            backend.get_value(key, "Missing")


@pytest.mark.os_agnostic
def test_delete_value(tmp_path: Path) -> None:
    with _make_backend(tmp_path) as backend:
        hive = backend.get_hive(HKEY_LOCAL_MACHINE)
        key = backend.create_key(hive, "TestKey")
        backend.set_value(key, "ToDelete", "bye", REG_SZ)
        backend.delete_value(key, "ToDelete")

        with pytest.raises(FileNotFoundError):
            backend.get_value(key, "ToDelete")


@pytest.mark.os_agnostic
def test_delete_value_not_found_raises(tmp_path: Path) -> None:
    with _make_backend(tmp_path) as backend:
        hive = backend.get_hive(HKEY_LOCAL_MACHINE)
        key = backend.create_key(hive, "TestKey")
        with pytest.raises(FileNotFoundError, match="WinError 2"):
            backend.delete_value(key, "Ghost")


@pytest.mark.os_agnostic
def test_set_value_overwrite(tmp_path: Path) -> None:
    with _make_backend(tmp_path) as backend:
        hive = backend.get_hive(HKEY_LOCAL_MACHINE)
        key = backend.create_key(hive, "TestKey")
        backend.set_value(key, "Version", "1.0", REG_SZ)
        backend.set_value(key, "Version", "2.0", REG_SZ)

        val = backend.get_value(key, "Version")
        assert val.value == "2.0"


# ---------------------------------------------------------------------------
# Enumeration
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_enum_keys(tmp_path: Path) -> None:
    with _make_backend(tmp_path) as backend:
        hive = backend.get_hive(HKEY_LOCAL_MACHINE)
        backend.create_key(hive, "Alpha")
        backend.create_key(hive, "Beta")
        backend.create_key(hive, "Gamma")

        names = backend.enum_keys(hive)
        assert sorted(names) == ["Alpha", "Beta", "Gamma"]


@pytest.mark.os_agnostic
def test_enum_keys_empty(tmp_path: Path) -> None:
    with _make_backend(tmp_path) as backend:
        hive = backend.get_hive(HKEY_LOCAL_MACHINE)
        key = backend.create_key(hive, "Leaf")
        assert backend.enum_keys(key) == []


@pytest.mark.os_agnostic
def test_enum_values(tmp_path: Path) -> None:
    with _make_backend(tmp_path) as backend:
        hive = backend.get_hive(HKEY_LOCAL_MACHINE)
        key = backend.create_key(hive, "TestKey")
        backend.set_value(key, "A", "alpha", REG_SZ)
        backend.set_value(key, "B", 99, REG_DWORD)

        values = backend.enum_values(key)
        names = [v[0] for v in values]
        assert sorted(names) == ["A", "B"]
        value_dict = {v[0]: (v[1], v[2]) for v in values}
        assert value_dict["A"] == ("alpha", REG_SZ)
        assert value_dict["B"] == (99, REG_DWORD)


@pytest.mark.os_agnostic
def test_enum_values_empty(tmp_path: Path) -> None:
    with _make_backend(tmp_path) as backend:
        hive = backend.get_hive(HKEY_LOCAL_MACHINE)
        key = backend.create_key(hive, "EmptyKey")
        assert backend.enum_values(key) == []


# ---------------------------------------------------------------------------
# Query info
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_query_info(tmp_path: Path) -> None:
    with _make_backend(tmp_path) as backend:
        hive = backend.get_hive(HKEY_LOCAL_MACHINE)
        key = backend.create_key(hive, "InfoKey")
        backend.create_key(key, "Child1")
        backend.create_key(key, "Child2")
        backend.set_value(key, "Val1", "x", REG_SZ)

        num_subkeys, num_values, last_modified_ns = backend.query_info(key)
        assert num_subkeys == 2
        assert num_values == 1
        assert last_modified_ns > 0


# ---------------------------------------------------------------------------
# Round-trip / persistence
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_round_trip_persistence(tmp_path: Path) -> None:
    """Build a registry in one session, reopen the file, verify content."""
    db_path = tmp_path / "roundtrip.db"

    # Session 1: populate
    with SqliteBackend(db_path) as backend:
        hive = backend.get_hive(HKEY_CURRENT_USER)
        key = backend.create_key(hive, r"Software\TestApp")
        backend.set_value(key, "Version", "3.1", REG_SZ)
        backend.set_value(key, "Count", 7, REG_DWORD)
        backend.set_value(key, "Payload", b"\xde\xad", REG_BINARY)
        backend.set_value(key, "Tags", ["a", "b"], REG_MULTI_SZ)
        backend.set_value(key, "Nil", None, REG_NONE)

    # Session 2: verify
    with SqliteBackend(db_path) as backend:
        hive = backend.get_hive(HKEY_CURRENT_USER)
        key = backend.get_key(hive, r"Software\TestApp")

        assert backend.get_value(key, "Version").value == "3.1"
        assert backend.get_value(key, "Count").value == 7
        assert backend.get_value(key, "Payload").value == b"\xde\xad"
        assert backend.get_value(key, "Tags").value == ["a", "b"]
        assert backend.get_value(key, "Nil").value is None

        subkeys = backend.enum_keys(hive)
        assert "Software" in subkeys

        num_sub, num_val, _ = backend.query_info(key)
        assert num_sub == 0
        assert num_val == 5


# ---------------------------------------------------------------------------
# Context manager
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_context_manager(tmp_path: Path) -> None:
    with SqliteBackend(tmp_path / "ctx.db") as backend:
        hive = backend.get_hive(HKEY_LOCAL_MACHINE)
        assert hive.full_key == "HKEY_LOCAL_MACHINE"
    # After close, operations should fail
    with pytest.raises((OSError, Exception)):
        backend.get_hive(HKEY_LOCAL_MACHINE)


# ---------------------------------------------------------------------------
# Positional access and typed records
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_enum_values_and_query_info_return_named_records(tmp_path: Path) -> None:
    with _make_backend(tmp_path) as backend:
        key = backend.create_key(backend.get_hive(HKEY_CURRENT_USER), r"Software\Rec")
        backend.set_value(key, "B", 2, REG_DWORD)
        backend.set_value(key, "A", "x", REG_SZ)
        backend.create_key(key, "Child")
        assert backend.enum_values(key) == [
            ValueEntry(name="A", data="x", value_type=REG_SZ),
            ValueEntry(name="B", data=2, value_type=REG_DWORD),
        ]
        info = backend.query_info(key)
        assert (info.subkey_count, info.value_count) == (1, 2)
        assert isinstance(info, KeyInfo)


@pytest.mark.os_agnostic
def test_subkey_name_at_follows_enum_keys_order(tmp_path: Path) -> None:
    with _make_backend(tmp_path) as backend:
        key = backend.create_key(backend.get_hive(HKEY_CURRENT_USER), r"Software\Pos")
        for name in ("Gamma", "Alpha", "Beta"):
            backend.create_key(key, name)
        names = backend.enum_keys(key)
        assert [backend.subkey_name_at(key, i) for i in range(len(names))] == names
        with pytest.raises(IndexError):
            backend.subkey_name_at(key, len(names))
        # List rules: a negative index counts from the end. SQLite reads a negative
        # OFFSET as 0, so an unresolved -1 would hand back the first row instead.
        assert backend.subkey_name_at(key, -1) == names[-1]
        assert backend.subkey_name_at(key, -len(names)) == names[0]
        with pytest.raises(IndexError):
            backend.subkey_name_at(key, -(len(names) + 1))


@pytest.mark.os_agnostic
def test_value_at_follows_enum_values_order(tmp_path: Path) -> None:
    with _make_backend(tmp_path) as backend:
        key = backend.create_key(backend.get_hive(HKEY_CURRENT_USER), r"Software\PosV")
        backend.set_value(key, "z", b"\x01", REG_BINARY)
        backend.set_value(key, "", "default", REG_SZ)
        backend.set_value(key, "m", ["a"], REG_MULTI_SZ)
        entries = backend.enum_values(key)
        assert [backend.value_at(key, i) for i in range(len(entries))] == entries
        with pytest.raises(IndexError):
            backend.value_at(key, len(entries))
        assert backend.value_at(key, -1) == entries[-1]
        assert backend.value_at(key, -len(entries)) == entries[0]
        with pytest.raises(IndexError):
            backend.value_at(key, -(len(entries) + 1))


def _positional_reads(backend: RegistryBackend, key: FakeRegistryKey, count: int) -> list[object]:
    """Read subkey names and values at the boundary indexes, recording IndexError as a result."""
    indexes = (0, count - 1, -1, -count, count, -(count + 1))
    return [
        _read_or_index_error(read, key, index)
        for index in indexes
        for read in (backend.subkey_name_at, backend.value_at)
    ]


def _read_or_index_error(read: Callable[[FakeRegistryKey, int], object], key: FakeRegistryKey, index: int) -> object:
    try:
        return read(key, index)
    except IndexError:
        return IndexError


@pytest.mark.os_agnostic
def test_positional_reads_agree_across_memory_json_and_sqlite(tmp_path: Path) -> None:
    """EnumKey/EnumValue index the same way whatever backend holds the registry."""
    names = ("Alpha", "Beta", "Gamma")
    results: dict[str, list[object]] = {}
    sqlite_backend = SqliteBackend(tmp_path / "pos.db")
    backends: dict[str, RegistryBackend] = {
        "memory": InMemoryBackend(),
        "json": JsonBackend(tmp_path / "pos.json"),
        "sqlite": sqlite_backend,
    }
    try:
        for label, backend in backends.items():
            key = backend.create_key(backend.get_hive(HKEY_CURRENT_USER), r"Software\Pos")
            # Inserted in sorted order, so insertion order (memory, json) equals SQLite's name order.
            for name in names:
                backend.create_key(key, name)
                backend.set_value(key, name.lower(), name, REG_SZ)
            results[label] = _positional_reads(backend, key, len(names))
    finally:
        sqlite_backend.close()
    assert results["memory"][:4] == [
        "Alpha",
        ValueEntry("alpha", "Alpha", REG_SZ),
        "Gamma",
        ValueEntry("gamma", "Gamma", REG_SZ),
    ]
    assert results["json"] == results["memory"]
    assert results["sqlite"] == results["memory"]


# ---------------------------------------------------------------------------
# Schema: parent_path index
# ---------------------------------------------------------------------------


def _child_lookup_plan(db_path: Path) -> str:
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            "EXPLAIN QUERY PLAN SELECT full_path FROM registry_keys WHERE parent_path = ? ORDER BY full_path",
            ("HKEY_CURRENT_USER",),
        ).fetchall()
    finally:
        conn.close()
    return " ".join(str(row[-1]) for row in rows)


@pytest.mark.os_agnostic
def test_child_lookups_use_the_parent_path_index(tmp_path: Path) -> None:
    db_path = tmp_path / "idx.db"
    SqliteBackend(db_path).close()
    assert "ix_registry_keys_parent_path" in _child_lookup_plan(db_path)


@pytest.mark.os_agnostic
def test_database_created_without_the_index_gets_it_on_open(tmp_path: Path) -> None:
    db_path = tmp_path / "old.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "CREATE TABLE registry_keys (full_path TEXT PRIMARY KEY, hive_name TEXT NOT NULL, "
        "parent_path TEXT, last_modified_ns INTEGER NOT NULL DEFAULT 0)"
    )
    conn.commit()
    conn.close()
    assert "ix_registry_keys_parent_path" not in _child_lookup_plan(db_path)
    SqliteBackend(db_path).close()
    assert "ix_registry_keys_parent_path" in _child_lookup_plan(db_path)


# ---------------------------------------------------------------------------
# bulk(): one transaction for many writes
# ---------------------------------------------------------------------------


def _committed_key_paths(db_path: Path) -> set[str]:
    """Read what another connection sees, i.e. only committed rows."""
    conn = sqlite3.connect(str(db_path))
    try:
        return {row[0] for row in conn.execute("SELECT full_path FROM registry_keys WHERE parent_path IS NOT NULL")}
    finally:
        conn.close()


@pytest.mark.os_agnostic
def test_single_writes_commit_immediately(tmp_path: Path) -> None:
    db_path = tmp_path / "auto.db"
    with SqliteBackend(db_path) as backend:
        backend.create_key(backend.get_hive(HKEY_CURRENT_USER), "Auto")
        assert _committed_key_paths(db_path) == {r"HKEY_CURRENT_USER\Auto"}


@pytest.mark.os_agnostic
def test_bulk_commits_once_at_the_end(tmp_path: Path) -> None:
    db_path = tmp_path / "bulk.db"
    with SqliteBackend(db_path) as backend:
        hive = backend.get_hive(HKEY_CURRENT_USER)
        with backend.bulk():
            key = backend.create_key(hive, "Bulk")
            backend.set_value(key, "v", 1, REG_DWORD)
            assert _committed_key_paths(db_path) == set()
        assert _committed_key_paths(db_path) == {r"HKEY_CURRENT_USER\Bulk"}
        assert backend.get_value(key, "v").value == 1
        # Autocommit resumes after the block.
        backend.create_key(hive, "After")
        assert r"HKEY_CURRENT_USER\After" in _committed_key_paths(db_path)


@pytest.mark.os_agnostic
def test_bulk_rolls_back_when_the_block_raises(tmp_path: Path) -> None:
    db_path = tmp_path / "rollback.db"
    with SqliteBackend(db_path) as backend:
        hive = backend.get_hive(HKEY_CURRENT_USER)
        with pytest.raises(RuntimeError, match="boom"), backend.bulk():
            backend.create_key(hive, "Gone")
            raise RuntimeError("boom")
        assert backend.enum_keys(hive) == []
        backend.create_key(hive, "Kept")
        assert _committed_key_paths(db_path) == {r"HKEY_CURRENT_USER\Kept"}


@pytest.mark.os_agnostic
def test_nested_bulk_commits_only_with_the_outer_block(tmp_path: Path) -> None:
    db_path = tmp_path / "nested.db"
    with SqliteBackend(db_path) as backend:
        hive = backend.get_hive(HKEY_CURRENT_USER)
        with backend.bulk():
            with backend.bulk():
                backend.create_key(hive, "Inner")
            assert _committed_key_paths(db_path) == set()
            backend.create_key(hive, "Outer")
        assert _committed_key_paths(db_path) == {r"HKEY_CURRENT_USER\Inner", r"HKEY_CURRENT_USER\Outer"}


@pytest.mark.os_agnostic
def test_failed_inner_bulk_undoes_only_its_own_writes(tmp_path: Path) -> None:
    db_path = tmp_path / "inner_fail.db"
    with SqliteBackend(db_path) as backend:
        hive = backend.get_hive(HKEY_CURRENT_USER)
        with backend.bulk():
            backend.create_key(hive, "Before")
            with pytest.raises(RuntimeError), backend.bulk():
                backend.create_key(hive, "Inner")
                raise RuntimeError("inner")
            backend.create_key(hive, "AfterInner")
        assert _committed_key_paths(db_path) == {r"HKEY_CURRENT_USER\Before", r"HKEY_CURRENT_USER\AfterInner"}


@pytest.mark.os_agnostic
def test_failed_outer_bulk_undoes_a_finished_inner_block(tmp_path: Path) -> None:
    db_path = tmp_path / "outer_fail.db"
    with SqliteBackend(db_path) as backend:
        hive = backend.get_hive(HKEY_CURRENT_USER)
        with pytest.raises(RuntimeError), backend.bulk():
            with backend.bulk():
                backend.create_key(hive, "Inner")
            raise RuntimeError("outer")
        assert _committed_key_paths(db_path) == set()


def _limit_database_growth(monkeypatch: pytest.MonkeyPatch, *, extra_pages: int) -> None:
    """Make every new SQLite connection refuse to grow its file past *extra_pages* more pages.

    ``PRAGMA max_page_count`` is per connection, and SqliteBackend opens its own,
    so the stdlib's connect is the only place to set it. A write past the limit
    fails with SQLITE_FULL, which makes SQLite roll back the whole transaction.
    """
    real_connect = sqlite3.connect

    def connect(database: str) -> sqlite3.Connection:
        conn = real_connect(database)
        pages = conn.execute("PRAGMA page_count").fetchone()[0]
        conn.execute(f"PRAGMA max_page_count = {pages + extra_pages}")
        return conn

    monkeypatch.setattr(sqlite3, "connect", connect)


def _fill_until_full(backend: SqliteBackend, key: FakeRegistryKey) -> None:
    """Create keys until the page limit is hit.

    Keys, not values: a failing INSERT OR REPLACE of a value is undone on its own
    (SQLite keeps a statement journal for it), while a failing key insert makes
    SQLite roll back the whole transaction, the case under test.
    """
    for index in range(3000):
        backend.create_key(key, f"k{index:04d}")


_ABORTED = "rolled back by SQLite"


@pytest.mark.os_agnostic
def test_a_transaction_sqlite_rolled_back_is_never_committed_in_part(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """SQLITE_FULL rolls back the whole transaction; nothing written after it may commit."""
    db_path = tmp_path / "full.db"
    SqliteBackend(db_path).close()
    _limit_database_growth(monkeypatch, extra_pages=2)
    with SqliteBackend(db_path) as backend:
        hive = backend.get_hive(HKEY_CURRENT_USER)
        with pytest.raises(sqlite3.OperationalError, match=_ABORTED), backend.bulk():
            outer = backend.create_key(hive, "Outer")
            with pytest.raises(sqlite3.OperationalError, match="full"), backend.bulk():
                _fill_until_full(backend, outer)
            with pytest.raises(sqlite3.OperationalError, match=_ABORTED):
                backend.create_key(hive, "AfterFull")
            entered: list[bool] = []
            with pytest.raises(sqlite3.OperationalError, match=_ABORTED), backend.bulk():
                entered.append(True)
            assert entered == []  # refused on entry, before its SAVEPOINT could open a new transaction
        assert backend.enum_keys(hive) == []
        assert _committed_key_paths(db_path) == set()
        with backend.bulk():
            pass


@pytest.mark.os_agnostic
def test_a_failed_statement_sqlite_undoes_alone_leaves_the_outer_block_committing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A full database on a value write keeps the transaction, so only the inner block is undone."""
    db_path = tmp_path / "full_statement.db"
    SqliteBackend(db_path).close()
    _limit_database_growth(monkeypatch, extra_pages=2)
    with SqliteBackend(db_path) as backend:
        hive = backend.get_hive(HKEY_CURRENT_USER)
        with backend.bulk():
            outer = backend.create_key(hive, "Outer")
            with pytest.raises(sqlite3.OperationalError, match="full"), backend.bulk():
                for index in range(500):
                    backend.set_value(outer, f"v{index:04d}", "x" * 500, REG_SZ)
        assert _committed_key_paths(db_path) == {r"HKEY_CURRENT_USER\Outer"}
        assert backend.enum_values(outer) == []


@pytest.mark.os_agnostic
def test_a_full_database_caught_inside_one_block_still_refuses_later_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db_path = tmp_path / "full_same_block.db"
    SqliteBackend(db_path).close()
    _limit_database_growth(monkeypatch, extra_pages=2)
    with SqliteBackend(db_path) as backend:
        hive = backend.get_hive(HKEY_CURRENT_USER)
        with pytest.raises(sqlite3.OperationalError, match=_ABORTED), backend.bulk():
            outer = backend.create_key(hive, "Outer")
            with pytest.raises(sqlite3.OperationalError, match="full"):
                _fill_until_full(backend, outer)
            with pytest.raises(sqlite3.OperationalError, match=_ABORTED):
                backend.set_value(outer, "late", "x", REG_SZ)
        assert _committed_key_paths(db_path) == set()


# ---------------------------------------------------------------------------
# Stored value text
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_stored_value_text_is_unchanged(tmp_path: Path) -> None:
    """Existing databases keep reading the same: pin the JSON text in the data column."""
    db_path = tmp_path / "text.db"
    with SqliteBackend(db_path) as backend:
        key = backend.create_key(backend.get_hive(HKEY_CURRENT_USER), "Text")
        backend.set_value(key, "b", b"\x00\xff", REG_BINARY)
        backend.set_value(key, "s", "caf" + chr(0xE9), REG_SZ)
        backend.set_value(key, "m", ["a", "b"], REG_MULTI_SZ)
        backend.set_value(key, "n", None, REG_NONE)
    conn = sqlite3.connect(str(db_path))
    try:
        stored = dict(conn.execute("SELECT value_name, data FROM registry_values").fetchall())
    finally:
        conn.close()
    assert stored == {"b": '{"_base64":"AP8="}', "s": '"caf' + chr(0xE9) + '"', "m": '["a","b"]', "n": None}
