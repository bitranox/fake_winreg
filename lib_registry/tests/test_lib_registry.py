"""lib_registry tests"""

from lib_registry import *

if is_platform_windows:
    if is_python2:
        import _winreg as winreg    # type: ignore
    else:
        import winreg               # type: ignore


def test_get_number_of_subkeys():
    # type: () -> None
    if is_platform_windows:
        result = get_number_of_subkeys(winreg.HKEY_USERS)
        assert isinstance(result, int)


def test_get_ls_user_sids():
    # type: () -> None
    if is_platform_windows:
        ls_user_sids = get_ls_user_sids()
        username = get_username_from_sid(ls_user_sids[1])
        if get_is_platform_windows_wine():
            assert username
        else:
            assert username == 'systemprofile'
