# STDLIB
"""

https://github.com/adamkerz/winreglib/blob/master/winreglib.py


"""

import pathlib
import platform
from types import TracebackType
from typing import Dict, Iterator, Optional, Tuple, Type, Union

# EXT

is_platform_windows = platform.system().lower() == 'windows'

# Own
try:
    from . import helpers
    from .types_custom import *
except ImportError:                 # pragma: no cover
    import helpers                  # type: ignore      # pragma: no cover
    from types_custom import *      # type: ignore      # pragma: no cover

if is_platform_windows:
    import winreg                           # type: ignore
else:
    import fake_winreg as winreg            # type: ignore
    # an empty Registry at the Moment
    fake_registry = winreg.fake_reg_tools.get_minimal_windows_testregistry()    # type: ignore
    winreg.load_fake_registry(fake_registry)                                    # type: ignore


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


class RegistryHKeyError(RegistryError):
    pass


class RegistryKeyNotFoundError(RegistryKeyError):
    pass


class RegistryKeyExistsError(RegistryKeyError):
    pass


class RegistryKeyCreateError(RegistryKeyError):
    pass


class RegistryKeyDeleteError(RegistryKeyError):
    pass


class RegistryValueNotFoundError(RegistryValueError):
    pass


class RegistryValueDeleteError(RegistryValueError):
    pass


class RegistryValueWriteError(RegistryValueError):
    pass


class RegistryHandleInvalidError(RegistryError):
    pass


class RegistryNetworkConnectionError(RegistryError):
    pass


# Registry{{{
class Registry(object):
    def __init__(self, key: Union[None, str, int] = None, computer_name: Optional[str] = None):
        """
        The Registry Class, to create the registry object.
        If a key is passed, a connection to the hive is established.

        Parameter
        ---------

        key:
            the predefined handle to connect to,
            or a key string with the hive as the first part (everything else but the hive will be ignored)
            or None (then no connection will be established)
        computer_name:
            the name of the remote computer, of the form r"\\computer_name" or "computer_name". If None, the local computer is used.

        Exceptions
        ----------
            RegistryNetworkConnectionError      if can not reach target computer
            RegistryHKeyError                   if can not connect to the hive
            winreg.ConnectRegistry              auditing event

        Examples
        --------

        >>> # just create the instance without connection
        >>> registry = Registry()

        >>> # test connect at init:
        >>> registry = Registry('HKCU')

        >>> # test invalid hive as string
        >>> Registry()._reg_connect('SPAM')
        Traceback (most recent call last):
            ...
        lib_registry.RegistryHKeyError: invalid KEY: "SPAM"

        >>> # test invalid hive as integer
        >>> Registry()._reg_connect(42)
        Traceback (most recent call last):
            ...
        lib_registry.RegistryHKeyError: invalid HIVE KEY: "42"

        >>> # test invalid computer to connect
        >>> Registry()._reg_connect(winreg.HKEY_LOCAL_MACHINE, computer_name='some_unknown_machine')
        Traceback (most recent call last):
            ...
        lib_registry.RegistryNetworkConnectionError: The network address "some_unknown_machine" is invalid

        >>> # test invalid network Path
        >>> Registry()._reg_connect(winreg.HKEY_LOCAL_MACHINE, computer_name=r'localhost\\ham\\spam')
        Traceback (most recent call last):
            ...
        lib_registry.RegistryNetworkConnectionError: The network path to "localhost\\ham\\spam" was not found

        """
        # Registry}}}

        # this holds all connections to the hives stated on init
        # or even later. We dont limit access to the selected hive,
        # but we connect to another hive if needed
        self.reg_hive_connections: Dict[int, winreg.HKEYType] = dict()
        self.computer_name = computer_name
        # if the computer is set already once by _connect -
        # we can not connect to different computers in the same with clause
        self._is_computer_name_set = False

        # we save and reuse the connections
        # dict[(hive, subkey, access)] = winreg.HKEYType
        self.reg_key_handles: Dict[Tuple[int, str, int], winreg.HKEYType] = dict()

        if key is not None:
            self._reg_connect(key=key, computer_name=computer_name)

    def __call__(self, key: Union[None, str, int], computer_name: Optional[str] = None) -> None:
        self.__init__(key, computer_name)  # type: ignore

    def __enter__(self) -> "Registry":
        return self

    def __exit__(self, exc_type: Optional[Type[BaseException]], exc_val: Optional[BaseException], exc_tb: Optional[TracebackType]) -> None:
        print('close connections !!!')

    def _reg_connect(self, key: Union[str, int], computer_name: Optional[str] = None) -> winreg.HKEYType:
        """
        Establishes a connection to a predefined registry handle on another computer, and returns a handle object.
        The user should not need to use this method - hives are opened, reused and closed automatically

        Parameter
        ---------

        key:
            the predefined handle to connect to,
            or a key string with the hive as the first part (everything else but the hive will be ignored)
        computer_name:
            the name of the remote computer, of the form r"\\computer_name" or "computer_name". If None, the local computer is used.

        Result
        ------
            the handle of the opened hive

        Exceptions
        ----------
            RegistryNetworkConnectionError      if can not reach target computer
            RegistryHKeyError                   if can not connect to the hive
            winreg.ConnectRegistry              auditing event

        Examples
        --------

        >>> # test connect at init:
        >>> registry = Registry('HKCU')
        >>> registry.reg_hive_connections[winreg.HKEY_CURRENT_USER]
        <...PyHKEY object at ...>
        >>> # test hive as string
        >>> Registry()._reg_connect('HKCR')
        <...PyHKEY object at ...>
        >>> Registry()._reg_connect('HKCC')
        <...PyHKEY object at ...>
        >>> Registry()._reg_connect('HKCU')
        <...PyHKEY object at ...>
        >>> Registry()._reg_connect('HKDD')
        <...PyHKEY object at ...>
        >>> Registry()._reg_connect('HKLM')
        <...PyHKEY object at ...>
        >>> Registry()._reg_connect('HKPD')
        <...PyHKEY object at ...>
        >>> Registry()._reg_connect('HKU')
        <...PyHKEY object at ...>
        >>> Registry()._reg_connect(r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList')
        <...PyHKEY object at ...>

        >>> # test hive as predefined hkey
        >>> Registry()._reg_connect(winreg.HKEY_LOCAL_MACHINE)
        <...PyHKEY object at ...>

        >>> # test invalid hive as string
        >>> Registry()._reg_connect('SPAM')
        Traceback (most recent call last):
            ...
        lib_registry.RegistryHKeyError: invalid KEY: "SPAM"

        >>> # test invalid hive as integer
        >>> Registry()._reg_connect(42)
        Traceback (most recent call last):
            ...
        lib_registry.RegistryHKeyError: invalid HIVE KEY: "42"

        >>> # test invalid computer to connect
        >>> Registry()._reg_connect(winreg.HKEY_LOCAL_MACHINE, computer_name='some_unknown_machine')
        Traceback (most recent call last):
            ...
        lib_registry.RegistryNetworkConnectionError: The network address "some_unknown_machine" is invalid

        >>> # test invalid network Path
        >>> Registry()._reg_connect(winreg.HKEY_LOCAL_MACHINE, computer_name=r'localhost\\ham\\spam')
        Traceback (most recent call last):
            ...
        lib_registry.RegistryNetworkConnectionError: The network path to "localhost\\ham\\spam" was not found

        """
        try:
            if self._is_computer_name_set and computer_name != self.computer_name:
                raise RegistryError('can not connect to different Machines in the same scope')

            hive_key, hive_sub_key = resolve_key(key)

            if hive_key in self.reg_hive_connections:
                hive_handle = self.reg_hive_connections[hive_key]
            else:
                hive_handle = winreg.ConnectRegistry(computer_name, hive_key)
                self.reg_hive_connections[hive_key] = hive_handle
                self._is_computer_name_set = True
            return hive_handle

        except FileNotFoundError as e_fnf:
            if hasattr(e_fnf, 'winerror') and e_fnf.winerror == 53:    # type: ignore
                raise RegistryNetworkConnectionError(f'The network path to "{computer_name}" was not found')
            else:
                raise RegistryConnectionError('unknown error connecting to registry')

        except OSError as e_os:
            if hasattr(e_os, 'winerror'):
                if e_os.winerror == 1707:       # type: ignore
                    # OSError: [WinError 1707] The network address is invalid
                    raise RegistryNetworkConnectionError(f'The network address "{computer_name}" is invalid')
                elif e_os.winerror == 6:        # type: ignore
                    raise RegistryHKeyError(f'invalid KEY: "{key}"')
            else:
                raise RegistryConnectionError('unknown error connecting to registry')

        assert False

    def _open_key(self, key: Union[str, int], sub_key: str = '', access: int = winreg.KEY_READ) -> winreg.HKEYType:
        """
        Opens a registry key and returns a reg_handle to it.
        Openend Keys with the Access Rights are stored in a Hash Table and Reused if possible.
        The user should not need to use this method - keys are opened , reused and closed automatically


        Parameter
        ---------
        key
          either a predefined HKEY_* constant,
          a string containing the root key,
          or an already open key

        sub_key
          a string with the desired subkey relative to the key

        access
          access is an integer that specifies an access mask that
          describes the desired security access for the key. Default is winreg.KEY_READ

        >>> registry = Registry()
        >>> reg_handle1 = registry._open_key(winreg.HKEY_LOCAL_MACHINE, sub_key=r'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList')
        >>> reg_handle2 = registry._open_key(r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList')
        >>> assert reg_handle1 == reg_handle2

        >>> # Test Key not Found:
        >>> reg_handle = registry._open_key(winreg.HKEY_LOCAL_MACHINE, sub_key=r'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\non_existing')
        Traceback (most recent call last):
            ...
        lib_registry.RegistryKeyNotFoundError: registry key ... not found

        """

        hive_key, hive_sub_key = resolve_key(key, sub_key)
        if (hive_key, hive_sub_key, access) in self.reg_key_handles:
            key_handle = self.reg_key_handles[(hive_key, hive_sub_key, access)]
        else:
            reg_handle = self._reg_connect(hive_key)
            try:
                key_handle = winreg.OpenKey(reg_handle, hive_sub_key, 0, access)
                self.reg_key_handles[(hive_key, hive_sub_key, access)] = key_handle
            except FileNotFoundError:
                key_str = get_key_as_string(key, sub_key)
                raise RegistryKeyNotFoundError(f'registry key "{key_str}" not found')
        return key_handle

    # create_key{{{
    def create_key(self, key: Union[str, int], sub_key: str = '', exist_ok: bool = True, parents: bool = False) -> winreg.HKEYType:
        """
        Creates a Key, and returns a Handle to the new key


        Parameter
        ---------
        key
          either a predefined HKEY_* constant,
          a string containing the root key,
          or an already open key
        sub_key
          a string with the desired subkey relative to the key
        exist_ok
          bool, default = True
        parents
          bool, default = false


        Exceptions
        ----------
        RegistryKeyCreateError
            if can not create the key


        Examples
        --------

        >>> # Setup
        >>> registry = Registry()
        >>> # create a key
        >>> registry.create_key(r'HKCU\\Software')
        <...PyHKEY object at ...>

        >>> # create an existing key, with exist_ok = True
        >>> registry.create_key(r'HKCU\\Software\\lib_registry_test', exist_ok=True)
        <...PyHKEY object at ...>

        >>> # create an existing key, with exist_ok = False (parent existing)
        >>> registry.create_key(r'HKCU\\Software\\lib_registry_test', exist_ok=False)
        Traceback (most recent call last):
            ...
        lib_registry.RegistryKeyCreateError: can not create key, it already exists: HKEY_CURRENT_USER...lib_registry_test

        >>> # create a key, parent not existing, with parents = False
        >>> registry.create_key(r'HKCU\\Software\\lib_registry_test\\a\\b', parents=False)
        Traceback (most recent call last):
            ...
        lib_registry.RegistryKeyCreateError: can not create key, the parent key to "HKEY_CURRENT_USER...b" does not exist

        >>> # create a key, parent not existing, with parents = True
        >>> registry.create_key(r'HKCU\\Software\\lib_registry_test\\a\\b', parents=True)
        <...PyHKEY object at ...>

        >>> # TEARDOWN
        >>> registry.delete_key(r'HKCU\\Software\\lib_registry_test', delete_subkeys=True)

        """
        # create_key}}}

        hive_key, hive_sub_key = resolve_key(key, sub_key)
        _key_exists = self.key_exist(hive_key, hive_sub_key)
        if (not exist_ok) and _key_exists:
            key_string = get_key_as_string(hive_key, hive_sub_key)
            raise RegistryKeyCreateError(f'can not create key, it already exists: {key_string}')
        elif _key_exists:
            key_handle = self._open_key(hive_key, hive_sub_key, winreg.KEY_ALL_ACCESS)
            return key_handle

        if not parents:
            hive_sub_key_parent = '\\'.join(hive_sub_key.split('\\')[:-1])
            if not self.key_exist(hive_key, hive_sub_key_parent):
                key_str = get_key_as_string(hive_key, hive_sub_key)
                raise RegistryKeyCreateError(f'can not create key, the parent key to "{key_str}" does not exist')

        new_key_handle = winreg.CreateKey(hive_key, hive_sub_key)
        self.reg_key_handles[(hive_key, hive_sub_key, winreg.KEY_ALL_ACCESS)] = new_key_handle

        return new_key_handle

    # delete_key{{{
    def delete_key(self, key: Union[str, int], sub_key: str = '', missing_ok: bool = False, delete_subkeys: bool = False) -> None:
        """
        deletes the specified key, this method can delete keys with subkeys.
        If the method succeeds, the entire key, including all of its values, is removed.

        Parameter
        ---------
        key
          either a predefined HKEY_* constant,
          a string containing the root key,
          or an already open key
        sub_key
          a string with the desired subkey relative to the key
        missing_ok
          bool, default = False
        delete_subkeys
          bool, default = False

        Exceptions
        ----------
            RegistryKeyDeleteError  If the key does not exist,
            RegistryKeyDeleteError  If the key has subkeys and delete_subkeys = False

        >>> # Setup
        >>> registry = Registry()
        >>> # create a key, parent not existing, with parents = True
        >>> registry.create_key(r'HKCU\\Software\\lib_registry_test\\a\\b', parents=True)
        <...PyHKEY object at ...>

        >>> # Delete a Key
        >>> assert registry.key_exist(r'HKCU\\Software\\lib_registry_test\\a\\b') == True
        >>> registry.delete_key(r'HKCU\\Software\\lib_registry_test\\a\\b')
        >>> assert registry.key_exist(r'HKCU\\Software\\lib_registry_test\\a\\b') == False

        >>> # Try to delete a missing Key
        >>> registry.delete_key(r'HKCU\\Software\\lib_registry_test\\a\\b')
        Traceback (most recent call last):
            ...
        lib_registry.RegistryKeyDeleteError: can not delete key none existing key ...

        >>> # Try to delete a missing Key, missing_ok = True
        >>> registry.delete_key(r'HKCU\\Software\\lib_registry_test\\a\\b')
        Traceback (most recent call last):
            ...
        lib_registry.RegistryKeyDeleteError: can not delete key none existing key ...

        >>> # Try to delete a Key with subkeys
        >>> registry.delete_key(r'HKCU\\Software\\lib_registry_test')
        Traceback (most recent call last):
            ...
        lib_registry.RegistryKeyDeleteError: can not delete none empty key ...

        >>> # Try to delete a Key with subkeys, delete_subkeys = True
        >>> registry.delete_key(r'HKCU\\Software\\lib_registry_test', delete_subkeys=True)
        >>> assert registry.key_exist(r'HKCU\\Software\\lib_registry_test') == False

        >>> # Try to delete a Key with missing_ok = True
        >>> registry.delete_key(r'HKCU\\Software\\lib_registry_test', missing_ok=True)

        """
        # delete_key}}}

        hive_key, hive_sub_key = resolve_key(key, sub_key)
        _key_exists = self.key_exist(hive_key, hive_sub_key)

        if not _key_exists:
            if missing_ok:
                return
            else:
                key_str = get_key_as_string(key, sub_key)
                raise RegistryKeyDeleteError(f'can not delete key none existing key "{key_str}"')

        if self.has_subkeys(hive_key, hive_sub_key):
            if not delete_subkeys:
                key_str = get_key_as_string(key, sub_key)
                raise RegistryKeyDeleteError(f'can not delete none empty key "{key_str}"')
            else:
                for sub_key in self.subkeys(hive_key, hive_sub_key):
                    hive_subkey_child = '\\'.join([hive_sub_key, sub_key])
                    self.delete_key(hive_key, hive_subkey_child, missing_ok=True, delete_subkeys=True)

        # we know only two access methods - KEY_READ and KEY_ALL_ACCESS
        # we close the handles before we delete the key
        if (hive_key, hive_sub_key, winreg.KEY_READ) in self.reg_key_handles:
            self.reg_key_handles[(hive_key, hive_sub_key, winreg.KEY_READ)].Close()
        if (hive_key, hive_sub_key, winreg.KEY_ALL_ACCESS) in self.reg_key_handles:
            self.reg_key_handles[(hive_key, hive_sub_key, winreg.KEY_ALL_ACCESS)].Close()

        try:
            winreg.DeleteKey(hive_key, hive_sub_key)
        # On Windows sometimes this Error occurs, if we try to delete a key that is already marked for deletion
        # OSError: [WinError 1018] Illegal operation attempted on a registry key that has been marked for deletion.
        except OSError as e:
            if hasattr(e, 'winerror') and e.winerror == 1018:   # type: ignore
                pass
            else:
                raise e

        # we know only two access methods - KEY_READ and KEY_ALL_ACCESS
        # we delete here key_handles from the cache
        self.reg_key_handles.pop((hive_key, hive_sub_key, winreg.KEY_READ), None)
        self.reg_key_handles.pop((hive_key, hive_sub_key, winreg.KEY_ALL_ACCESS), None)

    # key_exist{{{
    def key_exist(self, key: Union[str, int], sub_key: str = '') -> bool:
        """
        True if the given key exists

        Parameter
        ---------
        key
          either a predefined HKEY_* constant,
          a string containing the root key,
          or an already open key

        sub_key
          a string with the desired subkey relative to the key


        Examples
        --------

        >>> Registry().key_exist(r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion')
        True
        >>> Registry().key_exist(r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\DoesNotExist')
        False

        """
        # key_exist}}}

        try:
            self._open_key(key=key, sub_key=sub_key)
            return True
        except RegistryKeyNotFoundError:
            return False

    def key_info(self, key: Union[str, int], sub_key: str = '') -> Tuple[int, int, int]:
        """
        Returns information about a key, as a tuple.
        The result is a tuple of 3 items:
        Index, Meaning
                0       An integer giving the number of sub keys this key has.
                1       An integer giving the number of values this key has.
                2       An integer giving when the key was last modified (if available) as 100’s of nanoseconds since Jan 1, 1601.
        Raises an auditing event winreg.QueryInfoKey with argument key. (NOT IMPLEMENTED)

        >>> # DONE #3
        >>> registry = Registry()
        >>> registry.key_info(winreg.HKEY_USERS)
        (...)
        >>> registry.key_info('HKEY_USERS')
        (...)

        """
        key_handle = self._open_key(key=key, sub_key=sub_key)
        number_of_subkeys, number_of_values, last_modified_win_timestamp = winreg.QueryInfoKey(key_handle)
        return number_of_subkeys, number_of_values, last_modified_win_timestamp

    def number_of_subkeys(self, key: Union[str, int], sub_key: str = '') -> int:
        """
        Returns an integer giving the number of sub keys this key has.
        Raises an auditing event winreg.QueryInfoKey with argument key.

        >>> # DONE #3
        >>> registry = Registry()
        >>> assert registry.number_of_subkeys(winreg.HKEY_USERS) > 0
        >>> assert registry.number_of_subkeys('HKEY_USERS') > 0
        """

        number_of_subkeys, number_of_values, last_modified_win_timestamp = self.key_info(key, sub_key)
        return int(number_of_subkeys)

    def number_of_values(self, key: Union[str, int], sub_key: str = '') -> int:
        """
        Returns an integer giving the number of values this key has.
        Raises an auditing event winreg.QueryInfoKey with argument key.

        >>> # DONE #3
        >>> registry = Registry()
        >>> discard = registry.number_of_values(winreg.HKEY_USERS)
        >>> discard2 = registry.number_of_values('HKEY_USERS')
        """

        number_of_subkeys, number_of_values, last_modified_win_timestamp = self.key_info(key, sub_key)
        return int(number_of_values)

    def last_access_timestamp_windows(self, key: Union[str, int], sub_key: str = '') -> int:
        """
        Returns an integer giving when the key was last modified (if available) as 100’s of nanoseconds since Jan 1, 1601.
        Raises an auditing event winreg.QueryInfoKey with argument key.

        >>> # DONE #3
        >>> registry = Registry()
        >>> discard = registry.last_access_timestamp_windows(winreg.HKEY_USERS)
        >>> discard2 = registry.last_access_timestamp_windows('HKEY_USERS')

        """
        number_of_subkeys, number_of_values, last_modified_win_timestamp = self.key_info(key, sub_key)
        return int(last_modified_win_timestamp)

    def last_access_timestamp(self, key: Union[str, int], sub_key: str = '') -> float:
        """
        Return the time in seconds since the epoch as a floating point number.
        The specific date of the epoch and the handling of leap seconds is platform dependent.
        On Windows and most Unix systems, the epoch is January 1, 1970, 00:00:00 (UTC)
        and leap seconds are not counted towards the time in seconds since the epoch.
        This is commonly referred to as Unix time.
        Raises an auditing event winreg.QueryInfoKey with argument key.

        >>> # DONE #3
        >>> registry = Registry()
        >>> discard = registry.last_access_timestamp(winreg.HKEY_USERS)
        >>> assert registry.last_access_timestamp('HKEY_USERS') > 1594390488.8894954

        """
        windows_timestamp_100ns = self.last_access_timestamp_windows(key, sub_key)
        linux_windows_diff_100ns = int(11644473600 * 1E7)
        linux_timestamp_100ns = windows_timestamp_100ns - linux_windows_diff_100ns
        float_epoch = linux_timestamp_100ns / 1E7
        return float_epoch

    def has_subkeys(self, key: Union[str, int], sub_key: str = '') -> bool:
        """
        Return if the key has subkeys

        >>> # DONE #3
        >>> registry = Registry()
        >>> assert registry.has_subkeys(winreg.HKEY_USERS) == True

        """
        number_of_subkeys = self.number_of_subkeys(key=key, sub_key=sub_key)
        if number_of_subkeys:
            return True
        else:
            return False

    def subkeys(self, key: Union[str, int], sub_key: str = '') -> Iterator[str]:
        """
        Iterates through subkeys of an open registry key, returning a string.
        key by string, or one of the predefined HKEY_* constants.
        The function retrieves the name of one subkey each time it is called.
        Raises an auditing event winreg.EnumKey with arguments key, index.

        >>> # DONE #3
        >>> registry = Registry()
        >>> registry.subkeys(winreg.HKEY_USERS)
        <generator object Registry.subkeys at ...>
        >>> list(registry.subkeys(winreg.HKEY_USERS))
        [...S-1-5-...']

        """
        key_handle = self._open_key(key, sub_key)
        index = 0
        while True:
            try:
                subkey = winreg.EnumKey(key_handle, index)
                index = index + 1
                yield subkey
            except OSError as e:
                # [WinError 259] No more data is available
                if hasattr(e, 'winerror') and e.winerror == 259:    # type: ignore
                    break
                else:
                    raise e

    def values(self, key: Union[str, int], sub_key: str = '') -> Iterator[Tuple[str, RegData, int]]:
        """
        Iterates through values of an registry key, returning a tuple.
        key by string, or one of the predefined HKEY_* constants.
        The function retrieves the name of one subkey each time it is called.
        Raises an auditing event winreg.EnumValue with arguments key, index.

        The result is a tuple of 3 items:
        Index       Meaning
        0           A string that identifies the value name
        1           An object that holds the value data, and whose type depends on the underlying registry type
        2           An integer giving the registry type for this value (see table in docs for SetValueEx())



        Registry Types
        --------------

        =========  ==============================  ====================== ==========================================================================
        type(int)  type name                       accepted python Types  Description
        =========  ==============================  ====================== ==========================================================================
        0          REG_NONE	                       None, bytes            No defined value type.
        1          REG_SZ	                       None, str              A null-terminated string.
        2          REG_EXPAND_SZ	               None, str              Null-terminated string containing references to
                                                                          environment variables (%PATH%).
                                                                          (Python handles this termination automatically.)
        3          REG_BINARY	                   None, bytes            Binary data in any form.
        4          REG_DWORD	                   None, int              A 32-bit number.
        4          REG_DWORD_LITTLE_ENDIAN	       None, int              A 32-bit number in little-endian format.
        5          REG_DWORD_BIG_ENDIAN	           None, bytes            A 32-bit number in big-endian format.
        6          REG_LINK	                       None, bytes            A Unicode symbolic link.
        7          REG_MULTI_SZ	                   None, List[str]        A sequence of null-terminated strings, terminated by two null characters.
        8          REG_RESOURCE_LIST	           None, bytes            A device-driver resource list.
        9          REG_FULL_RESOURCE_DESCRIPTOR    None, bytes            A hardware setting.
        10         REG_RESOURCE_REQUIREMENTS_LIST  None, bytes            A hardware resource list.
        11         REG_QWORD                       None, bytes            A 64 - bit number.
        11         REG_QWORD_LITTLE_ENDIAN         None, bytes            A 64 - bit number in little - endian format.Equivalent to REG_QWORD.
        =========  ==============================  ====================== ==========================================================================
        - all other integers for REG_TYPE are accepted, and written to the registry.
          The value is handled as binary.
          by that way You would be able to encode data in the REG_TYPE for stealth data not easy to spot - who would expect it.


        >>> # DONE #3
        >>> registry = Registry()
        >>> registry.values(r'HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion')
        <generator object Registry.values at ...>
        >>> list(registry.values(r'HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion'))
        [...]

        """

        key_handle = self._open_key(key, sub_key)
        index = 0
        while True:
            try:
                value_name, value, value_type = winreg.EnumValue(key_handle, index)
                index = index + 1
                yield value_name, value, value_type
            except OSError as e:
                # [WinError 259] No more data is available
                assert hasattr(e, 'winerror')
                if hasattr(e, 'winerror') and e.winerror == 259:    # type: ignore
                    break
                else:
                    raise e

    def sids(self) -> Iterator[str]:
        """
        Iterates through sids (SECURITY IDENTIFIER)
        The function retrieves the name of one SID each time it is called.
        Raises an auditing event winreg.EnumKey with arguments key, index.

        >>> registry = Registry()
        >>> registry.sids
        <...Registry object at ...>>
        >>> list(registry.sids())
        ['S-1-5-...']
        >>> # Windows: ['S-1-5-18', 'S-1-5-19', 'S-1-5-20', ...]
        >>> # Wine: ['S-1-5-21-0-0-0-1000']

        """
        key = 'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList'
        for sid in self.subkeys(key):
            yield sid

    def get_value(self, key: Union[str, int], value_name: Optional[str]) -> RegData:
        """
        Retrieves the data for a specified value name associated with an open registry key.
        key by string, or one of the predefined HKEY_* constants.
        value_name is a string indicating the value to query.
        if value_name is None or '', it Reads the Default Value of the key - an Error is raised, if No Default Value is set.

        * Remark : this is the Value what is shown in Regedit as "(Standard)" or "(Default)" - it is usually not set.
        Nethertheless, even if the Default Value is not set, winreg.QueryValue will deliver ''

        >>> # DONE #3
        >>> registry = Registry()
        >>> registry.get_value(r'HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion', 'CurrentBuild')
        '...'

        >>> # value does not exist
        >>> registry.get_value(r'HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion', 'DoesNotExist')
        Traceback (most recent call last):
        ...
        lib_registry.RegistryValueNotFoundError: value "DoesNotExist" not found in key "...CurrentVersion"

        """
        result, result_type = self.get_value_ex(key, value_name)
        return result

    def get_value_ex(self, key: Union[str, int], value_name: Optional[str]) -> Tuple[RegData, int]:
        """
        Retrieves the data and type for a specified value name associated with an open registry key.
        key by string, or one of the predefined HKEY_* constants.
        value_name is a string indicating the value to query.
        if value_name is None or '', it Reads the Default Value of the key - an Error is raised, if No Default Value is set.

        * Remark : this is the Value what is shown in Regedit as "(Standard)" or "(Default)" - it is usually not set.
        Nethertheless, even if the Default Value is not set, winreg.QueryValue will deliver ''


        Result
        ------

        The result is a tuple of 2 items:

        ========  =================================================================================================
        Index       Meaning
        ========  =================================================================================================
        0           The value of the registry item.
        1           An integer giving the registry type for this value (see table in docs for SetValueEx())
        ========  =================================================================================================

        Raises an auditing event winreg.QueryValue with arguments key, sub_key, value_name. (NOT Implemented)



        Registry Types
        --------------

        =========  ==============================  ====================== ==========================================================================
        type(int)  type name                       accepted python Types  Description
        =========  ==============================  ====================== ==========================================================================
        0          REG_NONE	                       None, bytes            No defined value type.
        1          REG_SZ	                       None, str              A null-terminated string.
        2          REG_EXPAND_SZ	               None, str              Null-terminated string containing references to
                                                                          environment variables (%PATH%).
                                                                          (Python handles this termination automatically.)
        3          REG_BINARY	                   None, bytes            Binary data in any form.
        4          REG_DWORD	                   None, int              A 32-bit number.
        4          REG_DWORD_LITTLE_ENDIAN	       None, int              A 32-bit number in little-endian format.
        5          REG_DWORD_BIG_ENDIAN	           None, bytes            A 32-bit number in big-endian format.
        6          REG_LINK	                       None, bytes            A Unicode symbolic link.
        7          REG_MULTI_SZ	                   None, List[str]        A sequence of null-terminated strings, terminated by two null characters.
        8          REG_RESOURCE_LIST	           None, bytes            A device-driver resource list.
        9          REG_FULL_RESOURCE_DESCRIPTOR    None, bytes            A hardware setting.
        10         REG_RESOURCE_REQUIREMENTS_LIST  None, bytes            A hardware resource list.
        11         REG_QWORD                       None, bytes            A 64 - bit number.
        11         REG_QWORD_LITTLE_ENDIAN         None, bytes            A 64 - bit number in little - endian format.Equivalent to REG_QWORD.
        =========  ==============================  ====================== ==========================================================================
        - all other integers for REG_TYPE are accepted, and written to the registry.
          The value is handled as binary.
          by that way You would be able to encode data in the REG_TYPE for stealth data not easy to spot - who would expect it.


        >>> # DONE #3
        >>> registry = Registry()
        >>> registry.get_value_ex(r'HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion', 'CurrentBuild')
        (...)

        >>> # value does not exist
        >>> registry.get_value_ex(r'HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion', 'DoesNotExist')
        Traceback (most recent call last):
        ...
        lib_registry.RegistryValueNotFoundError: value "DoesNotExist" not found in key "...CurrentVersion"

        """
        if value_name is None:
            value_name = ''

        key_handle = self._open_key(key)
        try:
            reg_value, reg_type = winreg.QueryValueEx(key_handle, value_name)
            return reg_value, reg_type
        except FileNotFoundError:
            key_str = get_key_as_string(key)
            raise RegistryValueNotFoundError(f'value "{value_name}" not found in key "{key_str}"')

    def username_from_sid(self, sid: str) -> str:
        """

        >>> # Setup
        >>> l_users = list()
        >>> registry = Registry()
        >>> for sid in registry.sids():
        ...     try:
        ...         username = registry.username_from_sid(sid)
        ...         l_users.append(username)
        ...     except RegistryKeyNotFoundError:
        ...         pass
        >>> l_users
        [...]

        """

        try:
            username = self._get_username_from_volatile_environment(sid)
            if username:
                return username
        except RegistryError:
            pass

        try:
            username = self._get_username_from_profile_list(sid)
        except RegistryError:
            raise RegistryError(f'can not determine User for SID "{sid}"')
        if not username:
            raise RegistryError(f'can not determine User for SID "{sid}"')
        return username

    def _get_username_from_profile_list(self, sid: str) -> str:
        """
        gets the username by SID from the Profile Image Path

        >>> # Setup
        >>> registry = Registry()
        >>> for sid in registry.sids():
        ...     try:
        ...         registry._get_username_from_profile_list(sid)
        ...         break
        ...     except RegistryKeyNotFoundError:
        ...         pass
        '...'

        >>> # Test Key not Found
        >>> registry._get_username_from_profile_list('unknown')
        Traceback (most recent call last):
            ...
        lib_registry.RegistryKeyNotFoundError: registry key "...unknown" not found

        """
        value, value_type = self.get_value_ex(fr'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList\{sid}', 'ProfileImagePath')
        assert isinstance(value, str)
        username = pathlib.PureWindowsPath(value).name
        return username

    def _get_username_from_volatile_environment(self, sid: str) -> str:
        """
        gets the username by SID from the Volatile Environment

        >>> # Setup
        >>> registry = Registry()
        >>> import os
        >>> if 'TRAVIS' not in os.environ:     # there seems to be no volatile environment set in travis windows machine
        ...     for sid in registry.sids():
        ...         try:
        ...             registry._get_username_from_volatile_environment(sid)
        ...             break
        ...         except RegistryKeyNotFoundError:
        ...             pass
        ... else:
        ...   print("'pass'")
        '...'

        """
        value, value_type = self.get_value_ex(fr'HKEY_USERS\{sid}\Volatile Environment', 'USERNAME')
        assert isinstance(value, str)
        return str(value)

    def set_value(self, key: Union[str, int], value_name: Optional[str], value: RegData, value_type: Optional[int] = None) -> None:
        """
        Stores data in the value field of an open registry key.
        key is a key by string, or one of the predefined HKEY_* constants.

        value_name is a string that names the subkey with which the value is associated.
        if value_name is None or '' it will write to the default value of the Key

        * Remark : this is the Value what is shown in Regedit as "(Standard)" or "(Default)" - it is usually not set.
        Nethertheless, even if the Default Value is not set, winreg.QueryValue will deliver ''

        value_type is an integer that specifies the type of the data.
        if value_type is not given, it will be set automatically to an appropriate winreg.REG_TYPE:

        ==================  =============  =================
        value type          REG_TYPE       REG_TYPE(integer)
        ==================  =============  =================
        None                REG_NONE        0
        str                 REG_SZ          1
        List[str]           REG_MULTI_SZ    7
        bytes               REG_BINARY      3
        int                 REG_DWORD       4
        everything else     REG_BINARY      3
        ==================  =============  =================

        value is the new value.

        Value lengths are limited by available memory. Long values (more than 2048 bytes)
        should be stored as files with the filenames stored in the configuration registry. This helps the registry perform efficiently.
        Raises an auditing event winreg.SetValue with arguments key, sub_key, type, value.



        Registry Types
        --------------

        =========  ==============================  ====================== ==========================================================================
        type(int)  type name                       accepted python Types  Description
        =========  ==============================  ====================== ==========================================================================
        0          REG_NONE	                       None, bytes            No defined value type.
        1          REG_SZ	                       None, str              A null-terminated string.
        2          REG_EXPAND_SZ	               None, str              Null-terminated string containing references to
                                                                          environment variables (%PATH%).
                                                                          (Python handles this termination automatically.)
        3          REG_BINARY	                   None, bytes            Binary data in any form.
        4          REG_DWORD	                   None, int              A 32-bit number.
        4          REG_DWORD_LITTLE_ENDIAN	       None, int              A 32-bit number in little-endian format.
        5          REG_DWORD_BIG_ENDIAN	           None, bytes            A 32-bit number in big-endian format.
        6          REG_LINK	                       None, bytes            A Unicode symbolic link.
        7          REG_MULTI_SZ	                   None, List[str]        A sequence of null-terminated strings, terminated by two null characters.
        8          REG_RESOURCE_LIST	           None, bytes            A device-driver resource list.
        9          REG_FULL_RESOURCE_DESCRIPTOR    None, bytes            A hardware setting.
        10         REG_RESOURCE_REQUIREMENTS_LIST  None, bytes            A hardware resource list.
        11         REG_QWORD                       None, bytes            A 64 - bit number.
        11         REG_QWORD_LITTLE_ENDIAN         None, bytes            A 64 - bit number in little - endian format.Equivalent to REG_QWORD.
        =========  ==============================  ====================== ==========================================================================
        - all other integers for REG_TYPE are accepted, and written to the registry.
          The value is handled as binary.
          by that way You would be able to encode data in the REG_TYPE for stealth data not easy to spot - who would expect it.


        >>> # Setup
        >>> registry = Registry()
        >>> registry.create_key(r'HKCU\\Software\\lib_registry_test', parents=True)
        <...PyHKEY object at ...>

        >>> registry.set_value(key=r'HKCU\\Software\\lib_registry_test', value_name='test_name', value='test_string', value_type=winreg.REG_SZ)
        >>> assert registry.get_value_ex(key=r'HKCU\\Software\\lib_registry_test', value_name='test_name') == ('test_string', 1)

        >>> # Teardown
        >>> registry.delete_key(r'HKCU\\Software\\lib_registry_test', missing_ok=True, delete_subkeys=True)

        """

        if value_name is None:
            value_name = ''

        if value_type is None:
            if value is None:
                value_type = winreg.REG_NONE
            elif isinstance(value, int):
                value_type = winreg.REG_DWORD
            elif isinstance(value, list):
                value_type = winreg.REG_MULTI_SZ
            elif isinstance(value, str):
                value_type = winreg.REG_SZ
            else:
                value_type = winreg.REG_BINARY

        key_handle = self._open_key(key, access=winreg.KEY_ALL_ACCESS)
        try:
            winreg.SetValueEx(key_handle, value_name, 0, value_type, value)     # type: ignore
        except Exception:       # ToDo: narrow down
            # different Errors can occur here :
            # TypeError: Objects of type 'str' can not be used as binary registry values (if try to write string to REG_NONE type)
            # others to explore ...
            key_str = get_key_as_string(key)
            value_type_str = get_value_type_as_string(value_type)
            raise RegistryValueWriteError(f'can not write data to key "{key_str}", value_name "{value_name}", value_type "{value_type_str}"')

    def delete_value(self, key: Union[str, int], value_name: Optional[str]) -> None:
        """
        deletes the value field of an open registry key, if value_name == '' or 'None',
        then delete the default value of the key


        Parameter
        ---------

        key
            by string, or one of the predefined HKEY_* constants.

        value_name
            a string that names the subkey with which the value is associated.
            if value_name is None or '' it will delete the default value of the Key*

        * Remark : this is the Value what is shown in Regedit as "(Standard)" or "(Default)" - it is usually not set.
        Nethertheless, even if the Default Value is not set, winreg.QueryValue will deliver ''


        Examples
        --------

        >>> # Setup
        >>> registry = Registry()
        >>> key_handle = registry.create_key(r'HKCU\\Software\\lib_registry_test', parents=True)
        >>> registry.set_value(key=r'HKCU\\Software\\lib_registry_test', value_name='test_name', value='test_string', value_type=winreg.REG_SZ)
        >>> assert registry.get_value_ex(key=r'HKCU\\Software\\lib_registry_test', value_name='test_name') == ('test_string', 1)
        >>> registry.delete_value(key=r'HKCU\\Software\\lib_registry_test', value_name='test_name')
        >>> registry.get_value_ex(key=r'HKCU\\Software\\lib_registry_test', value_name='test_name')
        Traceback (most recent call last):
            ...
        lib_registry.RegistryValueNotFoundError: value "test_name" not found in key "HKEY_CURRENT_USER..."

        >>> # Teardown
        >>> registry.delete_key(r'HKCU\\Software\\lib_registry_test', missing_ok=True, delete_subkeys=True)

        """

        if value_name is None:
            value_name = ''

        key_handle = self._open_key(key, access=winreg.KEY_ALL_ACCESS)
        try:
            winreg.DeleteValue(key_handle, value_name)
        except FileNotFoundError as e:
            if hasattr(e, 'winerror') and e.winerror == 2:  # type: ignore
                key_str = get_key_as_string(key)
                raise RegistryValueDeleteError(f'can not delete value "{value_name}" from key "{key_str}"')
            else:
                raise e


def get_value_type_as_string(value_type: int) -> str:
    """
    Return the value type as string

    >>> get_value_type_as_string(winreg.REG_SZ)
    'REG_SZ'
    """
    value_type_as_string = reg_type_names_hashed_by_int[value_type]
    return value_type_as_string


def get_key_as_string(key: Union[str, int], sub_key: str = '') -> str:
    """
    >>> # DONE #3
    >>> get_key_as_string(winreg.HKEY_LOCAL_MACHINE)
    'HKEY_LOCAL_MACHINE'
    >>> get_key_as_string(winreg.HKEY_LOCAL_MACHINE, sub_key=r'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList')
    'HKEY_LOCAL_MACHINE\\\\SOFTWARE\\\\Microsoft\\\\Windows NT\\\\CurrentVersion\\\\ProfileList'

    >>> get_key_as_string(r'hklm\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList')
    'HKEY_LOCAL_MACHINE\\\\SOFTWARE\\\\Microsoft\\\\Windows NT\\\\CurrentVersion\\\\ProfileList'
    """
    hive_key, sub_key = resolve_key(key, sub_key)
    key_as_string = helpers.strip_backslashes(hive_names_hashed_by_int[hive_key] + '\\' + sub_key)
    return key_as_string


def resolve_key(key: Union[str, int], sub_key: str = '') -> Tuple[int, str]:
    """
    Returns hive_key and sub_key relative to the hive_key

    >>> # DONE #3
    >>> resolve_key(winreg.HKEY_LOCAL_MACHINE)
    (18446744071562067970, '')
    >>> resolve_key(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\\Microsoft')
    (18446744071562067970, 'SOFTWARE\\\\Microsoft')
    >>> resolve_key(r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft')
    (18446744071562067970, 'SOFTWARE\\\\Microsoft')
    >>> resolve_key(r'HKLM\\SOFTWARE\\Microsoft')
    (18446744071562067970, 'SOFTWARE\\\\Microsoft')
    >>> resolve_key(r'hklm\\SOFTWARE\\Microsoft')
    (18446744071562067970, 'SOFTWARE\\\\Microsoft')

    >>> # test invalid hive as string
    >>> resolve_key(r'HKX\\SOFTWARE\\Microsoft')
    Traceback (most recent call last):
    ...
    lib_registry.RegistryHKeyError: invalid KEY: "HKX"

    >>> # test invalid hive as int
    >>> resolve_key(42, r'SOFTWARE\\Microsoft')
    Traceback (most recent call last):
    ...
    lib_registry.RegistryHKeyError: invalid HIVE KEY: "42"

    """

    if isinstance(key, str):
        hive_key = get_hkey_int(key)
        key_without_hive = remove_hive_from_key_str_if_present(key)
        if sub_key:
            sub_key = '\\'.join([key_without_hive, sub_key])
        else:
            sub_key = key_without_hive
    else:
        hive_key = key
        if hive_key not in hive_names_hashed_by_int:
            raise RegistryHKeyError(f'invalid HIVE KEY: "{hive_key}"')
    return hive_key, sub_key


def get_hkey_int(key_name: str) -> int:
    """
    gets the root hive key from a key_name, containing short or long form, not case sensitive

    >>> # DONE #3
    >>> assert get_hkey_int(r'HKLM\\something') == winreg.HKEY_LOCAL_MACHINE
    >>> assert get_hkey_int(r'hklm\\something') == winreg.HKEY_LOCAL_MACHINE
    >>> assert get_hkey_int(r'HKEY_LOCAL_MACHINE\\something') == winreg.HKEY_LOCAL_MACHINE
    >>> assert get_hkey_int(r'hkey_local_machine\\something') == winreg.HKEY_LOCAL_MACHINE
    >>> get_hkey_int(r'Something\\else')
    Traceback (most recent call last):
    ...
    lib_registry.RegistryHKeyError: invalid KEY: "Something..."

    """
    main_key_name = helpers.get_first_part_of_the_key(key_name)
    main_key_name_lower = main_key_name.lower()
    if main_key_name_lower in main_key_hashed_by_name:
        main_key = int(main_key_hashed_by_name[main_key_name_lower])
        return main_key
    else:
        raise RegistryHKeyError(f'invalid KEY: "{main_key_name}"')


def remove_hive_from_key_str_if_present(key_name: str) -> str:
    """
    >>> # DONE #3
    >>> remove_hive_from_key_str_if_present(r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft')
    'SOFTWARE\\\\Microsoft'
    >>> remove_hive_from_key_str_if_present(r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft')
    'SOFTWARE\\\\Microsoft'
    >>> remove_hive_from_key_str_if_present(r'hklm\\SOFTWARE\\Microsoft')
    'SOFTWARE\\\\Microsoft'
    >>> remove_hive_from_key_str_if_present(r'SOFTWARE\\Microsoft')
    'SOFTWARE\\\\Microsoft'
    """
    result = key_name
    key_part_one = key_name.split('\\')[0]
    if key_part_one.upper() in l_hive_names:
        result = helpers.strip_backslashes(key_name[len(key_part_one):])
    return result


if __name__ == '__main__':
    print('this is a library only, the executable is named lib_parameter_cli.py')
