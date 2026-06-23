"""Tests for the SQLite registry backend."""

from __future__ import annotations

from pathlib import Path

import pytest

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
