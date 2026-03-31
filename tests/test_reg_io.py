"""Tests for .reg file import and export."""
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnknownParameterType=false, reportMissingParameterType=false

from __future__ import annotations

import textwrap

import pytest

from fake_winreg.adapters.persistence.reg_io import export_reg, import_reg
from fake_winreg.domain.api import _get_backend, load_fake_registry, use_backend  # pyright: ignore[reportPrivateUsage]
from fake_winreg.domain.constants import (
    HKEY_CURRENT_USER,
    HKEY_LOCAL_MACHINE,
    REG_BINARY,
    REG_DWORD,
    REG_EXPAND_SZ,
    REG_MULTI_SZ,
    REG_NONE,
    REG_QWORD,
    REG_SZ,
)
from fake_winreg.domain.memory_backend import InMemoryBackend
from fake_winreg.domain.test_registries import get_minimal_windows_testregistry

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fresh_backend() -> InMemoryBackend:
    """Create and activate a fresh in-memory backend."""
    backend = InMemoryBackend()
    use_backend(backend)  # type: ignore[arg-type]
    return backend


def _populate_all_types(backend: InMemoryBackend) -> None:
    """Add one value of every supported type under HKLM\\SOFTWARE\\TestApp."""
    hive = backend.get_hive(HKEY_LOCAL_MACHINE)
    key = backend.create_key(hive, r"SOFTWARE\TestApp")

    backend.set_value(key, "StringVal", "hello world", REG_SZ)
    backend.set_value(key, "", "default value", REG_SZ)
    backend.set_value(key, "DwordVal", 42, REG_DWORD)
    backend.set_value(key, "BinaryVal", b"\xde\xad\xbe\xef", REG_BINARY)
    backend.set_value(key, "ExpandVal", r"%PATH%\bin", REG_EXPAND_SZ)
    backend.set_value(key, "MultiVal", ["Alpha", "Beta"], REG_MULTI_SZ)
    backend.set_value(key, "QwordVal", 42, REG_QWORD)
    backend.set_value(key, "NoneVal", None, REG_NONE)


# ---------------------------------------------------------------------------
# Export tests
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_export_header(tmp_path):
    """Exported file starts with the correct header."""
    _fresh_backend()
    out = tmp_path / "out.reg"
    export_reg(out, hives=["HKEY_LOCAL_MACHINE"])
    content = out.read_text(encoding="utf-16")
    assert content.startswith("Windows Registry Editor Version 5.00\n")


@pytest.mark.os_agnostic
def test_export_key_syntax(tmp_path):
    """Exported keys use square bracket notation."""
    backend = _fresh_backend()
    hive = backend.get_hive(HKEY_LOCAL_MACHINE)
    backend.create_key(hive, r"SOFTWARE\MyApp")

    out = tmp_path / "out.reg"
    export_reg(out, hives=["HKEY_LOCAL_MACHINE"])
    content = out.read_text(encoding="utf-16")
    assert r"[HKEY_LOCAL_MACHINE\SOFTWARE\MyApp]" in content


@pytest.mark.os_agnostic
def test_export_all_value_types(tmp_path):
    """All supported value types are exported with correct syntax."""
    backend = _fresh_backend()
    _populate_all_types(backend)

    out = tmp_path / "out.reg"
    export_reg(out, hives=["HKEY_LOCAL_MACHINE"])
    content = out.read_text(encoding="utf-16")

    assert '"StringVal"="hello world"' in content
    assert '@="default value"' in content
    assert '"DwordVal"=dword:0000002a' in content
    assert '"BinaryVal"=hex:de,ad,be,ef' in content
    assert '"ExpandVal"=hex(2):' in content
    assert '"MultiVal"=hex(7):' in content
    assert '"QwordVal"=hex(b):' in content
    assert '"NoneVal"=hex(0):' in content


# ---------------------------------------------------------------------------
# Import tests
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_import_creates_keys(tmp_path):
    """Importing a .reg file creates the expected keys."""
    _fresh_backend()
    reg_file = tmp_path / "test.reg"
    reg_file.write_text(
        textwrap.dedent("""\
        Windows Registry Editor Version 5.00

        [HKEY_LOCAL_MACHINE\\SOFTWARE\\ImportTest\\Sub1]

        [HKEY_LOCAL_MACHINE\\SOFTWARE\\ImportTest\\Sub2]
    """),
        encoding="utf-8",
    )

    import_reg(reg_file)
    backend = _get_backend()
    hive = backend.get_hive(HKEY_LOCAL_MACHINE)
    key = backend.get_key(hive, r"SOFTWARE\ImportTest")
    subkeys = backend.enum_keys(key)
    assert "Sub1" in subkeys
    assert "Sub2" in subkeys


@pytest.mark.os_agnostic
def test_import_string_value(tmp_path):
    """REG_SZ values are imported correctly."""
    _fresh_backend()
    reg_file = tmp_path / "test.reg"
    reg_file.write_text(
        textwrap.dedent("""\
        Windows Registry Editor Version 5.00

        [HKEY_LOCAL_MACHINE\\SOFTWARE\\Test]
        "Name"="hello"
    """),
        encoding="utf-8",
    )

    import_reg(reg_file)
    backend = _get_backend()
    hive = backend.get_hive(HKEY_LOCAL_MACHINE)
    key = backend.get_key(hive, r"SOFTWARE\Test")
    values = backend.enum_values(key)
    assert ("Name", "hello", REG_SZ) in values


@pytest.mark.os_agnostic
def test_import_default_value(tmp_path):
    """Default values (@=) are imported with empty name."""
    _fresh_backend()
    reg_file = tmp_path / "test.reg"
    reg_file.write_text(
        textwrap.dedent("""\
        Windows Registry Editor Version 5.00

        [HKEY_LOCAL_MACHINE\\SOFTWARE\\Test]
        @="my default"
    """),
        encoding="utf-8",
    )

    import_reg(reg_file)
    backend = _get_backend()
    hive = backend.get_hive(HKEY_LOCAL_MACHINE)
    key = backend.get_key(hive, r"SOFTWARE\Test")
    val = backend.get_value(key, "")
    assert val.value == "my default"
    assert val.value_type == REG_SZ


@pytest.mark.os_agnostic
def test_import_dword(tmp_path):
    """DWORD values are parsed as integers."""
    _fresh_backend()
    reg_file = tmp_path / "test.reg"
    reg_file.write_text(
        textwrap.dedent("""\
        Windows Registry Editor Version 5.00

        [HKEY_LOCAL_MACHINE\\SOFTWARE\\Test]
        "Count"=dword:0000002a
    """),
        encoding="utf-8",
    )

    import_reg(reg_file)
    backend = _get_backend()
    hive = backend.get_hive(HKEY_LOCAL_MACHINE)
    key = backend.get_key(hive, r"SOFTWARE\Test")
    val = backend.get_value(key, "Count")
    assert val.value == 42
    assert val.value_type == REG_DWORD


@pytest.mark.os_agnostic
def test_import_binary(tmp_path):
    """Binary hex values are parsed as bytes."""
    _fresh_backend()
    reg_file = tmp_path / "test.reg"
    reg_file.write_text(
        textwrap.dedent("""\
        Windows Registry Editor Version 5.00

        [HKEY_LOCAL_MACHINE\\SOFTWARE\\Test]
        "Data"=hex:de,ad,be,ef
    """),
        encoding="utf-8",
    )

    import_reg(reg_file)
    backend = _get_backend()
    hive = backend.get_hive(HKEY_LOCAL_MACHINE)
    key = backend.get_key(hive, r"SOFTWARE\Test")
    val = backend.get_value(key, "Data")
    assert val.value == b"\xde\xad\xbe\xef"
    assert val.value_type == REG_BINARY


@pytest.mark.os_agnostic
def test_import_expand_sz(tmp_path):
    """REG_EXPAND_SZ values are decoded from UTF-16 LE."""
    _fresh_backend()
    reg_file = tmp_path / "test.reg"
    # "%PATH%" encoded as UTF-16 LE: 25,00,50,00,41,00,54,00,48,00,25,00,00,00
    reg_file.write_text(
        textwrap.dedent("""\
        Windows Registry Editor Version 5.00

        [HKEY_LOCAL_MACHINE\\SOFTWARE\\Test]
        "Expand"=hex(2):25,00,50,00,41,00,54,00,48,00,25,00,00,00
    """),
        encoding="utf-8",
    )

    import_reg(reg_file)
    backend = _get_backend()
    hive = backend.get_hive(HKEY_LOCAL_MACHINE)
    key = backend.get_key(hive, r"SOFTWARE\Test")
    val = backend.get_value(key, "Expand")
    assert val.value == "%PATH%"
    assert val.value_type == REG_EXPAND_SZ


@pytest.mark.os_agnostic
def test_import_multi_sz(tmp_path):
    """REG_MULTI_SZ values are decoded as list of strings."""
    _fresh_backend()
    reg_file = tmp_path / "test.reg"
    # "A\0B\0\0" in UTF-16 LE
    reg_file.write_text(
        textwrap.dedent("""\
        Windows Registry Editor Version 5.00

        [HKEY_LOCAL_MACHINE\\SOFTWARE\\Test]
        "Multi"=hex(7):41,00,00,00,42,00,00,00,00,00
    """),
        encoding="utf-8",
    )

    import_reg(reg_file)
    backend = _get_backend()
    hive = backend.get_hive(HKEY_LOCAL_MACHINE)
    key = backend.get_key(hive, r"SOFTWARE\Test")
    val = backend.get_value(key, "Multi")
    assert val.value == ["A", "B"]
    assert val.value_type == REG_MULTI_SZ


@pytest.mark.os_agnostic
def test_import_qword(tmp_path):
    """REG_QWORD values are parsed as 64-bit integers."""
    _fresh_backend()
    reg_file = tmp_path / "test.reg"
    # 42 as 8-byte LE: 2a,00,00,00,00,00,00,00
    reg_file.write_text(
        textwrap.dedent("""\
        Windows Registry Editor Version 5.00

        [HKEY_LOCAL_MACHINE\\SOFTWARE\\Test]
        "Big"=hex(b):2a,00,00,00,00,00,00,00
    """),
        encoding="utf-8",
    )

    import_reg(reg_file)
    backend = _get_backend()
    hive = backend.get_hive(HKEY_LOCAL_MACHINE)
    key = backend.get_key(hive, r"SOFTWARE\Test")
    val = backend.get_value(key, "Big")
    assert val.value == 42
    assert val.value_type == REG_QWORD


@pytest.mark.os_agnostic
def test_import_reg_none(tmp_path):
    """REG_NONE values are parsed correctly (empty data)."""
    _fresh_backend()
    reg_file = tmp_path / "test.reg"
    reg_file.write_text(
        textwrap.dedent("""\
        Windows Registry Editor Version 5.00

        [HKEY_LOCAL_MACHINE\\SOFTWARE\\Test]
        "Nothing"=hex(0):
    """),
        encoding="utf-8",
    )

    import_reg(reg_file)
    backend = _get_backend()
    hive = backend.get_hive(HKEY_LOCAL_MACHINE)
    key = backend.get_key(hive, r"SOFTWARE\Test")
    val = backend.get_value(key, "Nothing")
    assert val.value is None
    assert val.value_type == REG_NONE


# ---------------------------------------------------------------------------
# Line continuation
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_import_line_continuation(tmp_path):
    """Lines ending with backslash are joined with the next line."""
    _fresh_backend()
    reg_file = tmp_path / "test.reg"
    reg_file.write_text(
        "Windows Registry Editor Version 5.00\n"
        "\n"
        "[HKEY_LOCAL_MACHINE\\SOFTWARE\\Test]\n"
        '"LongBin"=hex:01,02,03,04,05,06,07,08,09,0a,\\\n'
        "  0b,0c,0d,0e,0f\n",
        encoding="utf-8",
    )

    import_reg(reg_file)
    backend = _get_backend()
    hive = backend.get_hive(HKEY_LOCAL_MACHINE)
    key = backend.get_key(hive, r"SOFTWARE\Test")
    val = backend.get_value(key, "LongBin")
    assert val.value == bytes(range(1, 16))
    assert val.value_type == REG_BINARY


# ---------------------------------------------------------------------------
# String escaping
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_import_escaped_strings(tmp_path):
    """Backslashes and quotes in strings are unescaped correctly."""
    _fresh_backend()
    reg_file = tmp_path / "test.reg"
    reg_file.write_text(
        textwrap.dedent("""\
        Windows Registry Editor Version 5.00

        [HKEY_LOCAL_MACHINE\\SOFTWARE\\Test]
        "Path"="C:\\\\Users\\\\test"
        "Quoted"="He said \\"hi\\""
    """),
        encoding="utf-8",
    )

    import_reg(reg_file)
    backend = _get_backend()
    hive = backend.get_hive(HKEY_LOCAL_MACHINE)
    key = backend.get_key(hive, r"SOFTWARE\Test")

    path_val = backend.get_value(key, "Path")
    assert path_val.value == r"C:\Users\test"

    quoted_val = backend.get_value(key, "Quoted")
    assert quoted_val.value == 'He said "hi"'


@pytest.mark.os_agnostic
def test_export_escapes_strings(tmp_path):
    """Exported strings have backslashes and quotes escaped."""
    backend = _fresh_backend()
    hive = backend.get_hive(HKEY_LOCAL_MACHINE)
    key = backend.create_key(hive, r"SOFTWARE\Test")
    backend.set_value(key, "Path", r"C:\Users\test", REG_SZ)
    backend.set_value(key, "Quoted", 'say "hi"', REG_SZ)

    out = tmp_path / "out.reg"
    export_reg(out, hives=["HKEY_LOCAL_MACHINE"])
    content = out.read_text(encoding="utf-16")

    assert r'"Path"="C:\\Users\\test"' in content
    assert r'"Quoted"="say \"hi\""' in content


# ---------------------------------------------------------------------------
# Delete syntax
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_import_delete_key(tmp_path):
    """[-HKEY_...] syntax deletes the key."""
    backend = _fresh_backend()
    hive = backend.get_hive(HKEY_LOCAL_MACHINE)
    backend.create_key(hive, r"SOFTWARE\ToDelete")

    reg_file = tmp_path / "test.reg"
    reg_file.write_text(
        textwrap.dedent("""\
        Windows Registry Editor Version 5.00

        [-HKEY_LOCAL_MACHINE\\SOFTWARE\\ToDelete]
    """),
        encoding="utf-8",
    )

    import_reg(reg_file)

    with pytest.raises(FileNotFoundError):
        backend.get_key(hive, r"SOFTWARE\ToDelete")


@pytest.mark.os_agnostic
def test_import_delete_value(tmp_path):
    """'Name'=- syntax deletes a value."""
    backend = _fresh_backend()
    hive = backend.get_hive(HKEY_LOCAL_MACHINE)
    key = backend.create_key(hive, r"SOFTWARE\Test")
    backend.set_value(key, "Remove", "old", REG_SZ)

    reg_file = tmp_path / "test.reg"
    reg_file.write_text(
        textwrap.dedent("""\
        Windows Registry Editor Version 5.00

        [HKEY_LOCAL_MACHINE\\SOFTWARE\\Test]
        "Remove"=-
    """),
        encoding="utf-8",
    )

    import_reg(reg_file)

    with pytest.raises(FileNotFoundError):
        backend.get_value(key, "Remove")


# ---------------------------------------------------------------------------
# Round-trip
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_round_trip_all_types(tmp_path):
    """Export -> fresh backend -> import preserves all value types."""
    backend = _fresh_backend()
    _populate_all_types(backend)

    reg_file = tmp_path / "round_trip.reg"
    export_reg(reg_file, hives=["HKEY_LOCAL_MACHINE"])

    # Switch to a fresh backend and import
    fresh = _fresh_backend()
    import_reg(reg_file)

    hive = fresh.get_hive(HKEY_LOCAL_MACHINE)
    key = fresh.get_key(hive, r"SOFTWARE\TestApp")
    values = {name: (data, vtype) for name, data, vtype in fresh.enum_values(key)}

    assert values["StringVal"] == ("hello world", REG_SZ)
    assert values[""] == ("default value", REG_SZ)
    assert values["DwordVal"] == (42, REG_DWORD)
    assert values["BinaryVal"] == (b"\xde\xad\xbe\xef", REG_BINARY)
    assert values["ExpandVal"] == (r"%PATH%\bin", REG_EXPAND_SZ)
    assert values["MultiVal"] == (["Alpha", "Beta"], REG_MULTI_SZ)
    assert values["QwordVal"] == (42, REG_QWORD)
    assert values["NoneVal"][1] == REG_NONE


@pytest.mark.os_agnostic
def test_round_trip_testregistry(tmp_path):
    """Round-trip the minimal Windows test registry."""
    fake_registry = get_minimal_windows_testregistry()
    load_fake_registry(fake_registry)

    reg_file = tmp_path / "testregistry.reg"
    export_reg(reg_file)

    # Import into a fresh backend
    fresh = _fresh_backend()
    import_reg(reg_file)

    hive = fresh.get_hive(HKEY_LOCAL_MACHINE)
    key = fresh.get_key(hive, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
    val = fresh.get_value(key, "CurrentBuild")
    assert val.value == "18363"
    assert val.value_type == REG_SZ


@pytest.mark.os_agnostic
def test_import_comments_and_blanks_are_skipped(tmp_path):
    """Comments and blank lines are ignored during import."""
    _fresh_backend()
    reg_file = tmp_path / "test.reg"
    reg_file.write_text(
        textwrap.dedent("""\
        Windows Registry Editor Version 5.00

        ; This is a comment

        [HKEY_LOCAL_MACHINE\\SOFTWARE\\Test]
        ; another comment
        "Val"="ok"
    """),
        encoding="utf-8",
    )

    import_reg(reg_file)
    backend = _get_backend()
    hive = backend.get_hive(HKEY_LOCAL_MACHINE)
    key = backend.get_key(hive, r"SOFTWARE\Test")
    val = backend.get_value(key, "Val")
    assert val.value == "ok"


@pytest.mark.os_agnostic
def test_import_regedit4_header(tmp_path):
    """REGEDIT4 header is accepted."""
    _fresh_backend()
    reg_file = tmp_path / "test.reg"
    reg_file.write_text(
        textwrap.dedent("""\
        REGEDIT4

        [HKEY_LOCAL_MACHINE\\SOFTWARE\\Old]
        "V"="val"
    """),
        encoding="utf-8",
    )

    import_reg(reg_file)
    backend = _get_backend()
    hive = backend.get_hive(HKEY_LOCAL_MACHINE)
    key = backend.get_key(hive, r"SOFTWARE\Old")
    val = backend.get_value(key, "V")
    assert val.value == "val"


@pytest.mark.os_agnostic
def test_export_hive_filter(tmp_path):
    """Only requested hives appear in filtered export."""
    backend = _fresh_backend()
    hklm = backend.get_hive(HKEY_LOCAL_MACHINE)
    backend.create_key(hklm, r"SOFTWARE\A")
    hkcu = backend.get_hive(HKEY_CURRENT_USER)
    backend.create_key(hkcu, r"SOFTWARE\B")

    out = tmp_path / "out.reg"
    export_reg(out, hives=["HKEY_CURRENT_USER"])
    content = out.read_text(encoding="utf-16")

    assert "HKEY_CURRENT_USER" in content
    assert "HKEY_LOCAL_MACHINE" not in content


# ---------------------------------------------------------------------------
# REGEDIT4 format (version=4)
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_export_regedit4_header(tmp_path):
    """Version 4 export starts with REGEDIT4 header."""
    _fresh_backend()
    out = tmp_path / "out.reg"
    export_reg(out, version=4)
    content = out.read_text(encoding="ascii")
    assert content.startswith("REGEDIT4\n")


@pytest.mark.os_agnostic
def test_export_regedit4_ascii_encoding(tmp_path):
    """Version 4 export uses ASCII encoding, not UTF-16."""
    backend = _fresh_backend()
    hklm = backend.get_hive(HKEY_LOCAL_MACHINE)
    backend.create_key(hklm, r"SOFTWARE\Test")
    backend.set_value(hklm, "TestVal", "hello", REG_SZ)

    out = tmp_path / "out.reg"
    export_reg(out, version=4)

    # Should be valid ASCII — no BOM
    raw = out.read_bytes()
    assert not raw.startswith(b"\xff\xfe"), "Version 4 should not have UTF-16 BOM"
    content = raw.decode("ascii")
    assert "REGEDIT4" in content
    assert "hello" in content


@pytest.mark.os_agnostic
def test_regedit4_roundtrip(tmp_path):
    """Values survive export (v4) → import round-trip."""
    backend = _fresh_backend()
    hklm = backend.get_hive(HKEY_LOCAL_MACHINE)
    key = backend.create_key(hklm, r"SOFTWARE\V4Test")
    backend.set_value(key, "Name", "regedit4", REG_SZ)
    backend.set_value(key, "Count", 99, REG_DWORD)

    out = tmp_path / "v4.reg"
    export_reg(out, version=4)

    # Import into fresh backend
    fresh = _fresh_backend()
    import_reg(out)

    hklm2 = fresh.get_hive(HKEY_LOCAL_MACHINE)
    key2 = fresh.get_key(hklm2, r"SOFTWARE\V4Test")
    val_name = fresh.get_value(key2, "Name")
    val_count = fresh.get_value(key2, "Count")
    assert val_name.value == "regedit4"
    assert val_name.value_type == REG_SZ
    assert val_count.value == 99
    assert val_count.value_type == REG_DWORD


@pytest.mark.os_agnostic
def test_regedit4_import_existing_header(tmp_path):
    """Import correctly handles a file with REGEDIT4 header."""
    reg_content = 'REGEDIT4\r\n\r\n[HKEY_LOCAL_MACHINE\\SOFTWARE\\ImportV4]\r\n"Key"="value"\r\n\r\n'
    out = tmp_path / "import_v4.reg"
    out.write_text(reg_content, encoding="ascii")

    _fresh_backend()
    import_reg(out)

    from fake_winreg.domain.api import _get_backend  # pyright: ignore[reportPrivateUsage]

    backend = _get_backend()
    hklm = backend.get_hive(HKEY_LOCAL_MACHINE)
    key = backend.get_key(hklm, r"SOFTWARE\ImportV4")
    val = backend.get_value(key, "Key")
    assert val.value == "value"
