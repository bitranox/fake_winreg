import fake_winreg as winreg
import pytest  # type: ignore
from typing import Generator
import unittest

fake_registry = winreg.fake_reg_tools.get_minimal_windows_testregistry()
winreg.load_fake_registry(fake_registry)


@pytest.fixture(scope="function")
def key_handle_test_read_only() -> Generator[winreg.HKEYType, None, None]:
    reg_handle = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
    key_handle = winreg.CreateKey(reg_handle, "Software\\lib_registry_test")
    with winreg.OpenKeyEx(key_handle, "", 0, winreg.KEY_READ) as key_handle_read_only:
        yield key_handle_read_only
        # teardown code
        try:
            winreg.DeleteKey(key_handle, "")
        # On Windows sometimes this Error occurs, if we try again to delete a key
        # that is already marked for deletion
        # OSError: [WinError 1018]
        except OSError:
            pass


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


def test_write_default_value(key_handle_test_read_only: winreg.HKEYType, key_handle_test_all_access: winreg.HKEYType) -> None:
    # test write value to key default value with SetValue - value Name ''
    winreg.SetValue(key_handle_test_all_access, "", winreg.REG_SZ, "test")
    assert winreg.EnumValue(key_handle_test_all_access, 0) == ("", "test", 1)
    # test write value to key default value with SetValue - value Name None
    winreg.SetValue(key_handle_test_all_access, None, winreg.REG_SZ, "test")

    # try if it appears with enum value
    winreg.EnumValue(key_handle_test_all_access, 0)

    # blank value DOES also appear in enum value
    winreg.SetValue(key_handle_test_all_access, None, winreg.REG_SZ, "")
    assert winreg.EnumValue(key_handle_test_all_access, 0) == ("", "", 1)

    # You need to delete the Value to put it back to Original
    winreg.DeleteValue(key_handle_test_all_access, None)
    unittest.TestCase().assertRaises(OSError, winreg.EnumValue, key_handle_test_read_only, 0)


if __name__ == "__main__":
    pytest.main(["--log-cli-level", "ERROR"])
