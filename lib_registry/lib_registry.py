# STDLIB
import pathlib
import platform
from typing import Any, List, Dict, Tuple, Union

# EXT
is_platform_windows = platform.system().lower() == 'windows'

# Own
if is_platform_windows:
    import winreg                                       # type: ignore
else:
    import fake_winreg
    # an empty Registry at the Moment
    fake_registry = fake_winreg.FakeRegistry()
    fake_winreg.setup_fake_registry.set_minimal_windows_testvalues(fake_registry)
    winreg = fake_winreg.FakeWinReg(fake_registry)


main_key_hashed_by_name: Dict[str, int] = \
    {
        'hkey_classes_root': winreg.HKEY_CLASSES_ROOT,
        'hkcr': winreg.HKEY_CLASSES_ROOT,
        'hkey_current_config': winreg.HKEY_CURRENT_CONFIG,
        'hkcc': winreg.HKEY_CURRENT_CONFIG,
        'hkey_current_user': winreg.HKEY_CURRENT_USER,
        'hkcu': winreg.HKEY_CURRENT_USER,
        'hkey_dyn_data': winreg.HKEY_DYN_DATA,
        'hkdd': winreg.HKEY_DYN_DATA,
        'hkey_local_machine': winreg.HKEY_LOCAL_MACHINE,
        'hklm': winreg.HKEY_LOCAL_MACHINE,
        'hkey_performance_data': winreg.HKEY_PERFORMANCE_DATA,
        'hkpd': winreg.HKEY_PERFORMANCE_DATA,
        'hkey_users': winreg.HKEY_USERS,
        'hku': winreg.HKEY_USERS
        }


l_hive_names = ['HKEY_LOCAL_MACHINE', 'HKLM', 'HKEY_CURRENT_USER', 'HKCU', 'HKEY_CLASSES_ROOT',
                'HKCR', 'HKEY_CURRENT_CONFIG', 'HKCC', 'HKEY_DYN_DATA', 'HKDD', 'HKEY_USERS',
                'HKU', 'HKEY_PERFORMANCE_DATA', 'HKPD'
                ]

hive_names_hashed_by_int = {winreg.HKEY_CLASSES_ROOT: 'HKEY_CLASSES_ROOT',
                            winreg.HKEY_CURRENT_CONFIG: 'HKEY_CURRENT_CONFIG',
                            winreg.HKEY_CURRENT_USER: 'HKEY_CURRENT_USER',
                            winreg.HKEY_DYN_DATA: 'HKEY_DYN_DATA',
                            winreg.HKEY_LOCAL_MACHINE: 'HKEY_LOCAL_MACHINE',
                            winreg.HKEY_PERFORMANCE_DATA: 'HKEY_PERFORMANCE_DATA',
                            winreg.HKEY_USERS: 'HKEY_USERS'}

reg_type_names_hashed_by_int = {
    winreg.REG_BINARY: 'REG_BINARY',                        # Binary data in any form.
    winreg.REG_DWORD: 'REG_DWORD',                          # 32 - bit number.
    winreg.REG_DWORD_BIG_ENDIAN: 'REG_DWORD_BIG_ENDIAN',    # A 32 - bit number in big - endian format.
    winreg.REG_EXPAND_SZ: 'REG_EXPAND_SZ',                  # Null - terminated string containing references to environment variables( % PATH %).
    winreg.REG_LINK: 'REG_LINK',                            # A Unicode symbolic link.
    winreg.REG_MULTI_SZ: 'REG_MULTI_SZ',                    # A sequence of null - terminated strings, terminated by two null characters.
    winreg.REG_NONE: 'REG_NONE',                            # No defined value type.
    winreg.REG_QWORD: 'REG_QWORD',                          # A 64 - bit number.
    winreg.REG_RESOURCE_LIST: 'REG_RESOURCE_LIST',          # A device - driver resource list.
    winreg.REG_FULL_RESOURCE_DESCRIPTOR: 'REG_FULL_RESOURCE_DESCRIPTOR',        # A hardware setting.
    winreg.REG_RESOURCE_REQUIREMENTS_LIST: 'REG_RESOURCE_REQUIREMENTS_LIST',    # A hardware resource list.
    winreg.REG_SZ: 'REG_SZ',                                # A null-terminated string.
    }


class RegistryError(Exception):
    pass


class RegistryConnectionError(RegistryError):
    pass


class RegistryKeyError(RegistryError):
    pass


class RegistryValueError(RegistryError):
    pass


class RegistryHKeyError(RegistryKeyError):
    pass


class RegistryKeyNotFoundError(RegistryKeyError):
    pass


class RegistryKeyExistsError(RegistryKeyError):
    pass


class RegistryValueNotFoundError(RegistryValueError):
    pass


class RegistryHandleInvalidError(RegistryError):
    pass


class RegistryNetworkConnectionError(RegistryError):
    pass


def reg_connect(key: Union[str, int], computer_name: Union[None, str] = None) -> winreg.HKEYType:
    """
    Gets the registry handle to the hive of the given key :
    get_registry_connection('/hklm/software/....') --> reg_handle to hklm
    get_registry_connection(winreg.HKEY_LOCAL_MACHINE) --> reg_handle to hklm

    >>> reg_connect('HKCR')
    <...PyHKEY object at ...>
    >>> reg_connect('HKCC')
    <...PyHKEY object at ...>
    >>> reg_connect('HKCU')
    <...PyHKEY object at ...>
    >>> reg_connect('HKDD')
    <...PyHKEY object at ...>
    >>> reg_connect('HKLM')
    <...PyHKEY object at ...>
    >>> reg_connect('HKPD')
    <...PyHKEY object at ...>
    >>> reg_connect('HKU')
    <...PyHKEY object at ...>
    >>> reg_connect(winreg.HKEY_LOCAL_MACHINE)
    <...PyHKEY object at ...>

    >>> sid='S-1-5-20'
    >>> key = r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList\\{}'.format(sid)
    >>> reg_connect(key)
    <...PyHKEY object at ...>
    >>> key = r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList\\{}'.format(sid)
    >>> reg_connect(key)
    <...PyHKEY object at ...>
    >>> key = r'HKEY_LOCAL_MACHINE/SOFTWARE/Microsoft/Windows NT/CurrentVersion/ProfileList/{}'.format(sid)
    >>> reg_connect(key)
    <...PyHKEY object at ...>

    >>> reg_connect('SPAM')
    Traceback (most recent call last):
        ...
    lib_registry.RegistryHKeyError: invalid KEY: SPAM

    >>> reg_connect(4711)
    Traceback (most recent call last):
        ...
    lib_registry.RegistryHKeyError: invalid KEY: 4711


    """
    try:
        if isinstance(key, str):
            key = get_hkey_int(key)
        reg_handle = winreg.ConnectRegistry(computer_name, key)
        return reg_handle
    except FileNotFoundError:
        raise RegistryNetworkConnectionError('can not connect to registry on computer {}'.format(computer_name))
    except OSError:
        raise RegistryHKeyError('invalid KEY: {}'.format(key))


def create_key(key: Union[str, int, winreg.HKEYType], sub_key: str = '', exist_ok: bool = True, parents: bool = False) -> winreg.HKEYType:
    """
    Creates a Key, and returns a Handle to the new key

    >>> create_key(r'HKCU\\Software\\lib_registry_test')
    >>> delete_key(r'HKCU\\Software\\lib_registry_test')
    """
    if (not exist_ok) and key_exist(key, sub_key):
        key_string = get_key_as_string(key, sub_key)
        raise RegistryKeyExistsError('can not create key, it already exists: {key_string}'.format(key_string=key_string))

    hive_key, sub_key = get_key_components(key, sub_key)

    if parents:
        pass
    else:
        reg_handle = open_key(hive_key, access=winreg.KEY_WRITE)
        winreg.CreateKey(reg_handle, sub_key)


def get_number_of_subkeys(key: Union[str, int, winreg.HKEYType], sub_key: str = '') -> int:
    """
    param key : one of the winreg HKEY_* constants :
                HKEY_CLASSES_ROOT, HKEY_CURRENT_CONFIG, HKEY_CURRENT_USER, HKEY_DYN_DATA,
                HKEY_LOCAL_MACHINE, HKEY_PERFORMANCE_DATA, HKEY_USERS

    >>> assert get_number_of_subkeys(winreg.HKEY_USERS) > 0
    >>> assert get_number_of_subkeys('HKEY_USERS') > 0
    """
    reg_handle = open_key(key=key, sub_key=sub_key)
    number_of_subkeys, number_of_values, last_modified_win_timestamp = winreg.QueryInfoKey(reg_handle)
    return int(number_of_subkeys)


def get_number_of_values(key: Union[str, int, winreg.HKEYType], sub_key: str = '') -> int:
    """
    param key : one of the winreg HKEY_* constants :
                HKEY_CLASSES_ROOT, HKEY_CURRENT_CONFIG, HKEY_CURRENT_USER, HKEY_DYN_DATA,
                HKEY_LOCAL_MACHINE, HKEY_PERFORMANCE_DATA, HKEY_USERS

    >>> assert get_number_of_values(winreg.HKEY_LOCAL_MACHINE, sub_key=r'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion') > 0
    >>> assert get_number_of_values(r'HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion') > 0
    """
    reg_handle = open_key(key=key, sub_key=sub_key)
    number_of_subkeys, number_of_values, last_modified_win_timestamp = winreg.QueryInfoKey(reg_handle)
    return int(number_of_values)


def get_ls_user_sids() -> List[str]:
    """
    >>> ls_user_sids = get_ls_user_sids()
    >>> assert len(ls_user_sids) > 1
    >>> assert ls_user_sids[0].lower() == '.default'
    >>> # Windows: ['.DEFAULT', 'S-1-5-18', 'S-1-5-19', 'S-1-5-20', ...]
    >>> # Wine: ['.Default', 'S-1-5-21-0-0-0-1000']

    """
    ls_user_sids = []
    n_sub_keys = get_number_of_subkeys(key=winreg.HKEY_USERS)
    for i in range(n_sub_keys):
        subkey = winreg.EnumKey(winreg.HKEY_USERS, i)
        ls_user_sids.append(subkey)
    return sorted(ls_user_sids)


def get_username_from_sid(sid: str) -> str:
    """
    >>> ls_user_sids = get_ls_user_sids()
    >>> assert len(ls_user_sids) > 1
    >>> username = get_username_from_sid(ls_user_sids[1])
    >>> assert len(username) > 1        # 'systemprofile' on windows, '<username>' on wine
    >>> get_username_from_sid('S-1-5-21-206651429-2786145735-121611483-1001')
    'bitranox'
    >>> get_username_from_sid('S-1-5-18')
    'systemprofile'
    >>> get_username_from_sid('S-1-5-42')
    Traceback (most recent call last):
        ...
    lib_registry.RegistryError: can not determine User from SID "S-1-5-42"


    """
    username = ''

    try:
        username = _get_username_from_volatile_environment(sid)
        if username:
            return username
    except RegistryError:
        pass

    try:
        username = _get_username_from_profile_list(sid)
    except RegistryError:
        raise RegistryError('can not determine User from SID "{}"'.format(sid))
    if not username:
        raise RegistryError('can not determine User from SID "{}"'.format(sid))
    return username


def _get_username_from_profile_list(sid: str) -> str:
    """
    >>> _get_username_from_profile_list('S-1-5-21-206651429-2786145735-121611483-1001')
    'bitranox'
    >>> _get_username_from_profile_list('S-1-5-18')
    'systemprofile'

    >>> # Test Key not Found
    >>> _get_username_from_profile_list('unknown')
    Traceback (most recent call last):
        ...
    lib_registry.RegistryKeyNotFoundError: registry key "...unknown" not found

    """
    value = get_value(r'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList\{}'.format(sid), 'ProfileImagePath')
    assert isinstance(value, str)
    username = pathlib.PureWindowsPath(value).name
    return username


def _get_username_from_volatile_environment(sid: str) -> str:
    """
    >>> _get_username_from_volatile_environment('S-1-5-21-206651429-2786145735-121611483-1001')
    'bitranox'
    """
    value = get_value(r'HKEY_USERS\{}\Volatile Environment'.format(sid), 'USERNAME')
    return str(value)


def get_value_ex(key_name: str, value_name: str) -> Tuple[Union[bytes, str, int], int]:
    """
    Return the value and the type of the Value of the given Key and Value Name
    the Type is one of the winreg.REG_* Types

    >>> ### key and subkey exist
    >>> key = r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion'
    >>> build_str, reg_type = get_value_ex(key, 'CurrentBuild')
    >>> assert int(build_str) > 1
    >>> assert reg_type == winreg.REG_SZ

    >>> ### slashes are NOT supported since there are keys with a slash in it !
    >>> key = 'HKEY_LOCAL_MACHINE/SOFTWARE/Microsoft/Windows NT/CurrentVersion'
    >>> build_str = get_value_ex(key, 'CurrentBuild')
    Traceback (most recent call last):
        ...
    lib_registry.RegistryKeyNotFoundError: registry key ... not found


    >>> ### key does not exist
    >>> key = r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\DoesNotExist'
    >>> get_value_ex(key, 'ProfileImagePath')
    Traceback (most recent call last):
    ...
    lib_registry.RegistryKeyNotFoundError: registry key "...DoesNotExist" not found

    >>> ### subkey does not exist
    >>> sid = 'S-1-5-20'
    >>> key = r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion'
    >>> get_value_ex(key, 'does_not_exist')
    Traceback (most recent call last):
       ...
    lib_registry.RegistryValueNotFoundError: value "does_not_exist" not found in key "...CurrentVersion"

    """
    key = open_key(key_name)
    try:
        reg_value, reg_type = winreg.QueryValueEx(key, value_name)
        return reg_value, reg_type
    except FileNotFoundError:
        raise RegistryValueNotFoundError('value "{}" not found in key "{}"'.format(value_name, key_name))


def get_value(key_name: str, value_name: str) -> Union[bytes, str, int]:
    """
    Return the value of the given Key and Value Name

    >>> ### key and subkey exist
    >>> key = r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion'
    >>> build_str = get_value(key, 'CurrentBuild')
    >>> assert int(build_str) > 1

    """
    value, value_type = get_value_ex(key_name, value_name)
    return value


def get_default_value(key_name: str) -> str:
    """
    Return the Default Value of a Key as String -

    * Remark : this is the Value what is shown in Regedit as "(Standard)" or "(Default)" - it does not have a value name.
    it is also not received with Enumvalues and can only be string

    """
    raise NotImplementedError('to come')


def delete_key(key_name: str) -> None:
    root_key = get_hkey_int(key_name)
    reg_path = remove_hive_from_keypath_if_present(key_name)
    winreg.DeleteKey(root_key, reg_path)


def set_value(key_name: str, value_name: str, value: Any, value_type: int = winreg.REG_SZ) -> None:
    """
    value_type:
    REG_BINARY	                Binary data in any form.
    REG_DWORD	                A 32-bit number.
    REG_DWORD_LITTLE_ENDIAN	    A 32-bit number in little-endian format.
    REG_DWORD_BIG_ENDIAN	    A 32-bit number in big-endian format.
    REG_EXPAND_SZ	            Null-terminated string containing references to environment variables (%PATH%).
    REG_LINK	                A Unicode symbolic link.
    REG_MULTI_SZ	            A sequence of null-terminated strings, terminated by two null characters.
                                (Python handles this termination automatically.)
    REG_NONE	                No defined value type.
    REG_RESOURCE_LIST	        A device-driver resource list.
    REG_SZ	                    A null-terminated string.

    >>> create_key(r'HKCU\\Software\\lib_registry_test')
    >>> set_value(key_name=r'HKCU\\Software\\lib_registry_test', value_name='test_name', value='test_string', value_type=winreg.REG_SZ)
    >>> result = get_value(key_name=r'HKCU\\Software\\lib_registry_test', value_name='test_name')
    >>> assert result == 'test_string'
    >>> delete_value(key_name=r'HKCU\\Software\\lib_registry_test', value_name='test_name')
    >>> delete_key(r'HKCU\\Software\\lib_registry_test')

    """
    root_key = get_hkey_int(key_name)
    reg_path = remove_hive_from_keypath_if_present(key_name)
    registry_key = winreg.OpenKey(root_key, reg_path, 0, winreg.KEY_WRITE)
    winreg.SetValueEx(registry_key, value_name, 0, value_type, value)
    winreg.CloseKey(registry_key)


def delete_value(key_name: str, value_name: str) -> None:
    root_key = get_hkey_int(key_name)
    reg_path = remove_hive_from_keypath_if_present(key_name)
    registry_key = winreg.OpenKey(root_key, reg_path, 0, winreg.KEY_ALL_ACCESS)
    winreg.DeleteValue(registry_key, value_name)
    winreg.CloseKey(registry_key)


def get_hkey_int(key_name: str) -> int:
    """
    gets the root hive key from a key_name, containing short or long form, not case sensitive

    >>> assert get_hkey_int('HKLM/something') == winreg.HKEY_LOCAL_MACHINE
    >>> assert get_hkey_int('hklm/something') == winreg.HKEY_LOCAL_MACHINE
    >>> assert get_hkey_int('HKEY_LOCAL_MACHINE/something') == winreg.HKEY_LOCAL_MACHINE
    >>> assert get_hkey_int('hkey_local_machine/something') == winreg.HKEY_LOCAL_MACHINE
    >>> get_hkey_int('Something/else')
    Traceback (most recent call last):
    ...
    lib_registry.RegistryHKeyError: invalid KEY: Something

    """
    key_name = strip_slashes(key_name)
    main_key_name = get_first_part_of_the_key(key_name)
    main_key_name_lower = main_key_name.lower()
    if main_key_name_lower in main_key_hashed_by_name:
        main_key = int(main_key_hashed_by_name[main_key_name_lower])
        return main_key
    else:
        raise RegistryHKeyError('invalid KEY: {main_key_name}'.format(main_key_name=main_key_name))


def strip_slashes(input_string: str) -> str:
    """
    >>> strip_slashes('//test\\\\')
    'test'
    """
    input_string = input_string.strip('/')
    input_string = input_string.strip('\\')
    return input_string


def get_first_part_of_the_key(key_name: str) -> str:
    """
    >>> get_first_part_of_the_key('')
    ''
    >>> get_first_part_of_the_key('something/')
    'something'

    """
    key_name = key_name.split('/', 1)[0]
    key_name = key_name.split('\\', 1)[0]
    return key_name


def remove_hive_from_keypath_if_present(key_name: str) -> str:
    """
    >>> sid='S-1-5-20'
    >>> key = r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList\\{}'.format(sid)
    >>> remove_hive_from_keypath_if_present(key)
    'SOFTWARE\\\\Microsoft\\\\Windows NT\\\\CurrentVersion\\\\ProfileList\\\\S-1-5-20'
    >>> key = r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList\\{}'.format(sid)
    >>> remove_hive_from_keypath_if_present(key)
    'SOFTWARE\\\\Microsoft\\\\Windows NT\\\\CurrentVersion\\\\ProfileList\\\\S-1-5-20'
    >>> key = r'HKEY_LOCAL_MACHINE/SOFTWARE/Microsoft/Windows NT/CurrentVersion/ProfileList/{}'.format(sid)
    >>> remove_hive_from_keypath_if_present(key)
    'SOFTWARE/Microsoft/Windows NT/CurrentVersion/ProfileList/S-1-5-20'
    """

    result = key_name
    for hive_name in l_hive_names:
        hive_name = strip_slashes(hive_name)
        if key_name.startswith(hive_name):
            result = strip_slashes(key_name[len(hive_name):])
            break
    return result


def key_exist(key: Union[str, int, winreg.HKEYType], sub_key: str = '') -> bool:
    """
    >>> key_exist(r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion')
    True
    >>> key_exist(r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\DoesNotExist')
    False

    """

    try:
        open_key(key=key, sub_key=sub_key)
        return True
    except RegistryKeyNotFoundError:
        return False


def open_key(key: Union[str, int, winreg.HKEYType], sub_key: str = '', access: int = winreg.KEY_READ) -> winreg.HKEYType:
    """
    Opens a registry key and returns a reg_handle to it.

    Parameters :    key         can be either a predefined HKEY_* constant,
                                a string containing the root key,
                                or an already open key

                    sub_key     a string with the desired subkey relative to the key

                    access      access is an integer that specifies an access mask that
                                describes the desired security access for the key. Default is winreg.KEY_READ

    >>> reg_handle_hklm = open_key(winreg.HKEY_LOCAL_MACHINE)
    >>> reg_handle1 = open_key(winreg.HKEY_LOCAL_MACHINE, sub_key=r'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList')
    >>> reg_handle2 = open_key(r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList')
    >>> reg_handle3 = open_key(reg_handle_hklm, sub_key=r'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList')
    >>> reg_handle4 = open_key(reg_handle3)
    >>> assert reg_handle1.data == reg_handle2.data == reg_handle3.data == reg_handle4.data

    >>> # Test Key not Found:
    >>> reg_handle = open_key(reg_handle_hklm, sub_key=r'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\non_existing')
    Traceback (most recent call last):
        ...
    lib_registry.RegistryKeyNotFoundError: registry key ... not found

    """

    hive_key, sub_key = get_key_components(key, sub_key)

    if not isinstance(key, winreg.HKEYType):
        reg_handle = winreg.ConnectRegistry(None, hive_key)  # must not use keyword args here, only positional args !
    else:
        reg_handle = key

    # if we have a subkey, or the access is not the default value, open a new handle
    # otherwise return the old handle to save some time
    if sub_key or (access != winreg.KEY_READ):
        try:
            reg_handle = winreg.OpenKey(reg_handle, sub_key, 0, access)
        except FileNotFoundError:
            raise RegistryKeyNotFoundError('registry key "{}" not found'.format(sub_key))
    return reg_handle


def get_key_components(key: Union[str, int, winreg.HKEYType], sub_key: str = '') -> Tuple[int, str]:
    """
    Returns hive_key and sub_key relative zu hive_key if the type if the key is int or str
    """
    hive_key = 0
    if isinstance(key, str):
        hive_key = get_hkey_int(key)
        key_without_hive = remove_hive_from_keypath_if_present(key)
        if sub_key:
            sub_key = r'\\'.join([key_without_hive, sub_key])
        else:
            sub_key = key_without_hive
    elif isinstance(key, int):
        hive_key = key
        if hive_key not in hive_names_hashed_by_int:
            raise RegistryHKeyError('invalid KEY: {hive_key}'.format(hive_key=hive_key))

    return hive_key, sub_key


def get_key_as_string(key: Union[str, int, winreg.HKEYType], sub_key: str = '') -> str:
    """
    >>> reg_handle_hklm = open_key(winreg.HKEY_LOCAL_MACHINE)
    >>> get_key_as_string(winreg.HKEY_LOCAL_MACHINE)
    'HKEY_LOCAL_MACHINE'
    >>> get_key_as_string(winreg.HKEY_LOCAL_MACHINE, sub_key=r'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList')
    'HKEY_LOCAL_MACHINE\\\\SOFTWARE\\\\Microsoft\\\\Windows NT\\\\CurrentVersion\\\\ProfileList'
    >>> get_key_as_string(reg_handle_hklm, sub_key=r'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList')
    'sub_key: SOFTWARE\\\\Microsoft\\\\Windows NT\\\\CurrentVersion\\\\ProfileList'
    >>> get_key_as_string(reg_handle_hklm)
    'the key can not be determined, since it was passed by a handle'

    """
    hive_key, sub_key = get_key_components(key, sub_key)
    if isinstance(key, winreg.HKEYType):
        if sub_key:
            key_as_string = 'sub_key: ' + sub_key
        else:
            key_as_string = 'the key can not be determined, since it was passed by a handle'
    else:
        key_as_string = strip_slashes(hive_names_hashed_by_int[hive_key] + '\\' + sub_key)
    return key_as_string


if __name__ == '__main__':
    print('this is a library only, the executable is named lib_parameter_cli.py')
