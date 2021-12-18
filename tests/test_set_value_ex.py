import platform
from typing import Any, List, Generator

import pytest  # type: ignore
import unittest

if platform.system() == "Windows":
    import winreg  # type: ignore
else:
    import fake_winreg as winreg  # type: ignore

    fake_registry = winreg.fake_reg_tools.get_minimal_windows_testregistry()  # type: ignore
    winreg.load_fake_registry(fake_registry)  # type: ignore

import logging

logger = logging.getLogger()


@pytest.fixture(scope="function")
def key_handle_test_all_access() -> Generator[winreg.HKEYType, None, None]:
    reg_handle = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
    key_handle = winreg.CreateKey(reg_handle, "Software\\lib_registry_test")
    key_handle_read_only = winreg.OpenKeyEx(key_handle, "", 0, winreg.KEY_ALL_ACCESS)
    yield key_handle_read_only
    # teardown code
    try:
        winreg.DeleteKey(key_handle, "")
    # On Windows sometimes this Error occurs, if we try again to delete a key
    # that is already marked for deletion
    # OSError: [WinError 1018]
    except OSError as e:
        if hasattr(e, "winerror") and e.winerror == 1018:  # type: ignore
            pass
        else:
            raise e

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
        "REG_UNUSUAL",  # SetValueEx accepts any REG_TYPE - it is handled as 'REG_BINARY' then !
    ],
)
def reg_type(request: Any) -> Any:
    return request.param


@pytest.fixture(
    params=[None, 1, "test", ["a", "b"], ["a", 1], (chr(128512) * 10).encode("utf-8")], ids=["none", "int", "str", "multi_str", "multi_str_malformed", "bytes"]
)
def data(request: Any) -> Any:
    return request.param


def test_write_value(key_handle_test_all_access: winreg.HKEYType, reg_type: Any, data: Any) -> None:
    type_error_reg_binary = "Objects of type '{data_type}' can not be used as binary registry values"
    type_error_reg_non_binary = "Could not convert the data to the specified type."
    data_type = type(data).__name__

    def value_write() -> None:
        winreg.SetValueEx(key_handle_test_all_access, "test_value_name", 0, reg_type, data)

    def is_value_write_ok() -> bool:
        try:
            value_write()
            return True
        except Exception:
            return False

    def value_write_error() -> str:
        try:
            winreg.SetValueEx(key_handle_test_all_access, "test_value_name", 0, reg_type, data)
            return ""
        except Exception as _error:
            return str(_error)

    if reg_type == winreg.REG_SZ or reg_type == winreg.REG_EXPAND_SZ:
        valid_types = ["NoneType", "str"]
        if data_type in valid_types:
            assert is_value_write_ok()
        else:
            error = value_write_error()
            unittest.TestCase().assertRaises(ValueError, value_write)
            assert str(error) == type_error_reg_non_binary

    elif reg_type == winreg.REG_DWORD or reg_type == winreg.REG_QWORD:
        valid_types = ["NoneType", "int"]
        if data_type in valid_types:
            assert is_value_write_ok()
        else:
            error = value_write_error()
            unittest.TestCase().assertRaises(ValueError, value_write)
            assert str(error) == type_error_reg_non_binary

    elif reg_type == winreg.REG_MULTI_SZ:
        """
        REG_MULTI_SZ accepts a list of strings -
        if anything else in the list, it will raise :
        ValueError: Could not convert the data to the specified type.
        """
        if data is None or isinstance(data, list) and is_list_of_str(data):
            assert is_value_write_ok()
        else:
            error = value_write_error()
            unittest.TestCase().assertRaises(ValueError, value_write)
            assert str(error) == type_error_reg_non_binary
    else:
        # all other integers for REG_TYPE are accepted, and written to the registry. The value is handled as binary.
        # by that way You would be able to encode data in the REG_TYPE for stealth data not easy to spot - who would expect it.
        valid_types = ["NoneType", "bytes"]
        if data_type in valid_types:
            assert is_value_write_ok()
        else:
            error = value_write_error()
            unittest.TestCase().assertRaises(TypeError, value_write)
            assert str(error) == type_error_reg_binary.format(data_type=data_type)


def is_list_of_str(list_of_str: List[Any]) -> bool:
    for element in list_of_str:
        if not isinstance(element, str):
            return False
    return True


if __name__ == "__main__":
    pytest.main(["--log-cli-level", "ERROR"])
