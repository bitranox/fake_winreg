"""Tests for .reg file import and export."""
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnknownParameterType=false, reportMissingParameterType=false

from __future__ import annotations

import os
import signal
import subprocess
import sys
import textwrap
import time
from typing import TYPE_CHECKING

import pytest

from fake_winreg.adapters.persistence.reg_io import export_reg, import_reg
from fake_winreg.domain.api import get_backend, load_fake_registry, use_backend
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

if TYPE_CHECKING:
    from pathlib import Path

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
    backend = get_backend()
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
    backend = get_backend()
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
    backend = get_backend()
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
    backend = get_backend()
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
    backend = get_backend()
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
    backend = get_backend()
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
    backend = get_backend()
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
    backend = get_backend()
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
    backend = get_backend()
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
    backend = get_backend()
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
    backend = get_backend()
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
    backend = get_backend()
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
    backend = get_backend()
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

    # Should be valid ASCII - no BOM
    raw = out.read_bytes()
    assert not raw.startswith(b"\xff\xfe"), "Version 4 should not have UTF-16 BOM"
    content = raw.decode("ascii")
    assert "REGEDIT4" in content
    assert "hello" in content


@pytest.mark.os_agnostic
def test_regedit4_roundtrip(tmp_path):
    """Values survive export (v4) -> import round-trip."""
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

    backend = get_backend()
    hklm = backend.get_hive(HKEY_LOCAL_MACHINE)
    key = backend.get_key(hklm, r"SOFTWARE\ImportV4")
    val = backend.get_value(key, "Key")
    assert val.value == "value"


# ---------------------------------------------------------------------------
# Streaming import/export
# ---------------------------------------------------------------------------

# Characters str.splitlines treats as line breaks although a .reg file never
# uses them as such; a REG_SZ value may contain any of them.
_NON_REG_LINE_BREAKS = [chr(c) for c in (0x0B, 0x0C, 0x1C, 0x1D, 0x1E, 0x85, 0x2028, 0x2029)]


@pytest.mark.os_agnostic
@pytest.mark.parametrize("encoding", ["utf-16-le", "utf-8"])
@pytest.mark.parametrize("separator", _NON_REG_LINE_BREAKS, ids=lambda c: f"U+{ord(c):04X}")
def test_reg_sz_with_a_non_reg_line_break_round_trips(tmp_path, separator, encoding):
    """Import splits only on CR/LF, so a value holding e.g. U+2028 is not cut in two."""
    backend = _fresh_backend()
    hive = backend.get_hive(HKEY_LOCAL_MACHINE)
    key = backend.create_key(hive, r"SOFTWARE\Breaks")
    value = f"before{separator}after"
    backend.set_value(key, "Text", value, REG_SZ)
    reg_file = tmp_path / "breaks.reg"
    export_reg(reg_file, encoding=encoding)

    fresh = _fresh_backend()
    import_reg(reg_file)
    imported = fresh.get_key(fresh.get_hive(HKEY_LOCAL_MACHINE), r"SOFTWARE\Breaks")
    assert fresh.get_value(imported, "Text").value == value


@pytest.mark.os_agnostic
@pytest.mark.parametrize("line_end", ["\r\n", "\n", "\r"], ids=["crlf", "lf", "cr"])
def test_import_accepts_every_line_ending(tmp_path, line_end):
    _fresh_backend()
    lines = [
        "Windows Registry Editor Version 5.00",
        "",
        r"[HKEY_CURRENT_USER\Ends]",
        '"x"="1"',
        '"b"=hex:01,\\',
        "  02",
    ]
    reg_file = tmp_path / "ends.reg"
    reg_file.write_bytes(line_end.join(lines).encode("utf-8"))
    import_reg(reg_file)
    backend = get_backend()
    key = backend.get_key(backend.get_hive(HKEY_CURRENT_USER), "Ends")
    assert backend.get_value(key, "x").value == "1"
    assert backend.get_value(key, "b").value == b"\x01\x02"


@pytest.mark.os_agnostic
def test_export_with_an_unencodable_value_leaves_no_file(tmp_path):
    """A failed export into a new path does not leave a truncated .reg file behind."""
    backend = _fresh_backend()
    key = backend.create_key(backend.get_hive(HKEY_LOCAL_MACHINE), r"SOFTWARE\Enc")
    backend.set_value(key, "Text", "caf" + chr(0xE9), REG_SZ)
    target = tmp_path / "out.reg"
    with pytest.raises(UnicodeEncodeError):
        export_reg(target, encoding="ascii")
    assert not target.exists()


@pytest.mark.os_agnostic
def test_export_with_an_unknown_codec_leaves_no_file(tmp_path):
    _fresh_backend()
    target = tmp_path / "out.reg"
    with pytest.raises(LookupError):
        export_reg(target, encoding="no-such-codec")
    assert not target.exists()


@pytest.mark.os_agnostic
def test_export_utf8_sig_writes_its_bom_once(tmp_path):
    """Lines are encoded one at a time; a codec's own BOM must still appear only at the start."""
    backend = _fresh_backend()
    backend.create_key(backend.get_hive(HKEY_LOCAL_MACHINE), r"SOFTWARE\Bom")
    target = tmp_path / "bom.reg"
    export_reg(target, encoding="utf-8-sig")
    raw = target.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbfWindows Registry Editor Version 5.00\r\n")
    assert raw.count(b"\xef\xbb\xbf") == 1


@pytest.mark.os_agnostic
def test_export_version_other_than_4_writes_version_5(tmp_path):
    _fresh_backend()
    target = tmp_path / "v.reg"
    export_reg(target, encoding="utf-8", version=7)
    assert target.read_bytes().startswith(b"Windows Registry Editor Version 5.00\r\n")


@pytest.mark.os_agnostic
@pytest.mark.parametrize(
    "encoding", ["utf-16-le", "UTF-16", "utf16", "utf16le", "UTF-16-LE", "utf_16_le", "UTF_16_LE", "utf_16", "u16"]
)
def test_export_every_utf16_spelling_writes_le_with_bom(tmp_path, encoding):
    _fresh_backend()
    target = tmp_path / "u.reg"
    export_reg(target, encoding=encoding)
    assert target.read_bytes().startswith(b"\xff\xfe" + "Windows".encode("utf-16-le"))


@pytest.mark.os_agnostic
@pytest.mark.parametrize("encoding", ["UTF-16-LE", "utf16le", "utf_16_le"])
def test_regedit4_keeps_an_explicitly_named_utf16_encoding(tmp_path: Path, encoding: str) -> None:
    """Only the default spelling ``utf-16-le`` becomes ASCII under version 4; a named one is kept."""
    _fresh_backend()
    target = tmp_path / "v4.reg"
    export_reg(target, encoding=encoding, version=4)
    assert target.read_bytes().startswith(b"\xff\xfe" + "REGEDIT4".encode("utf-16-le"))


# ---------------------------------------------------------------------------
# Import is all or nothing for an undecodable file
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_import_with_an_undecodable_last_line_writes_nothing(tmp_path: Path) -> None:
    """The file is decoded once before the first write, so a bad byte at the end adds no keys."""
    backend = _fresh_backend()
    lines = [b"Windows Registry Editor Version 5.00", b""]
    lines += [b"[HKEY_CURRENT_USER\\Early%04d]" % index for index in range(2000)]
    lines.append(b'"bad"="ab\xffcd"')
    reg_file = tmp_path / "bad.reg"
    reg_file.write_bytes(b"\r\n".join(lines) + b"\r\n")

    with pytest.raises(UnicodeDecodeError):
        import_reg(reg_file)

    assert backend.enum_keys(backend.get_hive(HKEY_CURRENT_USER)) == []


# ---------------------------------------------------------------------------
# Export target handling: new paths, symlinks, non-writable directories, copy-back failures
# ---------------------------------------------------------------------------


def _export_reference(tmp_path: Path) -> bytes:
    """Export the active backend into a fresh file of its own and return its bytes."""
    reference_dir = tmp_path / "reference"
    reference_dir.mkdir()
    reference = reference_dir / "fresh.reg"
    export_reg(reference, encoding="utf-8")
    return reference.read_bytes()


def _running_as_root() -> bool:
    """Return True for a POSIX root process, which ignores directory write permissions."""
    if sys.platform == "win32":
        return False
    return os.geteuid() == 0


@pytest.mark.os_posix
def test_failed_export_through_a_dangling_symlink_keeps_the_link(tmp_path: Path) -> None:
    """A dangling symlink is an existing path: a failed export must not delete it."""
    backend = _fresh_backend()
    key = backend.create_key(backend.get_hive(HKEY_LOCAL_MACHINE), r"SOFTWARE\Enc")
    backend.set_value(key, "Z", "caf" + chr(0xE9), REG_SZ)
    destination = tmp_path / "missing.reg"
    link = tmp_path / "link.reg"
    link.symlink_to(destination)

    with pytest.raises(UnicodeEncodeError):
        export_reg(link, encoding="ascii")

    assert link.is_symlink()
    assert not destination.exists()
    assert sorted(p.name for p in tmp_path.iterdir()) == ["link.reg"]


@pytest.mark.os_posix
def test_export_through_a_dangling_symlink_writes_its_destination(tmp_path: Path) -> None:
    backend = _fresh_backend()
    backend.create_key(backend.get_hive(HKEY_LOCAL_MACHINE), r"SOFTWARE\Link")
    expected = _export_reference(tmp_path)
    destination = tmp_path / "missing.reg"
    link = tmp_path / "link.reg"
    link.symlink_to(destination)

    export_reg(link, encoding="utf-8")

    assert link.is_symlink()
    assert destination.read_bytes() == expected


@pytest.mark.os_posix
@pytest.mark.skipif(_running_as_root(), reason="root writes into a read-only directory anyway")
def test_export_over_a_writable_file_in_a_read_only_directory(tmp_path: Path) -> None:
    """The temp file falls back to the system temp dir when the target's directory is read-only."""
    backend = _fresh_backend()
    backend.create_key(backend.get_hive(HKEY_LOCAL_MACHINE), r"SOFTWARE\ReadOnlyDir")
    expected = _export_reference(tmp_path)
    locked_dir = tmp_path / "locked"
    locked_dir.mkdir()
    target = locked_dir / "out.reg"
    target.write_bytes(b"previous export\r\n")
    locked_dir.chmod(0o555)
    try:
        export_reg(target, encoding="utf-8")
    finally:
        locked_dir.chmod(0o755)

    assert target.read_bytes() == expected
    assert sorted(p.name for p in locked_dir.iterdir()) == ["out.reg"]


# Both children build the same registry and export it once into a reference
# file, so the parent can compare the kept temp file against a complete export.
_CHILD_SETUP = """\
import os
import resource
import signal
import sys
from pathlib import Path

from fake_winreg.adapters.persistence.reg_io import export_reg
from fake_winreg.domain.api import use_backend
from fake_winreg.domain.constants import HKEY_LOCAL_MACHINE, REG_SZ
from fake_winreg.domain.memory_backend import InMemoryBackend

target = Path(os.environ["EXPORT_TARGET"])
reference = Path(os.environ["EXPORT_REFERENCE"])
backend = InMemoryBackend()
use_backend(backend)
key = backend.create_key(backend.get_hive(HKEY_LOCAL_MACHINE), "SOFTWARE\\\\Big")
for index in range(2000):
    backend.set_value(key, f"V{index:05d}", "x" * 50, REG_SZ)
export_reg(reference, encoding="utf-8")
"""

_CHILD_REPORT = """\
try:
    export_reg(target, encoding="utf-8")
except BaseException as exc:
    print(type(exc).__name__)
    print(exc)
else:
    print("no error")
"""

# The file size limit is set only once the export opens the target for the
# copy-back, so the temp file is complete and the copy-back fails partway with
# EFBIG, as a disk filling up during the copy would.
_FILE_TOO_LARGE_CHILD = (
    _CHILD_SETUP
    + """\
signal.signal(signal.SIGXFSZ, signal.SIG_IGN)


def limit_on_target_open(event, args):
    if event == "open" and str(args[0]) == str(target) and "w" in str(args[1]):
        resource.setrlimit(resource.RLIMIT_FSIZE, (4096, resource.getrlimit(resource.RLIMIT_FSIZE)[1]))


sys.addaudithook(limit_on_target_open)
"""
    + _CHILD_REPORT
)

# The target is a FIFO whose reader takes one byte and then stops reading, so the
# copy-back blocks in write until the parent's SIGINT arrives mid-copy.
_INTERRUPTED_CHILD = _CHILD_SETUP + "signal.signal(signal.SIGINT, signal.default_int_handler)\n" + _CHILD_REPORT


def _write_child(tmp_path: Path, source: str) -> tuple[Path, Path, dict[str, str]]:
    """Write *source* as ``child.py`` in *tmp_path*; return the target, the reference and the child's env.

    The paths travel in the environment, so the child's argv stays literal.
    """
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (tmp_path / "child.py").write_text(source, encoding="utf-8")
    target = out_dir / "out.reg"
    reference = tmp_path / "reference.reg"
    env = {**os.environ, "EXPORT_TARGET": str(target), "EXPORT_REFERENCE": str(reference)}
    return target, reference, env


def _kept_temp_files(target: Path) -> list[Path]:
    return sorted(target.parent.glob(f".{target.name}.*.tmp"))


def _wait_for_first_byte(reader: int, deadline_s: float) -> None:
    """Read one byte from a non-blocking FIFO reader, polling until the writer has sent some."""
    deadline = time.monotonic() + deadline_s
    while time.monotonic() < deadline:
        try:
            if os.read(reader, 1):
                return
        except BlockingIOError:
            pass
        time.sleep(0.01)
    pytest.fail("the child never started copying into the FIFO")


@pytest.mark.os_posix
def test_failed_copy_back_keeps_the_complete_export_and_names_it(tmp_path: Path) -> None:
    target, reference, env = _write_child(tmp_path, _FILE_TOO_LARGE_CHILD)
    target.write_bytes(b"previous export\r\n")

    completed = subprocess.run(
        [sys.executable, "child.py"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    report = completed.stdout.splitlines()
    kept = _kept_temp_files(target)
    assert len(kept) == 1
    assert kept[0].read_bytes() == reference.read_bytes()
    assert report[0] == "OSError"
    assert str(kept[0]) in report[1]
    assert "File too large" in report[1]
    assert target.stat().st_size <= 4096


@pytest.mark.os_posix
def test_interrupted_copy_back_keeps_the_complete_export(tmp_path: Path) -> None:
    if sys.platform == "win32":
        pytest.skip("a FIFO needs POSIX")
    target, reference, env = _write_child(tmp_path, _INTERRUPTED_CHILD)
    os.mkfifo(target)
    reader = os.open(target, os.O_RDONLY | os.O_NONBLOCK)
    try:
        with subprocess.Popen(
            [sys.executable, "child.py"],
            cwd=tmp_path,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            errors="replace",
        ) as proc:
            _wait_for_first_byte(reader, deadline_s=60)
            proc.send_signal(signal.SIGINT)
            stdout, stderr = proc.communicate(timeout=60)
    finally:
        os.close(reader)

    assert proc.returncode == 0, stderr
    assert stdout.splitlines()[0] == "KeyboardInterrupt"
    kept = _kept_temp_files(target)
    assert len(kept) == 1
    assert kept[0].read_bytes() == reference.read_bytes()


@pytest.mark.os_agnostic
def test_failed_export_leaves_an_existing_target_untouched(tmp_path):
    """An export that fails partway keeps the file it would have replaced, and leaves no temp file."""
    backend = _fresh_backend()
    key = backend.create_key(backend.get_hive(HKEY_LOCAL_MACHINE), r"SOFTWARE\Enc")
    # Enough encodable lines first that the failure lands after writing has begun.
    for index in range(500):
        backend.set_value(key, f"A{index:04d}", "plain", REG_SZ)
    backend.set_value(key, "Z", "caf" + chr(0xE9), REG_SZ)
    target = tmp_path / "out.reg"
    original = b"previous export\r\n"
    target.write_bytes(original)

    with pytest.raises(UnicodeEncodeError):
        export_reg(target, encoding="ascii")

    assert target.read_bytes() == original
    assert sorted(p.name for p in tmp_path.iterdir()) == ["out.reg"]


@pytest.mark.os_agnostic
def test_successful_export_over_an_existing_target_replaces_its_bytes_in_place(tmp_path):
    """The new content is copied into the existing file (same inode), not renamed over it."""
    backend = _fresh_backend()
    backend.create_key(backend.get_hive(HKEY_LOCAL_MACHINE), r"SOFTWARE\Over")
    fresh_path = tmp_path / "fresh.reg"
    export_reg(fresh_path, encoding="utf-8")
    target = tmp_path / "out.reg"
    target.write_bytes(b"x" * 100_000)
    inode = target.stat().st_ino

    export_reg(target, encoding="utf-8")

    assert target.read_bytes() == fresh_path.read_bytes()
    assert target.stat().st_ino == inode
    assert sorted(p.name for p in tmp_path.iterdir()) == ["fresh.reg", "out.reg"]
