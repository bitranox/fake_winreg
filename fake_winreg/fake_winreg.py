# STDLIB
from typing import Any, Callable, Dict, Tuple, TypeVar, Union, cast

# OWN
try:
    from .fake_registry import *
    from .set_fake_registry_testvalues import set_fake_test_registry_windows
except (ImportError, ModuleNotFoundError):                                      # pragma: no cover
    # imports for doctest
    from fake_registry import *                                                 # type: ignore  # pragma: no cover
    from set_fake_registry_testvalues import set_fake_test_registry_windows     # type: ignore  # pragma: no cover

F = TypeVar('F', bound=Callable[..., Any])


def check_for_kwargs(f: F) -> F:
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if kwargs:
            keys = ', '.join([key for key in kwargs.keys()])
            raise TypeError("{fn}() got some positional-only arguments passed as keyword arguments: '{keys}'".format(fn=f.__name__, keys=keys))
        return f(*args, **kwargs)
    return cast(F, wrapper)


class PyHKEY(object):
    """
    Registry Handle Objects
    This object wraps a Windows HKEY object, automatically closing it when the object is destroyed.
    To guarantee cleanup, you can call either the Close() method on the object, or the CloseKey() function.
    All registry functions in this module return one of these objects.

    # Not implemented features of the Original Object - its not hard, but I did not need it ATM:
    All registry functions in this module which accept a handle object also accept an integer, however, use of the handle object is encouraged.
    Handle objects provide semantics for __bool__() – thus
    if handle:
        print("Yes")
    will print Yes if the handle is currently valid (has not been closed or detached).

    The object also support comparison semantics, so handle objects will compare true if they both reference the same underlying Windows handle value.
    Handle objects can be converted to an integer (e.g., using the built-in int() function), in which case the underlying Windows handle value is returned.
    You can also use the Detach() method to return the integer handle, and also disconnect the Windows handle from the handle object.

    """
    KEY_READ = 131097  # Combines the STANDARD_RIGHTS_READ, KEY_QUERY_VALUE, KEY_ENUMERATE_SUB_KEYS, and KEY_NOTIFY values.

    def __init__(self, data: FakeRegistryKey, access: int = KEY_READ):
        self.data = data
        self.access = access


class FakeWinReg(object):
    # value Types
    REG_BINARY: int = 3                         # Binary data in any form.
    REG_DWORD: int = 4                          # 32 - bit number.
    REG_DWORD_LITTLE_ENDIAN: int = 4            # A 32 - bit number in little - endian format.Equivalent to REG_DWORD.
    REG_DWORD_BIG_ENDIAN: int = 5               # A 32 - bit number in big - endian format.
    REG_EXPAND_SZ: int = 2                      # Null - terminated string containing references to environment variables( % PATH %).
    REG_LINK: int = 6                           # A Unicode symbolic link.
    REG_MULTI_SZ: int = 7                       # A sequence of null - terminated strings, terminated by two null characters.
    REG_NONE: int = 0                           # No defined value type.
    REG_QWORD: int = 11                         # A 64 - bit number.
    REG_QWORD_LITTLE_ENDIAN: int = 11           # A 64 - bit number in little - endian format.Equivalent to REG_QWORD.
    REG_RESOURCE_LIST: int = 8                  # A device - driver resource list.
    REG_FULL_RESOURCE_DESCRIPTOR: int = 9       # A hardware setting.
    REG_RESOURCE_REQUIREMENTS_LIST: int = 10    # A hardware resource list.
    REG_SZ: int = 1                             # A null-terminated string.

    # predefined keys
    HKEYType = PyHKEY
    HKEY_CLASSES_ROOT: int = 18446744071562067968
    HKEY_CURRENT_CONFIG: int = 18446744071562067973
    HKEY_CURRENT_USER: int = 18446744071562067969
    HKEY_DYN_DATA: int = 18446744071562067974
    HKEY_LOCAL_MACHINE: int = 18446744071562067970
    HKEY_PERFORMANCE_DATA: int = 18446744071562067972
    HKEY_USERS: int = 18446744071562067971

    # access rights
    # Combines the STANDARD_RIGHTS_REQUIRED, KEY_QUERY_VALUE, KEY_SET_VALUE, KEY_CREATE_SUB_KEY,
    # KEY_ENUMERATE_SUB_KEYS, KEY_NOTIFY, and KEY_CREATE_LINK access rights.
    KEY_ALL_ACCESS = 983103
    KEY_WRITE = 131078  # Combines the STANDARD_RIGHTS_WRITE, KEY_SET_VALUE, and KEY_CREATE_SUB_KEY access rights.
    KEY_READ = 131097  # Combines the STANDARD_RIGHTS_READ, KEY_QUERY_VALUE, KEY_ENUMERATE_SUB_KEYS, and KEY_NOTIFY values.
    KEY_EXECUTE = 131097  # Equivalent to KEY_READ.
    KEY_QUERY_VALUE = 1  # Required to query the values of a registry key.
    KEY_SET_VALUE = 2  # Required to create, delete, or set a registry value.
    KEY_CREATE_SUB_KEY = 4  # Required to create a subkey of a registry key.
    KEY_ENUMERATE_SUB_KEYS = 8  # Required to enumerate the subkeys of a registry key.
    KEY_NOTIFY = 16  # Required to request change notifications for a registry key or for subkeys of a registry key.
    KEY_CREATE_LINK = 32  # Reserved for system use.
    KEY_WOW64_64KEY = 256  # Indicates that an application on 64-bit Windows should operate on the 64-bit registry view. NOT IMPLEMENTED
    KEY_WOW64_32KEY = 512  # Indicates that an application on 64-bit Windows should operate on the 32-bit registry view. NOT IMPLEMENTED

    def __init__(self, fake_registry: FakeRegistry) -> None:
        self.fake_registry = fake_registry
        # the list of the open handles - hashed by full_key_path
        self.py_hkey_handles: Dict[str, PyHKEY] = dict()

    @check_for_kwargs
    def CloseKey(self, hkey: int) -> None:
        """
        Closes a previously opened registry key. The hkey argument specifies a previously opened hive key.

        >>> # Setup
        >>> fake_registry = set_fake_test_registry_windows()
        >>> winreg = FakeWinReg(fake_registry)
        >>> # Test
        >>> hive_key = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
        >>> winreg.CloseKey(winreg.HKEY_LOCAL_MACHINE)

        >>> # must not accept keyword parameters
        >>> hive_key = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
        >>> winreg.CloseKey(hkey=winreg.HKEY_LOCAL_MACHINE)  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        Traceback (most recent call last):
            ...
        TypeError: CloseKey() got some positional-only arguments passed as keyword arguments: 'hkey'

        """
        # we could recursively delete all the handles in self.py_hkey_handles by walking the fake registry keys - atm we dont bother
        # or we can get the hive name and delete all self.py_hkey_handles beginning with hive name
        # tha objects are destroyed anyway when we close fake_winreg object, so we dont bother
        pass

    @check_for_kwargs
    def ConnectRegistry(self, computer_name: Union[None, str], key: int) -> PyHKEY:
        """
        Establishes a connection to a predefined registry handle on another computer, and returns a handle object.
        computer_name is the name of the remote computer, of the form r"\\computername". If None, the local computer is used.  (NOT IMPLEMENTED)
        key is the predefined handle to connect to.
        The return value is the handle of the opened key. If the function fails, an OSError exception is raised.
        Raises an auditing event winreg.ConnectRegistry with arguments computer_name, key.


        >>> # Setup
        >>> fake_registry = set_fake_test_registry_windows()
        >>> winreg = FakeWinReg(fake_registry)

        >>> # Connect
        >>> winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        <...PyHKEY object at ...>

        >>> # must not accept keyword parameters
        >>> winreg.ConnectRegistry(computer_name=None, key=winreg.HKEY_LOCAL_MACHINE)  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        Traceback (most recent call last):
            ...
        TypeError: ConnectRegistry() got some positional-only arguments passed as keyword arguments: 'computer_name, key'

        """
        if computer_name:
            raise NotImplementedError('we dont support to connect to remote computers on fake_winreg')
        fake_reg_handle = self.fake_registry.hive[key]
        reg_handle = PyHKEY(data=fake_reg_handle)
        reg_handle = self.add_handle_to_hash_list_or_return_already_existing_handle(reg_handle)
        return reg_handle

    @check_for_kwargs
    def CreateKey(self, key: Union[PyHKEY, int], sub_key: Union[str, None]) -> PyHKEY:
        """
        Creates or opens the specified key, returning a handle object.
        key is an already open key, or one of the predefined HKEY_* constants.
        sub_key is a string that names the key this method opens or creates.
        If key is one of the predefined keys, sub_key may be None. In that case,
        the handle returned is the same key handle passed in to the function.
        If the key already exists, this function opens the existing key.
        The return value is the handle of the opened key. If the function fails, an OSError exception is raised.
        The sub_key can contain a directory structure like r'Software\\xxx\\yyy' - all the parents to yyy will be created

        >>> # Setup
        >>> fake_registry = set_fake_test_registry_windows()
        >>> winreg = FakeWinReg(fake_registry)

        >>> # Connect
        >>> reg_handle = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)

        >>> # create key
        >>> reg_handle_created = winreg.CreateKey(reg_handle, r'SOFTWARE\\xxxx\\yyyy')

        >>> # create an existing key - we get the same handle back
        >>> reg_handle_existing = winreg.CreateKey(reg_handle, r'SOFTWARE\\xxxx\\yyyy')
        >>> assert reg_handle_existing == reg_handle_created

        >>> # open the new key - should be again the same handle :
        >>> # reg_handle_open = winreg.OpenKey(reg_handle, r'SOFTWARE\\xxxx\\yyyy')
        >>> # assert reg_handle_existing == reg_handle_created == reg_handle_open

        >>> # Teardown
        >>> winreg.DeleteKey(reg_handle, r'SOFTWARE\\xxxx\\yyyy')
        >>> winreg.DeleteKey(reg_handle, r'SOFTWARE\\xxxx')

        """
        if not sub_key:
            raise OSError('[WinError 1010] The configuration registry key is invalid.')

        reg_handle = self._resolve_key(key)
        access = reg_handle.access
        fake_reg_key = set_fake_reg_key(reg_handle.data, sub_key=sub_key)
        reg_handle = PyHKEY(fake_reg_key, access=access)
        reg_handle = self.add_handle_to_hash_list_or_return_already_existing_handle(reg_handle)
        return reg_handle

    @check_for_kwargs
    def DeleteKey(self, key: Union[PyHKEY, int], sub_key: str) -> None:
        """
        Deletes the specified key.
        key is an already open key, or one of the predefined HKEY_* constants.
        sub_key is a string that must be a subkey of the key identified by the key parameter or ''.
        This value must not be None, and the key may not have subkeys.
        This method can not delete keys with subkeys.
        If the method succeeds, the entire key, including all of its values, is removed.


        >>> # Setup
        >>> fake_registry = set_fake_test_registry_windows()
        >>> winreg = FakeWinReg(fake_registry)
        >>> reg_handle = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
        >>> reg_handle_created = winreg.CreateKey(reg_handle, r'SOFTWARE\\xxxx\\yyyy\\zzz')

        >>> # Delete key without subkeys
        >>> assert r'HKEY_CURRENT_USER\\SOFTWARE\\xxxx\\yyyy\\zzz' in winreg.py_hkey_handles
        >>> winreg.DeleteKey(reg_handle, r'SOFTWARE\\xxxx\\yyyy\\zzz')
        >>> assert r'HKEY_CURRENT_USER\\SOFTWARE\\xxxx\\yyyy\\zzz' not in winreg.py_hkey_handles

        >>> # try to delete non existing key (it was deleted before)
        >>> winreg.DeleteKey(reg_handle, r'SOFTWARE\\xxxx\\yyyy\\zzz')  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        Traceback (most recent call last):
            ...
        FileNotFoundError: [WinError 2] The system cannot find the file specified

        >>> # try to delete key with subkey
        >>> winreg.DeleteKey(reg_handle, r'SOFTWARE\\xxxx')  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        Traceback (most recent call last):
            ...
        PermissionError: [WinError 5] Access is denied

        >>> # try to delete key with subkey = None
        >>> winreg.DeleteKey(reg_handle, None)  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        Traceback (most recent call last):
            ...
        TypeError: DeleteKey() argument 2 must be str, not None

        >>> # subkey = '' is allowed here
        >>> reg_handle_sub = winreg.OpenKey(reg_handle, r'SOFTWARE\\xxxx\\yyyy')
        >>> winreg.DeleteKey(reg_handle_sub, '')

        >>> # Teardown
        >>> winreg.DeleteKey(reg_handle, r'SOFTWARE\\xxxx')

        """
        if not isinstance(sub_key, str):
            raise TypeError('DeleteKey() argument 2 must be str, not None')

        sub_key = str(sub_key)
        reg_handle = self._resolve_key(key)
        try:
            fake_reg_key = get_fake_reg_key(fake_reg_key=reg_handle.data, sub_key=sub_key)
        except FileNotFoundError:
            raise FileNotFoundError('[WinError 2] The system cannot find the file specified')

        if fake_reg_key.subkeys:
            raise PermissionError('[WinError 5] Access is denied')

        full_key_path = fake_reg_key.full_key
        sub_key = str(full_key_path.rsplit('\\', 1)[1])
        fake_parent_key = fake_reg_key.parent_fake_registry_key
        del fake_parent_key.subkeys[sub_key]     # delete the subkey
        if full_key_path in self.py_hkey_handles:
            del self.py_hkey_handles[full_key_path]  # delete the handle from the dict, if any

    @check_for_kwargs
    def DeleteKeyEx(self, key: Union[PyHKEY, int], sub_key: str, access: int = KEY_WOW64_64KEY, reserved: int = 0) -> None:
        """
        Deletes the specified key.

        Note The DeleteKeyEx() function is implemented with the RegDeleteKeyEx Windows API function,
        which is specific to 64-bit versions of Windows. See the RegDeleteKeyEx documentation.

        key is an already open key, or one of the predefined HKEY_* constants.
        sub_key is a string that must be a subkey of the key identified by the key parameter.
        This value must not be None, and the key may not have subkeys.

        reserved is a reserved integer, and must be zero. The default is zero.
        access is an integer that specifies an access mask that describes the desired security
        access for the key. Default is KEY_WOW64_64KEY. See Access Rights for other allowed values. (NOT IMPLEMENTED)

        This method can not delete keys with subkeys.

        If the method succeeds, the entire key, including all of its values, is removed.
        If the method fails, an OSError exception is raised.

        On unsupported Windows versions, NotImplementedError is raised.
        Raises an auditing event winreg.DeleteKey with arguments key, sub_key, access. (NOT IMPLEMENTED)

        >>> # Setup
        >>> fake_registry = set_fake_test_registry_windows()
        >>> winreg = FakeWinReg(fake_registry)
        >>> reg_handle = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
        >>> reg_handle_created = winreg.CreateKey(reg_handle, r'SOFTWARE\\xxxx\\yyyy\\zzz')

        >>> # Delete key without subkeys
        >>> assert r'HKEY_CURRENT_USER\\SOFTWARE\\xxxx\\yyyy\\zzz' in winreg.py_hkey_handles
        >>> winreg.DeleteKeyEx(reg_handle, r'SOFTWARE\\xxxx\\yyyy\\zzz')
        >>> assert r'HKEY_CURRENT_USER\\SOFTWARE\\xxxx\\yyyy\\zzz' not in winreg.py_hkey_handles

        >>> # try to delete non existing key (it was deleted before)
        >>> winreg.DeleteKeyEx(reg_handle, r'SOFTWARE\\xxxx\\yyyy\\zzz')  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        Traceback (most recent call last):
            ...
        FileNotFoundError: [WinError 2] The system cannot find the file specified

        >>> # try to delete key with subkey
        >>> winreg.DeleteKeyEx(reg_handle, r'SOFTWARE\\xxxx')  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        Traceback (most recent call last):
            ...
        PermissionError: [WinError 5] Access is denied

        >>> # try to delete key with subkey = None
        >>> winreg.DeleteKeyEx(reg_handle, None)  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        Traceback (most recent call last):
            ...
        TypeError: DeleteKey() argument 2 must be str, not None

        >>> # try to delete key with access = KEY_WOW64_32KEY
        >>> winreg.DeleteKeyEx(reg_handle, r'SOFTWARE\\xxxx\\yyyy', KEY_WOW64_32KEY)  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        Traceback (most recent call last):
            ...
        NotImplementedError: we only support KEY_WOW64_64KEY

        >>> # Teardown
        >>> winreg.DeleteKeyEx(reg_handle, r'SOFTWARE\\xxxx\\yyyy')
        >>> winreg.DeleteKeyEx(reg_handle, r'SOFTWARE\\xxxx')

        """
        if access == KEY_WOW64_32KEY:
            raise NotImplementedError('we only support KEY_WOW64_64KEY')
        self.DeleteKey(key, sub_key)

    @check_for_kwargs
    def DeleteValue(self, key: Union[PyHKEY, int], value: str) -> None:
        """
        Removes a named value from a registry key.
        key is an already open key, or one of the predefined HKEY_* constants.
        value is a string that identifies the value to remove.
        Raises an auditing event winreg.DeleteValue with arguments key, value. (NOT IMPLEMENTED)

        >>> # Setup
        >>> fake_registry = set_fake_test_registry_windows()
        >>> winreg = FakeWinReg(fake_registry)
        >>> reg_handle = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
        >>> reg_key = winreg.OpenKey(reg_handle, r'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion')
        >>> # winreg.SetValueEx(reg_key, 'some_test', 0, winreg.REG_SZ, 'some_test_value')

        >>> # Delete Value
        >>> #winreg.DeleteValue(reg_key, 'some_test')

        >>> # Delete Non Existing Value
        >>> winreg.DeleteValue(reg_key, 'some_test')  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        Traceback (most recent call last):
            ...
        FileNotFoundError: [WinError 2] The system cannot find the file specified

        """
        reg_handle = self._resolve_key(key)
        try:
            del reg_handle.data.values[value]
        except KeyError:
            raise FileNotFoundError('[WinError 2] The system cannot find the file specified')

    @check_for_kwargs
    def EnumKey(self, key: Union[PyHKEY, int], index: int) -> str:
        """
        Enumerates subkeys of an open registry key, returning a string.
        key is an already open key, or one of the predefined HKEY_* constants.
        index is an integer that identifies the index of the key to retrieve.
        The function retrieves the name of one subkey each time it is called.
        It is typically called repeatedly until an OSError exception is raised,
        indicating, no more values are available.
        Raises an auditing event winreg.EnumKey with arguments key, index. (NOT IMPLEMENTED)

        >>> # Setup
        >>> fake_registry = set_fake_test_registry_windows()
        >>> winreg = FakeWinReg(fake_registry)
        >>> reg_handle = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)

        >>> # test get the first profile in the profile list
        >>> reg_handle_profile = winreg.OpenKey(reg_handle, r'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList')
        >>> assert isinstance(winreg.EnumKey(reg_handle_profile, 0), str)

        >>> # test out of index
        >>> winreg.EnumKey(reg_handle_profile, 100000000)  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        Traceback (most recent call last):
            ...
        OSError: [WinError 259] No more data is available

        """
        reg_handle = self._resolve_key(key)
        try:
            sub_key_str = list(reg_handle.data.subkeys.keys())[index]
            return sub_key_str
        except IndexError:
            raise OSError('[WinError 259] No more data is available')

    # named arguments are allowed here !
    def OpenKey(self, key: Union[PyHKEY, int], sub_key: Union[str, None], reserved: int = 0, access: int = KEY_READ) -> PyHKEY:
        """
        Opens the specified key, returning a handle object.
        key is an already open key, or one of the predefined HKEY_* constants.
        sub_key is a string that identifies the sub_key to open.
        reserved is a reserved integer, and must be zero. The default is zero.
        access is an integer that specifies an access mask that describes the desired security access for the key.
        Default is KEY_READ. See Access Rights for other allowed values.

        The result is a new handle to the specified key.
        If the key is not found, FileNotFoundError is raised
        If the function fails, OSError is raised.
        Raises an auditing event winreg.OpenKey with arguments key, sub_key, access.    # not implemented
        Raises an auditing event winreg.OpenKey/result with argument key.               # not implemented
        Changed in version 3.2: Allow the use of named arguments.
        Changed in version 3.3: See above.

        >>> # Setup
        >>> fake_registry = set_fake_test_registry_windows()
        >>> winreg = FakeWinReg(fake_registry)
        >>> reg_handle = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)

        >>> # Open Key
        >>> reg_key = winreg.OpenKey(reg_handle, r'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion')
        >>> assert reg_key.data.full_key == r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion'

        >>> # Open Key mit subkey=None
        >>> reg_open1 = winreg.OpenKey(reg_key, None)

        >>> # Open Key mit subkey=None
        >>> reg_open2 = winreg.OpenKey(reg_key, '')
        >>> assert reg_open1 == reg_open2

        >>> # Open non existing Key
        >>> winreg.OpenKey(reg_handle, r'SOFTWARE\\Microsoft\\Windows NT\\DoesNotExist')  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        Traceback (most recent call last):
            ...
        FileNotFoundError: [WinError 2] The system cannot find the file specified

        """
        if sub_key is None:
            sub_key = ''

        try:
            reg_handle = self._resolve_key(key)
            access = reg_handle.access
            reg_key = get_fake_reg_key(reg_handle.data, sub_key=sub_key)
            reg_handle = PyHKEY(reg_key, access=access)
            reg_handle = self.add_handle_to_hash_list_or_return_already_existing_handle(reg_handle)
            return reg_handle
        except FileNotFoundError:
            raise FileNotFoundError('[WinError 2] The system cannot find the file specified')

    # named arguments are allowed here !
    def OpenKeyEx(self, key: Union[PyHKEY, int], sub_key: str, reserved: int = 0, access: int = KEY_READ) -> PyHKEY:
        """
        Opens the specified key, returning a handle object.
        key is an already open key, or one of the predefined HKEY_* constants.
        sub_key is a string that identifies the sub_key to open.
        reserved is a reserved integer, and must be zero. The default is zero.
        access is an integer that specifies an access mask that describes the desired security access for the key.
        Default is KEY_READ. See Access Rights for other allowed values.

        The result is a new handle to the specified key.
        If the key is not found, FileNotFoundError is raised
        If the function fails, OSError is raised.
        Raises an auditing event winreg.OpenKey with arguments key, sub_key, access.    # not implemented
        Raises an auditing event winreg.OpenKey/result with argument key.               # not implemented
        Changed in version 3.2: Allow the use of named arguments.
        Changed in version 3.3: See above.

        >>> # Setup
        >>> fake_registry = set_fake_test_registry_windows()
        >>> winreg = FakeWinReg(fake_registry)
        >>> reg_handle = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)

        >>> # Open Key
        >>> reg_key = winreg.OpenKeyEx(reg_handle, r'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion')
        >>> assert reg_key.data.full_key == r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion'

        >>> # Open non existing Key
        >>> winreg.OpenKeyEx(reg_handle, r'SOFTWARE\\Microsoft\\Windows NT\\DoesNotExist')  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        Traceback (most recent call last):
            ...
        FileNotFoundError: [WinError 2] The system cannot find the file specified

        """
        key_handle = self.OpenKey(key, sub_key, reserved, access)
        return key_handle

    @check_for_kwargs
    def QueryInfoKey(self, key: Union[PyHKEY, int]) -> Tuple[int, int, int]:
        """
        Returns information about a key, as a tuple.
        key is an already open key, or one of the predefined HKEY_* constants.
        The result is a tuple of 3 items:
        Index, Meaning
                0       An integer giving the number of sub keys this key has.
                1       An integer giving the number of values this key has.
                2       An integer giving when the key was last modified (if available) as 100’s of nanoseconds since Jan 1, 1601.
        Raises an auditing event winreg.QueryInfoKey with argument key. (NOT IMPLEMENTED)

        >>> # Setup
        >>> fake_registry = set_fake_test_registry_windows()
        >>> winreg = FakeWinReg(fake_registry)
        >>> reg_handle = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)

        >>> # Open Key
        >>> reg_key = winreg.OpenKeyEx(reg_handle, r'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion')

        >>> new_reg_key_without_values = winreg.CreateKey(reg_key, 'test_without_values')
        >>> new_reg_key_with_subkeys_and_values = winreg.CreateKey(reg_key, 'test_with_subkeys_and_values')
        >>> winreg.SetValueEx(new_reg_key_with_subkeys_and_values, 'test_value_name', 0, REG_SZ, 'test_value')
        >>> new_reg_key_with_subkeys_subkey = winreg.CreateKey(new_reg_key_with_subkeys_and_values, 'subkey_of_test_with_subkeys')

        >>> # Test
        >>> winreg.QueryInfoKey(new_reg_key_without_values)  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        (0, 0, ...)
        >>> winreg.QueryInfoKey(new_reg_key_with_subkeys_and_values)  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        (1, 1, ...)

        >>> # Teardown
        >>> winreg.DeleteKey(reg_key, 'test_without_values')
        >>> winreg.DeleteKey(new_reg_key_with_subkeys_and_values, 'subkey_of_test_with_subkeys')
        >>> winreg.DeleteKey(reg_key, 'test_with_subkeys_and_values')
        """
        reg_handle = self._resolve_key(key)
        n_subkeys = len(reg_handle.data.subkeys)
        n_values = len(reg_handle.data.values)
        last_modified_nanoseconds = reg_handle.data.last_modified_ns        # 100’s of nanoseconds since Jan 1, 1601. / 1.Jan.1970 diff = 11644473600 * 1E9
        return n_subkeys, n_values, last_modified_nanoseconds

    @check_for_kwargs
    def QueryValue(self, key: Union[PyHKEY, int], sub_key: Union[str, None]) -> str:
        """
        Retrieves the unnamed value for a key, as a string.
        key is an already open key, or one of the predefined HKEY_* constants.
        sub_key is a string that holds the name of the subkey with which the value is associated.
        If this parameter is None or empty, the function retrieves the value set by the SetValue()
        method for the key identified by key.
        Values in the registry have name, type, and data components.
        This method retrieves the data for a key’s first value that has a NULL name.
        But the underlying API call doesn’t return the type, so always use QueryValueEx() if possible.

        * Remark : this is the Value what is shown in Regedit as "(Standard)" or "(Default)" - it does not have a value name.
        it is also not received with Enumvalues and can only be string

        >>> # Setup
        >>> fake_registry = set_fake_test_registry_windows()
        >>> winreg = FakeWinReg(fake_registry)
        >>> reg_handle = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
        >>> reg_handle_created = winreg.CreateKey(reg_handle, r'SOFTWARE\\xxxx')

        >>> # read Default Value, which is ''
        >>> assert winreg.QueryValue(reg_handle, r'SOFTWARE\\xxxx') == ''

        >>> # sub key can be here None or empty !
        >>> assert winreg.QueryValue(reg_handle_created, '') == ''
        >>> assert winreg.QueryValue(reg_handle_created, None) == ''

        >>> winreg.SetValue(reg_handle, r'SOFTWARE\\xxxx', REG_SZ, 'test1')
        >>> winreg.SetValue(reg_handle, r'SOFTWARE\\xxxx', REG_SZ, 'test1')
        >>> assert winreg.QueryValue(reg_handle, r'SOFTWARE\\xxxx') == 'test1'

        >>> # Teardown
        >>> winreg.DeleteKey(reg_handle, r'SOFTWARE\\xxxx')

        """
        reg_handle = self._resolve_key(key)
        reg_handle = self.OpenKey(reg_handle, sub_key)
        default_value = reg_handle.data.default_value
        return default_value

    @check_for_kwargs
    def QueryValueEx(self, key: Union[PyHKEY, int], value_name: str) -> Tuple[Union[bytes, str, int], int]:
        """
        Retrieves the type and data for a specified value name associated with an open registry key.
        key is an already open key, or one of the predefined HKEY_* constants.
        value_name is a string indicating the value to query.
        The result is a tuple of 2 items:
        Index       Meaning
        0           The value of the registry item.
        1           An integer giving the registry type for this value (see table in docs for SetValueEx())
        Raises an auditing event winreg.QueryValue with arguments key, sub_key, value_name. (NOT Implemented)

        >>> # Setup
        >>> fake_registry = set_fake_test_registry_windows()
        >>> winreg = FakeWinReg(fake_registry)
        >>> reg_handle = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)

        >>> # Read the current Version
        >>> reg_key = winreg.OpenKey(reg_handle, r'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion')
        >>> assert winreg.QueryValueEx(reg_key, 'CurrentBuild') == ('18363', REG_SZ)
        """

        reg_handle = self._resolve_key(key)
        value = reg_handle.data.values[value_name].value
        value_type = reg_handle.data.values[value_name].value_type
        return value, value_type

    @check_for_kwargs
    def SetValue(self, key: Union[PyHKEY, int], sub_key: Union[str, None], type: int, value: str) -> None:
        """
        Associates a value with a specified key. (the Default Value of the Key, usually blank)
        key is an already open key, or one of the predefined HKEY_* constants.
        sub_key is a string that names the subkey with which the value is associated.
        type is an integer that specifies the type of the data. Currently this must be REG_SZ,
        meaning only strings are supported. Use the SetValueEx() function for support for other data types.
        value is a string that specifies the new value.
        If the key specified by the sub_key parameter does not exist, the SetValue function creates it.
        Value lengths are limited by available memory. Long values (more than 2048 bytes) should be stored
        as files with the filenames stored in the configuration registry. This helps the registry perform efficiently.
        The key identified by the key parameter must have been opened with KEY_SET_VALUE access.    (NOT IMPLEMENTED)
        Raises an auditing event winreg.SetValue with arguments key, sub_key, type, value.          (NOT IMPLEMENTED)

        * Remark : this is the Value what is shown in Regedit as "(Standard)" or "(Default)" - it does not have a value name.
        it is also not received with Enumvalues and can only be string

        >>> # Setup
        >>> fake_registry = set_fake_test_registry_windows()
        >>> winreg = FakeWinReg(fake_registry)
        >>> reg_handle = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
        >>> reg_handle_created = winreg.CreateKey(reg_handle, r'SOFTWARE\\xxxx')

        >>> # read Default Value, which is ''
        >>> assert winreg.QueryValue(reg_handle, r'SOFTWARE\\xxxx') == ''

        >>> # sub key can be ''
        >>> winreg.SetValue(reg_handle_created, '', REG_SZ, 'test1')
        >>> assert winreg.QueryValue(reg_handle, r'SOFTWARE\\xxxx') == 'test1'

        >>> # sub key can be None
        >>> winreg.SetValue(reg_handle_created, None, REG_SZ, 'test2')
        >>> assert winreg.QueryValue(reg_handle, r'SOFTWARE\\xxxx') == 'test2'

        >>> # use sub key
        >>> reg_handle_software = winreg.OpenKey(reg_handle, 'SOFTWARE')
        >>> winreg.SetValue(reg_handle_software, 'xxxx', REG_SZ, 'test3')
        >>> assert winreg.QueryValue(reg_handle, r'SOFTWARE\\xxxx') == 'test3'

        >>> # Tear Down
        >>> winreg.DeleteKey(reg_handle,r'SOFTWARE\\xxxx')

        """
        if type != REG_SZ:
            raise TypeError('type must be winreg.REG_SZ')

        reg_handle = self._resolve_key(key)
        access = reg_handle.access
        try:
            reg_handle = self.OpenKey(reg_handle, sub_key, 0, access=access)
        except FileNotFoundError:
            reg_handle = self.CreateKey(reg_handle, sub_key=sub_key)
            reg_handle = self.OpenKey(reg_handle, '', 0, access)
        reg_handle.data.default_value = value

    @check_for_kwargs
    def SetValueEx(self, key: Union[PyHKEY, int], value_name: str, reserved: int, type: int, value: Union[bytes, str, int]) -> None:
        """
        Stores data in the value field of an open registry key.
        key is an already open key, or one of the predefined HKEY_* constants.
        value_name is a string that names the subkey with which the value is associated.
        reserved can be anything – zero is always passed to the API.
        type is an integer that specifies the type of the data. See Value Types for the available types.
        value is a string that specifies the new value.
        This method can also set additional value and type information for the specified key.
        The key identified by the key parameter must have been opened with KEY_SET_VALUE access.    (NOT IMPLEMENTED))
        To open the key, use the CreateKey() or OpenKey() methods.
        Value lengths are limited by available memory. Long values (more than 2048 bytes)
        should be stored as files with the filenames stored in the configuration registry. This helps the registry perform efficiently.
        Raises an auditing event winreg.SetValue with arguments key, sub_key, type, value.          (NOT IMPLEMENTED)

        >>> # Setup
        >>> # Setup
        >>> fake_registry = set_fake_test_registry_windows()
        >>> winreg = FakeWinReg(fake_registry)
        >>> reg_handle = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
        >>> reg_key = winreg.OpenKey(reg_handle, r'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion')

        >>> # Test
        >>> winreg.SetValueEx(reg_key, 'some_test', 0, winreg.REG_SZ, 'some_test_value')
        >>> assert winreg.QueryValueEx(reg_key, 'some_test') == ('some_test_value', winreg.REG_SZ)

        >>> # Teardown
        >>> winreg.DeleteValue(reg_key, 'some_test')

        """
        reg_handle = self._resolve_key(key)
        set_fake_reg_value(reg_handle.data, sub_key='', value_name=value_name, value=value, value_type=type)

    def _resolve_key(self, key: Union[int, PyHKEY]) -> PyHKEY:
        """
        Returns the full path to the key and the access of the parent key

        >>> # Setup
        >>> fake_registry = set_fake_test_registry_windows()
        >>> winreg = FakeWinReg(fake_registry)

        >>> # Connect
        >>> reg_handle = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)

        >>> winreg._resolve_key(key=reg_handle).data.full_key
        'HKEY_CURRENT_USER'

        >>> winreg._resolve_key(key=winreg.HKEY_CURRENT_USER).data.full_key
        'HKEY_CURRENT_USER'

        """

        if isinstance(key, int):
            key_handle = PyHKEY(self.fake_registry.hive[key])
        else:
            key_handle = key
        return key_handle

    def add_handle_to_hash_list_or_return_already_existing_handle(self, reg_handle: PyHKEY) -> PyHKEY:
        if reg_handle.data.full_key in self.py_hkey_handles:
            reg_handle = self.py_hkey_handles[reg_handle.data.full_key]
        else:
            self.py_hkey_handles[reg_handle.data.full_key] = reg_handle
        return reg_handle
