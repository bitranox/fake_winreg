"""Tests for the JSON backend and JSON import/export functions."""

from __future__ import annotations

from pathlib import Path

import orjson
import pytest

from fake_winreg.adapters.persistence.json_backend import JsonBackend
from fake_winreg.adapters.persistence.json_io import export_json, import_json
from fake_winreg.domain.api import _get_backend, use_backend  # pyright: ignore[reportPrivateUsage]
from fake_winreg.domain.constants import HKEY_LOCAL_MACHINE, HKEY_USERS, REG_EXPAND_SZ, REG_SZ
from fake_winreg.domain.memory_backend import InMemoryBackend
from fake_winreg.domain.serialization import registry_to_dict
from fake_winreg.domain.test_registries import get_minimal_windows_testregistry

# ---------------------------------------------------------------------------
# JsonBackend tests
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
class TestJsonBackendLoad:
    """Loading registry data from JSON files."""

    def test_nonexistent_file_creates_empty_registry(self, tmp_path: Path) -> None:
        json_path = tmp_path / "nonexistent.json"
        backend = JsonBackend(json_path)
        hive = backend.get_hive(HKEY_LOCAL_MACHINE)
        assert hive.full_key == "HKEY_LOCAL_MACHINE"
        assert backend.enum_keys(hive) == []

    def test_empty_file_creates_empty_registry(self, tmp_path: Path) -> None:
        json_path = tmp_path / "empty.json"
        json_path.write_bytes(b"")
        backend = JsonBackend(json_path)
        hive = backend.get_hive(HKEY_LOCAL_MACHINE)
        assert backend.enum_keys(hive) == []

    def test_load_populated_registry(self, tmp_path: Path) -> None:
        registry = get_minimal_windows_testregistry()
        data = registry_to_dict(registry)
        json_path = tmp_path / "populated.json"
        json_path.write_bytes(orjson.dumps(data))

        backend = JsonBackend(json_path)
        hive = backend.get_hive(HKEY_LOCAL_MACHINE)
        subkeys = backend.enum_keys(hive)
        assert "SOFTWARE" in subkeys

    def test_load_keys_and_values(self, tmp_path: Path) -> None:
        registry = get_minimal_windows_testregistry()
        data = registry_to_dict(registry)
        json_path = tmp_path / "full.json"
        json_path.write_bytes(orjson.dumps(data))

        backend = JsonBackend(json_path)
        hive = backend.get_hive(HKEY_LOCAL_MACHINE)
        cv_key = backend.get_key(hive, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
        values = backend.enum_values(cv_key)
        value_names = [v[0] for v in values]
        assert "CurrentBuild" in value_names


@pytest.mark.os_agnostic
class TestJsonBackendSave:
    """Saving and reloading registry data."""

    def test_save_creates_file(self, tmp_path: Path) -> None:
        json_path = tmp_path / "save_test.json"
        backend = JsonBackend(json_path)
        backend.save()
        assert json_path.exists()
        data = orjson.loads(json_path.read_bytes())
        assert "hives" in data

    def test_modify_and_save_persists_changes(self, tmp_path: Path) -> None:
        json_path = tmp_path / "modify.json"
        backend = JsonBackend(json_path)
        hive = backend.get_hive(HKEY_LOCAL_MACHINE)
        new_key = backend.create_key(hive, r"SOFTWARE\TestKey")
        backend.set_value(new_key, "TestValue", "hello", REG_SZ)
        backend.save()

        backend2 = JsonBackend(json_path)
        hive2 = backend2.get_hive(HKEY_LOCAL_MACHINE)
        reloaded_key = backend2.get_key(hive2, r"SOFTWARE\TestKey")
        fval = backend2.get_value(reloaded_key, "TestValue")
        assert fval.value == "hello"
        assert fval.value_type == REG_SZ

    def test_delete_key_and_save(self, tmp_path: Path) -> None:
        json_path = tmp_path / "delete.json"
        backend = JsonBackend(json_path)
        hive = backend.get_hive(HKEY_LOCAL_MACHINE)
        backend.create_key(hive, r"SOFTWARE\ToDelete")
        backend.save()

        backend2 = JsonBackend(json_path)
        hive2 = backend2.get_hive(HKEY_LOCAL_MACHINE)
        sw_key = backend2.get_key(hive2, "SOFTWARE")
        backend2.delete_key(sw_key, "ToDelete")
        backend2.save()

        backend3 = JsonBackend(json_path)
        hive3 = backend3.get_hive(HKEY_LOCAL_MACHINE)
        sw_key3 = backend3.get_key(hive3, "SOFTWARE")
        assert "ToDelete" not in backend3.enum_keys(sw_key3)

    def test_save_creates_parent_directories(self, tmp_path: Path) -> None:
        json_path = tmp_path / "nested" / "dirs" / "registry.json"
        backend = JsonBackend(json_path)
        backend.save()
        assert json_path.exists()


@pytest.mark.os_agnostic
class TestJsonBackendDelegation:
    """All backend methods delegate correctly."""

    def test_query_info(self, tmp_path: Path) -> None:
        json_path = tmp_path / "info.json"
        backend = JsonBackend(json_path)
        hive = backend.get_hive(HKEY_LOCAL_MACHINE)
        backend.create_key(hive, "TestSub")
        num_subkeys, num_values, _ = backend.query_info(hive)
        assert num_subkeys == 1
        assert num_values == 0

    def test_delete_value(self, tmp_path: Path) -> None:
        json_path = tmp_path / "delval.json"
        backend = JsonBackend(json_path)
        hive = backend.get_hive(HKEY_LOCAL_MACHINE)
        key = backend.create_key(hive, "TestKey")
        backend.set_value(key, "val", "data", REG_SZ)
        assert len(backend.enum_values(key)) == 1
        backend.delete_value(key, "val")
        assert len(backend.enum_values(key)) == 0

    def test_get_key_missing_raises(self, tmp_path: Path) -> None:
        json_path = tmp_path / "missing.json"
        backend = JsonBackend(json_path)
        hive = backend.get_hive(HKEY_LOCAL_MACHINE)
        with pytest.raises(FileNotFoundError):
            backend.get_key(hive, "NoSuchKey")


# ---------------------------------------------------------------------------
# import_json / export_json tests
# ---------------------------------------------------------------------------


@pytest.fixture()
def _fresh_memory_backend():  # pyright: ignore[reportUnusedFunction]
    """Install a fresh InMemoryBackend and restore after the test."""
    original = _get_backend()
    use_backend(InMemoryBackend())  # type: ignore[arg-type]
    yield
    use_backend(original)  # type: ignore[arg-type]


@pytest.mark.os_agnostic
@pytest.mark.usefixtures("_fresh_memory_backend")
class TestJsonImportExport:
    """Tests for import_json and export_json functions."""

    def test_export_creates_valid_json(self, tmp_path: Path) -> None:
        json_path = tmp_path / "export.json"
        export_json(json_path)
        data = orjson.loads(json_path.read_bytes())
        assert "hives" in data

    def test_export_import_roundtrip(self, tmp_path: Path) -> None:
        backend = _get_backend()
        hive = backend.get_hive(HKEY_LOCAL_MACHINE)
        key = backend.create_key(hive, r"SOFTWARE\RoundTrip")
        backend.set_value(key, "Name", "test_value", REG_SZ)

        export_path = tmp_path / "roundtrip.json"
        export_json(export_path)

        use_backend(InMemoryBackend())  # type: ignore[arg-type]
        import_json(export_path)

        backend2 = _get_backend()
        hive2 = backend2.get_hive(HKEY_LOCAL_MACHINE)
        reloaded = backend2.get_key(hive2, r"SOFTWARE\RoundTrip")
        fval = backend2.get_value(reloaded, "Name")
        assert fval.value == "test_value"
        assert fval.value_type == REG_SZ

    def test_import_from_test_registry(self, tmp_path: Path) -> None:
        registry = get_minimal_windows_testregistry()
        data = registry_to_dict(registry)
        json_path = tmp_path / "testregistry.json"
        json_path.write_bytes(orjson.dumps(data))

        use_backend(InMemoryBackend())  # type: ignore[arg-type]
        import_json(json_path)

        backend = _get_backend()
        hive = backend.get_hive(HKEY_LOCAL_MACHINE)
        cv_key = backend.get_key(hive, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
        fval = backend.get_value(cv_key, "CurrentBuild")
        assert fval.value == "18363"

    def test_roundtrip_minimal_windows_testregistry(self, tmp_path: Path) -> None:
        """Full round-trip: test registry -> export -> import -> verify."""
        registry = get_minimal_windows_testregistry()
        use_backend(InMemoryBackend(registry))  # type: ignore[arg-type]

        export_path = tmp_path / "full_roundtrip.json"
        export_json(export_path)

        use_backend(InMemoryBackend())  # type: ignore[arg-type]
        import_json(export_path)

        backend = _get_backend()

        hive_lm = backend.get_hive(HKEY_LOCAL_MACHINE)
        cv_key = backend.get_key(hive_lm, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
        fval = backend.get_value(cv_key, "CurrentBuild")
        assert fval.value == "18363"

        profile_key = backend.get_key(
            hive_lm,
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList\S-1-5-21-206651429-2786145735-121611483-1001",
        )
        fval_profile = backend.get_value(profile_key, "ProfileImagePath")
        assert fval_profile.value == r"C:\Users\bitranox"
        assert fval_profile.value_type == REG_EXPAND_SZ

        hive_users = backend.get_hive(HKEY_USERS)
        vol_key = backend.get_key(hive_users, r"S-1-5-21-206651429-2786145735-121611483-1001\Volatile Environment")
        fval_user = backend.get_value(vol_key, "USERNAME")
        assert fval_user.value == "bitranox"

    def test_import_empty_hives(self, tmp_path: Path) -> None:
        json_path = tmp_path / "empty_hives.json"
        json_path.write_bytes(orjson.dumps({"hives": {}}))
        import_json(json_path)
        backend = _get_backend()
        hive = backend.get_hive(HKEY_LOCAL_MACHINE)
        assert backend.enum_keys(hive) == []

    def test_export_creates_parent_directories(self, tmp_path: Path) -> None:
        json_path = tmp_path / "deep" / "nested" / "export.json"
        export_json(json_path)
        assert json_path.exists()
