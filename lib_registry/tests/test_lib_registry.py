"""lib_registry tests"""

from lib_registry import *


def test_get_number_of_subkeys():
    result = get_number_of_subkeys(HKEY_USERS)
    assert isinstance(result, int)


def test_get_ls_user_sids():
    ls_user_sids = get_ls_user_sids()
    username = get_username_from_sid(ls_user_sids[1])
    if get_is_platform_windows_wine():
        assert username
    else:
        assert username == 'systemprofile'
