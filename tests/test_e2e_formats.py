# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false, reportUnknownParameterType=false
# pyright: reportMissingParameterType=false
"""End-to-end tests: export → re-import → verify for all formats and conversions.

Tests every combination of source → target format (9 pairs) and verifies
that all registry values survive the round-trip intact.
"""

from __future__ import annotations

import itertools
from pathlib import Path
from typing import Any

import pytest

import fake_winreg as winreg
from fake_winreg.adapters.persistence.convert import convert_registry
from fake_winreg.adapters.persistence.json_io import export_json, import_json
from fake_winreg.adapters.persistence.reg_io import export_reg, import_reg
from fake_winreg.adapters.persistence.sqlite_backend import SqliteBackend
from fake_winreg.domain.constants import (
    HKEY_CURRENT_USER,
    HKEY_LOCAL_MACHINE,
    REG_BINARY,
    REG_DWORD,
    REG_EXPAND_SZ,
    REG_MULTI_SZ,
    REG_QWORD,
    REG_SZ,
)
from fake_winreg.domain.memory_backend import InMemoryBackend
from fake_winreg.domain.test_registries import (
    get_minimal_windows11_testregistry,
    get_minimal_windows_testregistry,
    get_minimal_wine_testregistry,
)

# ---------------------------------------------------------------------------
# Reference values — the "truth" we verify against after every round-trip
# ---------------------------------------------------------------------------

# Key path → [(value_name, expected_data, expected_type), ...]
WINDOWS10_EXPECTED: dict[str, list[tuple[str, Any, int]]] = {
    r"SOFTWARE\Microsoft\Windows NT\CurrentVersion": [
        ("CurrentBuild", "18363", REG_SZ),
    ],
    r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList\S-1-5-18": [
        ("ProfileImagePath", r"%systemroot%\system32\config\systemprofile", REG_EXPAND_SZ),
    ],
    r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList\S-1-5-21-206651429-2786145735-121611483-1001": [
        ("ProfileImagePath", r"C:\Users\bitranox", REG_EXPAND_SZ),
    ],
}

WINDOWS11_EXPECTED: dict[str, list[tuple[str, Any, int]]] = {
    r"SOFTWARE\Microsoft\Windows NT\CurrentVersion": [
        ("CurrentBuild", "22631", REG_SZ),
        ("DisplayVersion", "23H2", REG_SZ),
        ("ProductName", "Windows 10 Pro", REG_SZ),
        ("EditionID", "Professional", REG_SZ),
        ("CurrentMajorVersionNumber", 10, REG_DWORD),
        ("CurrentMinorVersionNumber", 0, REG_DWORD),
        ("UBR", 4317, REG_DWORD),
        ("BuildBranch", "ni_release", REG_SZ),
    ],
}

WINE_EXPECTED: dict[str, list[tuple[str, Any, int]]] = {
    r"Software\Microsoft\Windows NT\CurrentVersion": [
        ("CurrentBuild", "7601", REG_SZ),
    ],
}

# All value types for comprehensive type coverage
ALL_TYPES_KEY = r"Software\E2E_AllTypes"
ALL_TYPES_VALUES: list[tuple[str, Any, int]] = [
    ("StringVal", "hello world", REG_SZ),
    ("ExpandVal", r"%SystemRoot%\System32", REG_EXPAND_SZ),
    ("DwordVal", 42, REG_DWORD),
    ("QwordVal", 2**40, REG_QWORD),
    ("BinaryVal", b"\xde\xad\xbe\xef\xca\xfe", REG_BINARY),
    ("MultiVal", ["alpha", "beta", "gamma"], REG_MULTI_SZ),
    ("EmptyString", "", REG_SZ),
    ("ZeroDword", 0, REG_DWORD),
]

FORMATS = ["db", "json", "reg"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_comprehensive_registry() -> InMemoryBackend:
    """Build a registry with all value types for thorough testing."""
    reg = get_minimal_windows11_testregistry()
    backend = InMemoryBackend(reg)
    winreg.use_backend(backend)  # type: ignore[arg-type]

    hkcu = winreg.ConnectRegistry(None, HKEY_CURRENT_USER)
    key = winreg.CreateKey(hkcu, ALL_TYPES_KEY)
    for vname, vdata, vtype in ALL_TYPES_VALUES:
        winreg.SetValueEx(key, vname, 0, vtype, vdata)

    return backend


def _save_to_format(backend: InMemoryBackend, path: Path, fmt: str) -> None:
    """Save backend state to a file in the given format."""
    winreg.use_backend(backend)  # type: ignore[arg-type]
    if fmt == "json":
        export_json(path)
    elif fmt == "reg":
        export_reg(path)
    elif fmt == "db":
        tgt = SqliteBackend(path)
        _stream_to_sqlite(backend, tgt)
        tgt.close()


def _load_from_format(path: Path, fmt: str) -> InMemoryBackend:
    """Load a file into a fresh InMemoryBackend."""
    if fmt == "db":
        # Read from SQLite, stream into InMemoryBackend
        src = SqliteBackend(path)
        tgt = InMemoryBackend()
        winreg.use_backend(tgt)  # type: ignore[arg-type]
        _stream_from_sqlite(src, tgt)
        src.close()
        return tgt
    else:
        backend = InMemoryBackend()
        winreg.use_backend(backend)  # type: ignore[arg-type]
        if fmt == "json":
            import_json(path)
        elif fmt == "reg":
            import_reg(path)
        return backend


def _stream_to_sqlite(src: InMemoryBackend, tgt: SqliteBackend) -> None:
    """Copy all data from InMemoryBackend to SqliteBackend."""
    from fake_winreg.domain.constants import hive_name_hashed_by_int

    for hive_int in sorted(hive_name_hashed_by_int):
        src_hive = src.get_hive(hive_int)
        tgt_hive = tgt.get_hive(hive_int)
        _copy_recursive(src, tgt, src_hive, tgt_hive)


def _stream_from_sqlite(src: SqliteBackend, tgt: InMemoryBackend) -> None:
    """Copy all data from SqliteBackend to InMemoryBackend."""
    from fake_winreg.domain.constants import hive_name_hashed_by_int

    for hive_int in sorted(hive_name_hashed_by_int):
        src_hive = src.get_hive(hive_int)
        tgt_hive = tgt.get_hive(hive_int)
        _copy_recursive(src, tgt, src_hive, tgt_hive)


def _copy_recursive(src, tgt, src_key, tgt_key) -> None:
    for vname, vdata, vtype in src.enum_values(src_key):
        tgt.set_value(tgt_key, vname, vdata, vtype)
    for sname in src.enum_keys(src_key):
        child_src = src.get_key(src_key, sname)
        child_tgt = tgt.create_key(tgt_key, sname)
        _copy_recursive(src, tgt, child_src, child_tgt)


def _verify_values(
    backend: InMemoryBackend,
    hive_int: int,
    expected: dict[str, list[tuple[str, Any, int]]],
    label: str,
) -> None:
    """Verify expected values exist in the backend."""
    winreg.use_backend(backend)  # type: ignore[arg-type]
    hive = winreg.ConnectRegistry(None, hive_int)

    for sub_path, values in expected.items():
        key = winreg.OpenKey(hive, sub_path)
        for vname, expected_data, expected_type in values:
            actual_data, actual_type = winreg.QueryValueEx(key, vname)
            assert actual_type == expected_type, f"{label}: {sub_path}\\{vname}: type {actual_type} != {expected_type}"
            assert actual_data == expected_data, (
                f"{label}: {sub_path}\\{vname}: data {actual_data!r} != {expected_data!r}"
            )


def _verify_all_types(backend: InMemoryBackend, label: str) -> None:
    """Verify the ALL_TYPES_VALUES survive a round-trip."""
    winreg.use_backend(backend)  # type: ignore[arg-type]
    hkcu = winreg.ConnectRegistry(None, HKEY_CURRENT_USER)
    key = winreg.OpenKey(hkcu, ALL_TYPES_KEY)

    for vname, expected_data, expected_type in ALL_TYPES_VALUES:
        actual_data, actual_type = winreg.QueryValueEx(key, vname)
        assert actual_type == expected_type, f"{label}: {vname}: type {actual_type} != {expected_type}"
        assert actual_data == expected_data, f"{label}: {vname}: data {actual_data!r} != {expected_data!r}"


@pytest.fixture(autouse=True)
def _restore_backend():  # type: ignore[no-untyped-def]  # pyright: ignore[reportUnusedFunction]
    yield
    winreg.use_backend(InMemoryBackend())  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Test 1: Export each test registry to all formats, re-import, verify
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
@pytest.mark.parametrize("fmt", FORMATS, ids=FORMATS)
def test_windows10_roundtrip(tmp_path: Path, fmt: str) -> None:
    """Windows 10 test registry survives export → import in each format."""
    reg = get_minimal_windows_testregistry()
    backend = InMemoryBackend(reg)
    path = tmp_path / f"win10.{fmt}"

    _save_to_format(backend, path, fmt)
    loaded = _load_from_format(path, fmt)
    _verify_values(loaded, HKEY_LOCAL_MACHINE, WINDOWS10_EXPECTED, f"win10-{fmt}")


@pytest.mark.os_agnostic
@pytest.mark.parametrize("fmt", FORMATS, ids=FORMATS)
def test_windows11_roundtrip(tmp_path: Path, fmt: str) -> None:
    """Windows 11 test registry survives export → import in each format."""
    reg = get_minimal_windows11_testregistry()
    backend = InMemoryBackend(reg)
    path = tmp_path / f"win11.{fmt}"

    _save_to_format(backend, path, fmt)
    loaded = _load_from_format(path, fmt)
    _verify_values(loaded, HKEY_LOCAL_MACHINE, WINDOWS11_EXPECTED, f"win11-{fmt}")


@pytest.mark.os_agnostic
@pytest.mark.parametrize("fmt", FORMATS, ids=FORMATS)
def test_wine_roundtrip(tmp_path: Path, fmt: str) -> None:
    """Wine test registry survives export → import in each format."""
    reg = get_minimal_wine_testregistry()
    backend = InMemoryBackend(reg)
    path = tmp_path / f"wine.{fmt}"

    _save_to_format(backend, path, fmt)
    loaded = _load_from_format(path, fmt)
    _verify_values(loaded, HKEY_LOCAL_MACHINE, WINE_EXPECTED, f"wine-{fmt}")


# ---------------------------------------------------------------------------
# Test 2: All value types survive round-trip in each format
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
@pytest.mark.parametrize("fmt", FORMATS, ids=FORMATS)
def test_all_value_types_roundtrip(tmp_path: Path, fmt: str) -> None:
    """Every registry value type survives export → import."""
    backend = _build_comprehensive_registry()
    path = tmp_path / f"alltypes.{fmt}"

    _save_to_format(backend, path, fmt)
    loaded = _load_from_format(path, fmt)
    _verify_all_types(loaded, f"alltypes-{fmt}")


# ---------------------------------------------------------------------------
# Test 3: Full conversion matrix — all 9 source→target format pairs
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
@pytest.mark.parametrize(
    "src_fmt,tgt_fmt",
    list(itertools.product(FORMATS, FORMATS)),
    ids=[f"{s}-to-{t}" for s, t in itertools.product(FORMATS, FORMATS)],
)
def test_conversion_matrix(tmp_path: Path, src_fmt: str, tgt_fmt: str) -> None:
    """Convert between every format pair and verify values survive."""
    backend = _build_comprehensive_registry()

    # Step 1: save to source format
    src_path = tmp_path / f"source.{src_fmt}"
    _save_to_format(backend, src_path, src_fmt)

    # Step 2: convert source → target
    tgt_path = tmp_path / f"target.{tgt_fmt}"
    convert_registry(src_path, tgt_path)

    # Step 3: load target and verify
    loaded = _load_from_format(tgt_path, tgt_fmt)

    # Verify Windows 11 values
    _verify_values(loaded, HKEY_LOCAL_MACHINE, WINDOWS11_EXPECTED, f"{src_fmt}→{tgt_fmt}")

    # Verify all value types
    _verify_all_types(loaded, f"{src_fmt}→{tgt_fmt}")


# ---------------------------------------------------------------------------
# Test 4: Chain conversion — db → reg → json → db and verify
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_chain_conversion(tmp_path: Path) -> None:
    """Values survive a multi-hop conversion chain: db → reg → json → db."""
    backend = _build_comprehensive_registry()

    # db
    db1 = tmp_path / "step1.db"
    _save_to_format(backend, db1, "db")

    # db → reg
    reg_file = tmp_path / "step2.reg"
    convert_registry(db1, reg_file)

    # reg → json
    json_file = tmp_path / "step3.json"
    convert_registry(reg_file, json_file)

    # json → db
    db2 = tmp_path / "step4.db"
    convert_registry(json_file, db2)

    # Verify final result
    loaded = _load_from_format(db2, "db")
    _verify_values(loaded, HKEY_LOCAL_MACHINE, WINDOWS11_EXPECTED, "chain")
    _verify_all_types(loaded, "chain")


# ---------------------------------------------------------------------------
# Test 5: Verify user hive keys survive (HKEY_USERS, HKEY_CURRENT_USER)
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
@pytest.mark.parametrize("fmt", FORMATS, ids=FORMATS)
def test_user_hive_roundtrip(tmp_path: Path, fmt: str) -> None:
    """HKEY_USERS values survive export → import."""
    reg = get_minimal_windows11_testregistry()
    backend = InMemoryBackend(reg)
    path = tmp_path / f"userhive.{fmt}"

    _save_to_format(backend, path, fmt)
    loaded = _load_from_format(path, fmt)

    winreg.use_backend(loaded)  # type: ignore[arg-type]
    hku = winreg.ConnectRegistry(None, winreg.HKEY_USERS)
    vol_env = winreg.OpenKey(hku, r"S-1-5-21-3623811015-3361044348-30300820-1013\Volatile Environment")
    username, utype = winreg.QueryValueEx(vol_env, "USERNAME")
    assert username == "TestUser", f"user-{fmt}: USERNAME={username!r}"
    assert utype == REG_SZ


# ---------------------------------------------------------------------------
# Test 6: REGEDIT4 (version=4) round-trip with all value types
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_regedit4_all_types_roundtrip(tmp_path: Path) -> None:
    """All value types survive a REGEDIT4 (version=4) export → import."""
    backend = _build_comprehensive_registry()
    path = tmp_path / "v4_alltypes.reg"

    # Export as version 4
    winreg.use_backend(backend)  # type: ignore[arg-type]
    from fake_winreg.adapters.persistence.reg_io import export_reg as _export_reg

    _export_reg(path, version=4)

    # Verify header
    raw = path.read_bytes()
    assert raw.startswith(b"REGEDIT4"), "Should have REGEDIT4 header"
    assert not raw.startswith(b"\xff\xfe"), "Should NOT have UTF-16 BOM"

    # Import into fresh backend
    loaded = _load_from_format(path, "reg")

    # Verify all values survived
    _verify_values(loaded, HKEY_LOCAL_MACHINE, WINDOWS11_EXPECTED, "regedit4")
    _verify_all_types(loaded, "regedit4")
