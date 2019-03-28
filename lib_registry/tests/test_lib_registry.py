"""lib_registry tests"""

from lib_registry import *
import pytest
from winreg import *


def test_get_number_of_subkeys():
    assert get_number_of_subkeys(HKEY_USERS) >= 1
