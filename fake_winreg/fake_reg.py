# STDLIB
import ctypes
import subprocess
import pathlib
import platform
import time
from typing import Dict, Optional, Union


is_windows = platform.system().lower() == 'windows'

# CONSTANTS
HKEY_CLASSES_ROOT: int = 18446744071562067968
HKEY_CURRENT_CONFIG: int = 18446744071562067973
HKEY_CURRENT_USER: int = 18446744071562067969
HKEY_DYN_DATA: int = 18446744071562067974
HKEY_LOCAL_MACHINE: int = 18446744071562067970
HKEY_PERFORMANCE_DATA: int = 18446744071562067972
HKEY_USERS: int = 18446744071562067971

# value Types
REG_BINARY: int = 3                 # Binary data in any form.
REG_DWORD: int = 4                  # 32 - bit number.
REG_DWORD_LITTLE_ENDIAN: int = 4    # A 32 - bit number in little - endian format.Equivalent to REG_DWORD.
REG_DWORD_BIG_ENDIAN: int = 5       # A 32 - bit number in big - endian format.
REG_EXPAND_SZ: int = 2              # Null - terminated string containing references to environment variables( % PATH %).
REG_LINK: int = 6                   # A Unicode symbolic link.
REG_MULTI_SZ: int = 7               # A sequence of null - terminated strings, terminated by two null characters. python handles this termination automatically
REG_NONE: int = 0                   # No defined value type.
REG_QWORD: int = 11                 # A 64 - bit number.
REG_QWORD_LITTLE_ENDIAN: int = 11   # A 64 - bit number in little - endian format.Equivalent to REG_QWORD.
REG_RESOURCE_LIST: int = 8          # A device - driver resource list.
REG_FULL_RESOURCE_DESCRIPTOR: int = 9       # A hardware setting.
REG_RESOURCE_REQUIREMENTS_LIST: int = 10    # A hardware resource list.
REG_SZ: int = 1                             # A null-terminated string.
# the type of a fake registry key in the csv file
REG_FAKE_KEY = -1

# key access rights
# Combines the STANDARD_RIGHTS_REQUIRED, KEY_QUERY_VALUE, KEY_SET_VALUE, KEY_CREATE_SUB_KEY,
# KEY_ENUMERATE_SUB_KEYS, KEY_NOTIFY, and KEY_CREATE_LINK access rights.
KEY_ALL_ACCESS = 983103
KEY_WRITE = 131078          # Combines the STANDARD_RIGHTS_WRITE, KEY_SET_VALUE, and KEY_CREATE_SUB_KEY access rights.
KEY_READ = 131097           # Combines the STANDARD_RIGHTS_READ, KEY_QUERY_VALUE, KEY_ENUMERATE_SUB_KEYS, and KEY_NOTIFY values.
KEY_EXECUTE = 131097        # Equivalent to KEY_READ.
KEY_QUERY_VALUE = 1         # Required to query the values of a registry key.
KEY_SET_VALUE = 2           # Required to create, delete, or set a registry value.
KEY_CREATE_SUB_KEY = 4      # Required to create a subkey of a registry key.
KEY_ENUMERATE_SUB_KEYS = 8  # Required to enumerate the subkeys of a registry key.
KEY_NOTIFY = 16             # Required to request change notifications for a registry key or for subkeys of a registry key.
KEY_CREATE_LINK = 32        # Reserved for system use.
KEY_WOW64_64KEY = 256       # Indicates that an application on 64-bit Windows should operate on the 64-bit registry view.
KEY_WOW64_32KEY = 512       # Indicates that an application on 64-bit Windows should operate on the 32-bit registry view.


hive_name_hashed_by_int = dict()
hive_name_hashed_by_int[18446744071562067968] = 'HKEY_CLASSES_ROOT'
hive_name_hashed_by_int[18446744071562067973] = 'HKEY_CURRENT_CONFIG'
hive_name_hashed_by_int[18446744071562067969] = 'HKEY_CURRENT_USER'
hive_name_hashed_by_int[18446744071562067974] = 'HKEY_DYN_DATA'
hive_name_hashed_by_int[18446744071562067970] = 'HKEY_LOCAL_MACHINE'
hive_name_hashed_by_int[18446744071562067972] = 'HKEY_PERFORMANCE_DATA'
hive_name_hashed_by_int[18446744071562067971] = 'HKEY_USERS'


class FakeRegistry(object):

    def __init__(self) -> None:
        self.hive = dict()
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
        self.value: Union[None, bytes, str, int] = ''
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
                       value_name: str, value: Union[None, bytes, str, int], value_type: int = REG_SZ,
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


def dump_windows_registry_branch_to_hive_file(root_key: str, path_hive_file: pathlib.Path) -> None:
    """
    You can only save SUBKEYS of of HKLM and HKU under Windows 10 !!!
    since that is not practical, and we get a lot of additional (hidden) registry Values, we decided to use winreg to read in the future !
    we keep that part of the code as documentation

    >>> # Setup
    >>> path_test_dir = pathlib.Path(__file__).resolve().parent.parent / 'tests'
    >>> path_test_hive_file = path_test_dir / 'test_hklm_ProfileList.hive'
    >>> if is_windows:
    ...     dump_windows_registry_branch_to_hive_file(r'HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList', path_test_hive_file)

    >>> # Teardown
    >>> if path_test_hive_file.exists(): path_test_hive_file.unlink()

    """
    if not is_windows:
        raise RuntimeError('you can only dump the registry to a file on windows')
    if is_windows_wine():
        raise RuntimeError('WINE does not support "reg save"')
    if not is_windows_user_admin():
        raise RuntimeError('You need to run the Program as Administrator to be able to save the Registry')
    subprocess.run(['reg', 'save', root_key, str(path_hive_file), '/y'], check=True)


def is_windows_wine() -> bool:
    """
    >>> assert is_windows_wine() or True == True

    """
    if is_windows:
        import winreg as real_winreg    # type: ignore

        reg_handle = real_winreg.ConnectRegistry(None, real_winreg.HKEY_LOCAL_MACHINE)
        try:
            real_winreg.OpenKey(reg_handle, r'Software\Wine')
            return True
        except FileNotFoundError:
            pass
    return False


def is_windows_user_admin() -> bool:
    if is_windows:
        is_admin = int(ctypes.windll.shell32.IsUserAnAdmin()) == 1  # type: ignore
        is_admin = bool(is_admin)
        return is_admin
    else:
        raise RuntimeError('You can check that only on Windows')


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
