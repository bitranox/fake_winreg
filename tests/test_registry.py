"""Tests for registry default values and SetValueEx type validation.

Ported from the original fake_winreg test suite.
"""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Any, cast

import pytest

import fake_winreg as winreg

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture(autouse=True)
def _fresh_registry() -> Generator[None, None, None]:  # pyright: ignore[reportUnusedFunction]
    """Load a fresh test registry before each test."""
    fake_registry = winreg.fake_reg_tools.get_minimal_windows_testregistry()
    winreg.load_fake_registry(fake_registry)
    yield


# ---------------------------------------------------------------------------
# Default value tests (ported from test_default_values.py)
# ---------------------------------------------------------------------------


@pytest.fixture()
def key_handle_test_read_only() -> Generator[winreg.HKEYType, None, None]:
    reg_handle = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
    key_handle = winreg.CreateKey(reg_handle, "Software\\lib_registry_test")
    with winreg.OpenKeyEx(key_handle, "", 0, winreg.KEY_READ) as key_handle_read_only:
        yield key_handle_read_only
        with contextlib.suppress(OSError):
            winreg.DeleteKey(key_handle, "")


@pytest.fixture()
def key_handle_test_all_access() -> Generator[winreg.HKEYType, None, None]:
    reg_handle = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
    key_handle = winreg.CreateKey(reg_handle, "Software\\lib_registry_test")
    key_handle_all = winreg.OpenKeyEx(key_handle, "", 0, winreg.KEY_ALL_ACCESS)
    yield key_handle_all
    with contextlib.suppress(OSError):
        winreg.DeleteKey(key_handle, "")
    winreg.CloseKey(key_handle)


@pytest.mark.os_agnostic
def test_write_default_value(
    key_handle_test_read_only: winreg.HKEYType,
    key_handle_test_all_access: winreg.HKEYType,
) -> None:
    winreg.SetValue(key_handle_test_all_access, "", winreg.REG_SZ, "test")
    assert winreg.EnumValue(key_handle_test_all_access, 0) == ("", "test", 1)

    winreg.SetValue(key_handle_test_all_access, None, winreg.REG_SZ, "test")
    winreg.EnumValue(key_handle_test_all_access, 0)

    winreg.SetValue(key_handle_test_all_access, None, winreg.REG_SZ, "")
    assert winreg.EnumValue(key_handle_test_all_access, 0) == ("", "", 1)

    winreg.DeleteValue(key_handle_test_all_access, None)
    with pytest.raises(OSError):
        winreg.EnumValue(key_handle_test_read_only, 0)


# ---------------------------------------------------------------------------
# SetValueEx type validation tests (ported from test_set_value_ex.py)
# ---------------------------------------------------------------------------


@pytest.fixture()
def key_handle_setvalue() -> Generator[winreg.HKEYType, None, None]:
    reg_handle = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
    key_handle = winreg.CreateKey(reg_handle, "Software\\lib_registry_test")
    key_handle_all = winreg.OpenKeyEx(key_handle, "", 0, winreg.KEY_ALL_ACCESS)
    yield key_handle_all
    with contextlib.suppress(OSError):
        winreg.DeleteKey(key_handle, "")
    winreg.CloseKey(key_handle)


@pytest.fixture(
    params=[
        winreg.REG_NONE,
        winreg.REG_SZ,
        winreg.REG_EXPAND_SZ,
        winreg.REG_BINARY,
        winreg.REG_DWORD,
        winreg.REG_DWORD_BIG_ENDIAN,
        winreg.REG_LINK,
        winreg.REG_MULTI_SZ,
        winreg.REG_RESOURCE_LIST,
        winreg.REG_FULL_RESOURCE_DESCRIPTOR,
        winreg.REG_RESOURCE_REQUIREMENTS_LIST,
        winreg.REG_QWORD,
        4711,
    ],
    ids=[
        "REG_NONE",
        "REG_SZ",
        "REG_EXPAND_SZ",
        "REG_BINARY",
        "REG_DWORD",
        "REG_DWORD_BIG_ENDIAN",
        "REG_LINK",
        "REG_MULTI_SZ",
        "REG_RESOURCE_LIST",
        "REG_FULL_RESOURCE_DESCRIPTOR",
        "REG_RESOURCE_REQUIREMENTS_LIST",
        "REG_QWORD",
        "REG_UNUSUAL",
    ],
)
def reg_type(request: Any) -> Any:
    return request.param


@pytest.fixture(
    params=[None, 1, "test", ["a", "b"], ["a", 1], (chr(128512) * 10).encode("utf-8")],
    ids=["none", "int", "str", "multi_str", "multi_str_malformed", "bytes"],
)
def data(request: Any) -> Any:
    return request.param


def _is_list_of_str(lst: list[object]) -> bool:
    return all(isinstance(e, str) for e in lst)


_TYPE_ERROR_REG_BINARY = "Objects of type '{data_type}' can not be used as binary registry values"
_TYPE_ERROR_REG_NON_BINARY = "Could not convert the data to the specified type."


def _is_value_accepted(reg_type: Any, data: Any) -> bool:
    """Return whether SetValueEx should accept *data* for *reg_type*."""
    data_type = type(data).__name__
    if reg_type in (winreg.REG_SZ, winreg.REG_EXPAND_SZ):
        return data_type in ("NoneType", "str")
    if reg_type in (winreg.REG_DWORD, winreg.REG_QWORD):
        return data_type in ("NoneType", "int")
    if reg_type == winreg.REG_MULTI_SZ:
        return data is None or (isinstance(data, list) and _is_list_of_str(cast("list[object]", data)))
    return data_type in ("NoneType", "bytes")


def _expected_write_error(reg_type: Any, data: Any) -> tuple[type[Exception], str] | None:
    """Return the exception type and message SetValueEx should raise, or None if it should succeed."""
    if _is_value_accepted(reg_type, data):
        return None
    non_binary_types = (winreg.REG_SZ, winreg.REG_EXPAND_SZ, winreg.REG_DWORD, winreg.REG_QWORD, winreg.REG_MULTI_SZ)
    if reg_type in non_binary_types:
        return ValueError, _TYPE_ERROR_REG_NON_BINARY
    return TypeError, _TYPE_ERROR_REG_BINARY.format(data_type=type(data).__name__)


def _value_write(key_handle: winreg.HKEYType, reg_type: Any, data: Any) -> None:
    winreg.SetValueEx(key_handle, "test_value_name", 0, reg_type, data)


def _is_value_write_ok(key_handle: winreg.HKEYType, reg_type: Any, data: Any) -> bool:
    try:
        _value_write(key_handle, reg_type, data)
        return True
    except Exception:
        return False


def _value_write_error(key_handle: winreg.HKEYType, reg_type: Any, data: Any) -> str:
    try:
        winreg.SetValueEx(key_handle, "test_value_name", 0, reg_type, data)
        return ""
    except Exception as _error:
        return str(_error)


@pytest.mark.os_agnostic
def test_write_value(key_handle_setvalue: winreg.HKEYType, reg_type: Any, data: Any) -> None:
    expected_error = _expected_write_error(reg_type, data)
    if expected_error is None:
        assert _is_value_write_ok(key_handle_setvalue, reg_type, data)
        return

    expected_exception, expected_message = expected_error
    error = _value_write_error(key_handle_setvalue, reg_type, data)
    with pytest.raises(expected_exception):
        _value_write(key_handle_setvalue, reg_type, data)
    assert str(error) == expected_message
