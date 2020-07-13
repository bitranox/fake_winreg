# STDLIB
import platform
import time
from typing import Dict, Optional


is_windows = platform.system().lower() == 'windows'

# PROJ
try:
    from .types_custom import *
    from .registry_constants import *
except (ImportError, ModuleNotFoundError):      # pragma: no cover
    # imports for doctest
    from types_custom import *                  # type: ignore  # pragma: no cover
    from registry_constants import *            # type: ignore  # pragma: no cover


class FakeRegistry(object):

    def __init__(self) -> None:
        # the Key of the hive Dict is int or PyHKEY
        self.hive: Dict[object, FakeRegistryKey] = dict()
        self.hive[HKEY_CLASSES_ROOT] = set_fake_reg_key(FakeRegistryKey(), 'HKEY_CLASSES_ROOT')
        self.hive[HKEY_CURRENT_CONFIG] = set_fake_reg_key(FakeRegistryKey(), 'HKEY_CURRENT_CONFIG')
        self.hive[HKEY_CURRENT_USER] = set_fake_reg_key(FakeRegistryKey(), 'HKEY_CURRENT_USER')
        self.hive[HKEY_DYN_DATA] = set_fake_reg_key(FakeRegistryKey(), 'HKEY_DYN_DATA')
        self.hive[HKEY_LOCAL_MACHINE] = set_fake_reg_key(FakeRegistryKey(), 'HKEY_LOCAL_MACHINE')
        self.hive[HKEY_PERFORMANCE_DATA] = set_fake_reg_key(FakeRegistryKey(), 'HKEY_PERFORMANCE_DATA')
        self.hive[HKEY_USERS] = set_fake_reg_key(FakeRegistryKey(), 'HKEY_USERS')


class FakeRegistryKey(object):
    def __init__(self) -> None:
        """
        >>> fake_reg_root = FakeRegistryKey()
        """
        # the key name including the hive
        self.full_key: str = ''
        # the parent fake_key
        self.parent_fake_registry_key: Optional[FakeRegistryKey] = None
        # the subkeys, hashed by reg_key
        self.subkeys: Dict[str, FakeRegistryKey] = dict()
        # the values, hashed by value_name
        self.values: Dict[str, FakeRegistryValue] = dict()
        # the time in ns since (Linux)Epoch, of the last modification, some entries dont have timestamp
        self.last_modified_ns: int = 0


class FakeRegistryValue(object):
    def __init__(self) -> None:
        """
        >>> fake_reg_value = FakeRegistryValue()
        """
        # the key name including the hive (Not including the Value Name)
        self.full_key: str = ''
        # the name of the value
        self.value_name: str = ''
        # the value
        self.value: RegData = ''
        # the REG_* type of the Value
        self.value_type: int = REG_SZ
        # used in module fake_winreg, Default = KEY_READ
        self.access: int = 0
        # the time in ns since (Linux)Epoch, of the last modification, some entries dont have timestamp
        self.last_modified_ns: Union[None, int] = None


def set_fake_reg_key(fake_reg_key: FakeRegistryKey, sub_key: Union[str, None] = None,
                     last_modified_ns: Union[int, None] = None) -> FakeRegistryKey:
    """
    Creates a registry key if it does not exist already

    >>> fake_reg_root = FakeRegistryKey()
    >>> assert set_fake_reg_key(fake_reg_key=fake_reg_root, sub_key=r'HKEY_LOCAL_MACHINE').full_key == 'HKEY_LOCAL_MACHINE'
    >>> assert set_fake_reg_key(fake_reg_key=fake_reg_root,
    ...     sub_key=r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT').full_key == r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT'
    """
    if last_modified_ns is None:
        last_modified_ns = get_windows_timestamp_now()

    key_parts_full = fake_reg_key.full_key.split('\\')
    if sub_key:
        key_parts_sub = sub_key.split('\\')
    else:
        key_parts_sub = []

    data = fake_reg_key

    for key_part in key_parts_sub:
        key_parts_full.append(key_part)

        if key_part not in data.subkeys:
            data.subkeys[key_part] = FakeRegistryKey()
            data.subkeys[key_part].full_key = ('\\'.join(key_parts_full)).strip('\\')
            data.subkeys[key_part].last_modified_ns = last_modified_ns
            data.subkeys[key_part].parent_fake_registry_key = data
        data = data.subkeys[key_part]

    return data


def get_fake_reg_key(fake_reg_key: FakeRegistryKey, sub_key: str) -> FakeRegistryKey:
    """
    >>> # Setup
    >>> fake_reg_root = FakeRegistryKey()
    >>> assert set_fake_reg_key(fake_reg_key=fake_reg_root,
    ...     sub_key=r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT').full_key == r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT'

    >>> # Test existing Key
    >>> assert get_fake_reg_key(fake_reg_key=fake_reg_root,
    ...     sub_key=r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT').full_key == r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT'

    >>> # Test not existing Key
    >>> get_fake_reg_key(fake_reg_key=fake_reg_root, sub_key=r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\non_existing')
    Traceback (most recent call last):
        ...
    FileNotFoundError: subkey not found, key="HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft", subkey="non_existing"

    """
    current_fake_reg_key = fake_reg_key
    if sub_key:
        key_parts = sub_key.split('\\')
        for key_part in key_parts:
            try:
                current_fake_reg_key = current_fake_reg_key.subkeys[key_part]
            except KeyError:
                raise FileNotFoundError('subkey not found, key="{}", subkey="{}"'.format(current_fake_reg_key.full_key, key_part))
    return current_fake_reg_key


def set_fake_reg_value(fake_reg_key: FakeRegistryKey, sub_key: str,
                       value_name: str, value: Union[None, bytes, str, List[str], int], value_type: int = REG_SZ,
                       last_modified_ns: Union[int, None] = None) -> FakeRegistryValue:
    """
    sets the value of the fake key - we create here keys on the fly, but beware of the last_modified_ns time !
    if You need to have correct last_modified_ns time for each subkey, You need to create those keys first

    >>> # Setup
    >>> fake_reg_root = FakeRegistryKey()
    >>> fake_reg_key = set_fake_reg_key(fake_reg_key=fake_reg_root, sub_key=r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT')

    >>> # Write Value
    >>> fake_reg_value = set_fake_reg_value(fake_reg_key, '', 'CurrentBuild', '18363', REG_SZ)
    >>> assert fake_reg_value.full_key == r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT'
    >>> assert fake_reg_value.value_name == 'CurrentBuild'
    >>> assert fake_reg_value.value == '18363'
    >>> assert fake_reg_value.value_type == REG_SZ
    >>> last_modified_ns = fake_reg_value.last_modified_ns

    >>> # Write other Value to the same fake_registry_value :
    >>> time.sleep(0.1)
    >>> fake_reg_value = set_fake_reg_value(fake_reg_key, '', 'CurrentBuild', '18364', REG_MULTI_SZ, last_modified_ns=get_windows_timestamp_now())
    >>> assert fake_reg_value.value == '18364'
    >>> assert fake_reg_value.value_type == REG_MULTI_SZ
    >>> assert fake_reg_value.last_modified_ns != last_modified_ns

    """

    if last_modified_ns is None:
        last_modified_ns = get_windows_timestamp_now()

    # create the keys if not there - take care for the last_modified_ns on that automatically created keys
    fake_reg_key = set_fake_reg_key(fake_reg_key=fake_reg_key, sub_key=sub_key, last_modified_ns=last_modified_ns)

    if value_name not in fake_reg_key.values:
        fake_reg_key.values[value_name] = FakeRegistryValue()
        fake_reg_value = fake_reg_key.values[value_name]
        fake_reg_value.full_key = fake_reg_key.full_key
        fake_reg_value.value_name = value_name
    else:
        fake_reg_value = fake_reg_key.values[value_name]

    fake_reg_value.value = value
    fake_reg_value.value_type = value_type
    fake_reg_value.last_modified_ns = last_modified_ns
    return fake_reg_value


def get_windows_timestamp_now() -> int:
    """
    Windows Timestamp in hundreds of ns since 01.01.1601 – 00:00:00 UTC

    >>> assert get_windows_timestamp_now() > 10000
    >>> save_time = get_windows_timestamp_now()
    >>> time.sleep(0.1)
    >>> assert get_windows_timestamp_now() > save_time

    """
    linux_timestamp_100ns = int(time.time() * 1E7)
    linux_windows_diff_100ns = int(11644473600 * 1E7)
    windows_timestamp_100ns = linux_timestamp_100ns + linux_windows_diff_100ns
    return windows_timestamp_100ns
