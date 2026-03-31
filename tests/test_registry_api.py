"""Smoke tests for all 16 winreg API functions.

Tests handle creation, key CRUD, value CRUD, enumeration, and error paths.
"""

from __future__ import annotations

from collections.abc import Generator

import pytest

import fake_winreg as winreg
from fake_winreg.domain.api import configure_network_resolver


@pytest.fixture(autouse=True)
def _fresh_registry() -> Generator[None, None, None]:  # pyright: ignore[reportUnusedFunction]
    """Load a fresh test registry before each test."""
    fake_registry = winreg.fake_reg_tools.get_minimal_windows_testregistry()
    winreg.load_fake_registry(fake_registry)
    yield


# ---------------------------------------------------------------------------
# Connection & handle tests
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_connect_registry_local() -> None:
    handle = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
    assert isinstance(handle, winreg.PyHKEY)
    assert handle.handle.full_key == "HKEY_LOCAL_MACHINE"


@pytest.mark.os_agnostic
def test_connect_registry_invalid_handle() -> None:
    with pytest.raises(OSError, match="handle is invalid"):
        winreg.ConnectRegistry(None, 42)


@pytest.mark.os_agnostic
def test_connect_registry_remote_unreachable() -> None:
    with pytest.raises(OSError, match="network address is invalid"):
        winreg.ConnectRegistry("HAL", winreg.HKEY_LOCAL_MACHINE)


@pytest.mark.os_agnostic
def test_close_key() -> None:
    handle = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
    winreg.CloseKey(handle)


# ---------------------------------------------------------------------------
# Key creation & deletion
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_create_and_delete_key() -> None:
    reg = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
    key = winreg.CreateKey(reg, r"SOFTWARE\test_fake_winreg")
    assert key.handle.full_key == r"HKEY_CURRENT_USER\SOFTWARE\test_fake_winreg"

    winreg.DeleteKey(reg, r"SOFTWARE\test_fake_winreg")

    with pytest.raises(FileNotFoundError):
        winreg.OpenKey(reg, r"SOFTWARE\test_fake_winreg")


@pytest.mark.os_agnostic
def test_create_key_ex() -> None:
    reg = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
    key = winreg.CreateKeyEx(reg, r"SOFTWARE\test_ckex", 0, winreg.KEY_WRITE)
    assert "test_ckex" in key.handle.full_key
    winreg.DeleteKey(reg, r"SOFTWARE\test_ckex")


@pytest.mark.os_agnostic
def test_delete_key_with_subkeys_fails() -> None:
    reg = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
    winreg.CreateKey(reg, r"SOFTWARE\parent\child")

    with pytest.raises(PermissionError, match="Access is denied"):
        winreg.DeleteKey(reg, r"SOFTWARE\parent")

    winreg.DeleteKey(reg, r"SOFTWARE\parent\child")
    winreg.DeleteKey(reg, r"SOFTWARE\parent")


@pytest.mark.os_agnostic
def test_delete_key_ex() -> None:
    reg = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
    winreg.CreateKey(reg, r"SOFTWARE\dkex_test")
    winreg.DeleteKeyEx(reg, r"SOFTWARE\dkex_test")


# ---------------------------------------------------------------------------
# Value operations
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_set_and_query_value() -> None:
    reg = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
    key = winreg.CreateKey(reg, r"SOFTWARE\val_test")

    winreg.SetValue(key, "", winreg.REG_SZ, "hello")
    assert winreg.QueryValue(reg, r"SOFTWARE\val_test") == "hello"

    winreg.DeleteKey(reg, r"SOFTWARE\val_test")


@pytest.mark.os_agnostic
def test_set_and_query_value_ex() -> None:
    reg = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
    key = winreg.CreateKey(reg, r"SOFTWARE\valex_test")

    winreg.SetValueEx(key, "myval", 0, winreg.REG_SZ, "world")
    result = winreg.QueryValueEx(key, "myval")
    assert result == ("world", winreg.REG_SZ)

    winreg.DeleteValue(key, "myval")
    winreg.DeleteKey(reg, r"SOFTWARE\valex_test")


@pytest.mark.os_agnostic
def test_delete_value_nonexistent() -> None:
    reg = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
    key = winreg.CreateKey(reg, r"SOFTWARE\dv_test")

    with pytest.raises(FileNotFoundError):
        winreg.DeleteValue(key, "nonexistent")

    winreg.DeleteKey(reg, r"SOFTWARE\dv_test")


# ---------------------------------------------------------------------------
# Enumeration
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_enum_key() -> None:
    reg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
    key = winreg.OpenKey(reg, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList")
    first_subkey = winreg.EnumKey(key, 0)
    assert isinstance(first_subkey, str)
    assert len(first_subkey) > 0


@pytest.mark.os_agnostic
def test_enum_key_out_of_range() -> None:
    reg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
    key = winreg.OpenKey(reg, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList")
    with pytest.raises(OSError, match="No more data"):
        winreg.EnumKey(key, 999999)


@pytest.mark.os_agnostic
def test_enum_value() -> None:
    reg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
    key = winreg.OpenKey(reg, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
    name, _data, typ = winreg.EnumValue(key, 0)
    assert isinstance(name, str)
    assert isinstance(typ, int)


@pytest.mark.os_agnostic
def test_enum_value_out_of_range() -> None:
    reg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
    key = winreg.OpenKey(reg, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
    with pytest.raises(OSError, match="No more data"):
        winreg.EnumValue(key, 999999)


# ---------------------------------------------------------------------------
# Query info
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_query_info_key() -> None:
    reg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
    key = winreg.OpenKey(reg, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
    n_subkeys, n_values, last_mod = winreg.QueryInfoKey(key)
    assert n_subkeys > 0
    assert n_values > 0
    assert last_mod > 0


# ---------------------------------------------------------------------------
# Open key tests
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_open_key_nonexistent() -> None:
    reg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
    with pytest.raises(FileNotFoundError):
        winreg.OpenKey(reg, r"SOFTWARE\DoesNotExist")


@pytest.mark.os_agnostic
def test_open_key_ex_context_manager() -> None:
    reg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
    with winreg.OpenKeyEx(reg, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion") as key:
        assert "CurrentVersion" in key.handle.full_key


# ---------------------------------------------------------------------------
# Type validation errors
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_check_key_none() -> None:
    with pytest.raises(TypeError, match="None is not a valid HKEY"):
        winreg.OpenKey(None, "")  # type: ignore[arg-type]


@pytest.mark.os_agnostic
def test_check_key_wrong_type() -> None:
    with pytest.raises(TypeError, match="not a PyHKEY"):
        winreg.OpenKey("bad", "")  # type: ignore[arg-type]


@pytest.mark.os_agnostic
def test_check_key_overflow() -> None:
    with pytest.raises(OverflowError, match="int too big"):
        winreg.ConnectRegistry(None, 2**64)


# ---------------------------------------------------------------------------
# Backward compatibility — module aliases
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_module_alias_fake_reg_tools() -> None:
    reg = winreg.fake_reg_tools.get_minimal_windows_testregistry()
    assert isinstance(reg, winreg.FakeRegistry)


@pytest.mark.os_agnostic
def test_module_alias_fake_reg() -> None:
    key = winreg.fake_reg.FakeRegistryKey()
    assert key.full_key == ""


# ---------------------------------------------------------------------------
# Handle identity
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_handle_int_conversion() -> None:
    reg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
    assert int(reg) > 0


@pytest.mark.os_agnostic
def test_pyhkey_detach_returns_zero() -> None:
    reg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
    assert reg.Detach() == 0


# ---------------------------------------------------------------------------
# Wine test registry
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_get_minimal_wine_testregistry() -> None:
    """Verify the Wine test registry is a FakeRegistry with Wine-specific keys."""
    wine_reg = winreg.fake_reg_tools.get_minimal_wine_testregistry()
    assert isinstance(wine_reg, winreg.FakeRegistry)

    winreg.load_fake_registry(wine_reg)
    reg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
    key = winreg.OpenKey(reg, r"Software\Wine")
    assert "Wine" in key.handle.full_key


# ---------------------------------------------------------------------------
# ConnectRegistry — reachable computer name
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_connect_registry_reachable_computer_raises_file_not_found() -> None:
    """A reachable host should raise FileNotFoundError with winerror 53."""
    configure_network_resolver(lambda _name: True)
    try:
        with pytest.raises(FileNotFoundError, match="network path was not found") as exc_info:
            winreg.ConnectRegistry("localhost", winreg.HKEY_LOCAL_MACHINE)
        assert exc_info.value.winerror == 53  # type: ignore[attr-defined]
    finally:
        configure_network_resolver(lambda _name: False)


# ---------------------------------------------------------------------------
# CreateKey / CreateKeyEx — sub_key=None edge cases
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_create_key_with_none_subkey_on_predefined_hkey() -> None:
    """CreateKey with sub_key=None on a predefined HKEY should succeed."""
    reg = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
    key = winreg.CreateKey(reg, None)
    assert key.handle.full_key == "HKEY_CURRENT_USER"


@pytest.mark.os_agnostic
def test_create_key_ex_with_none_subkey_raises_os_error_1010() -> None:
    """CreateKeyEx with sub_key=None should raise OSError with winerror 1010."""
    reg = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
    with pytest.raises(OSError, match="1010") as exc_info:
        winreg.CreateKeyEx(reg, None, 0, winreg.KEY_WRITE)  # type: ignore[arg-type]
    assert exc_info.value.winerror == 1010  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# DeleteKeyEx — KEY_WOW64_32KEY
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_delete_key_ex_wow64_32key_raises_not_implemented() -> None:
    """DeleteKeyEx with KEY_WOW64_32KEY should raise NotImplementedError."""
    reg = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
    winreg.CreateKey(reg, r"SOFTWARE\wow64_test")
    with pytest.raises(NotImplementedError, match="KEY_WOW64_64KEY"):
        winreg.DeleteKeyEx(reg, r"SOFTWARE\wow64_test", winreg.KEY_WOW64_32KEY)
    # Clean up
    winreg.DeleteKey(reg, r"SOFTWARE\wow64_test")


# ---------------------------------------------------------------------------
# QueryValue — non-string default value
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_query_value_non_string_default_raises_os_error_13() -> None:
    """QueryValue should raise OSError winerror 13 when default value is not a string."""
    reg = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
    key = winreg.CreateKey(reg, r"SOFTWARE\qv_nonstr_test")

    # Set a non-string default value (DWORD) using SetValueEx with empty name
    winreg.SetValueEx(key, "", 0, winreg.REG_DWORD, 42)

    with pytest.raises(OSError, match="data is invalid") as exc_info:
        winreg.QueryValue(reg, r"SOFTWARE\qv_nonstr_test")
    assert exc_info.value.winerror == 13  # type: ignore[attr-defined]

    winreg.DeleteValue(key, "")
    winreg.DeleteKey(reg, r"SOFTWARE\qv_nonstr_test")


# ---------------------------------------------------------------------------
# SetValue — non-REG_SZ type
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_set_value_non_reg_sz_raises_type_error() -> None:
    """SetValue with a type other than REG_SZ should raise TypeError."""
    reg = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
    key = winreg.CreateKey(reg, r"SOFTWARE\sv_type_test")

    with pytest.raises(TypeError, match="REG_SZ"):
        winreg.SetValue(key, "", winreg.REG_DWORD, "value")

    winreg.DeleteKey(reg, r"SOFTWARE\sv_type_test")


# ---------------------------------------------------------------------------
# ExpandEnvironmentStrings
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_expand_environment_strings_with_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    """ExpandEnvironmentStrings should expand %VAR% using actual env vars."""
    monkeypatch.setenv("FAKE_WINREG_TEST_VAR", "expanded_value")
    result = winreg.ExpandEnvironmentStrings(r"%FAKE_WINREG_TEST_VAR%\subpath")
    assert result == r"expanded_value\subpath"


@pytest.mark.os_agnostic
def test_expand_environment_strings_unknown_var_unchanged() -> None:
    """ExpandEnvironmentStrings should leave unknown %VAR% references unchanged."""
    result = winreg.ExpandEnvironmentStrings("%THIS_VAR_DOES_NOT_EXIST_XYZ%")
    assert result == "%THIS_VAR_DOES_NOT_EXIST_XYZ%"


# ---------------------------------------------------------------------------
# FlushKey
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_flush_key_no_error() -> None:
    """FlushKey should complete without error."""
    reg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
    winreg.FlushKey(reg)


# ---------------------------------------------------------------------------
# Reflection key functions
# ---------------------------------------------------------------------------


@pytest.mark.os_agnostic
def test_disable_reflection_key_no_error() -> None:
    """DisableReflectionKey should complete without error (no-op)."""
    reg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
    winreg.DisableReflectionKey(reg)


@pytest.mark.os_agnostic
def test_enable_reflection_key_no_error() -> None:
    """EnableReflectionKey should complete without error (no-op)."""
    reg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
    winreg.EnableReflectionKey(reg)


@pytest.mark.os_agnostic
def test_query_reflection_key_returns_true() -> None:
    """QueryReflectionKey should return True (reflection enabled)."""
    reg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
    assert winreg.QueryReflectionKey(reg) is True
