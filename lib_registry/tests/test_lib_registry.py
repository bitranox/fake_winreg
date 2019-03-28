"""lib_registry tests"""

from lib_registry import *
from winreg import *


def test_get_number_of_subkeys():
    result = get_number_of_subkeys(HKEY_USERS)
    assert isinstance(result, int)
