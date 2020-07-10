# STDLIB
from typing import Any, Callable, Dict, Optional, Tuple, TypeVar, Union, cast

# OWN
try:
    from . import fake_reg
    from . import setup_fake_registry
except (ImportError, ModuleNotFoundError):                                      # pragma: no cover
    # imports for doctest
    import fake_reg                     # type: ignore  # pragma: no cover
    import setup_fake_registry          # type: ignore  # pragma: no cover

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

    def __init__(self, data: fake_reg.FakeRegistryKey, access: int = KEY_READ):
        self.data = data
        self.access = access

    @staticmethod
    def Close() -> None:    # noqa
        """
        Closes the underlying Windows handle.
        If the handle is already closed, no error is raised.
        """
        pass

    @staticmethod
    def Detach() -> int:  # noqa
        """
        Detaches the Windows handle from the handle object.
        The result is an integer that holds the value of the handle before it is detached.
        If the handle is already detached or closed, this will return zero.
        After calling this function, the handle is effectively invalidated,
        but the handle is not closed.
        You would call this function when you need the underlying Win32 handle
        to exist beyond the lifetime of the handle object.
        Raises an auditing event winreg.PyHKEY.Detach with argument key.
        """
        return 0


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

    def __init__(self, fake_registry: fake_reg.FakeRegistry) -> None:
        self.PyHKEY = PyHKEY
        self.fake_registry = fake_registry
        # the list of the open handles - hashed by full_key_path
        self.py_hkey_handles: Dict[str, PyHKEY] = dict()

    @check_for_kwargs
    def CloseKey(self, hkey: Union[int, PyHKEY]) -> None:      # noqa
        """
        Closes a previously opened registry key. The hkey argument specifies a previously opened hive key.

        >>> # Setup
        >>> f_registry = fake_reg.FakeRegistry()
        >>> discard = setup_fake_registry.set_minimal_windows_testvalues(f_registry)
        >>> winreg = FakeWinReg(f_registry)
        >>> # Test
        >>> hive_key = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
        >>> winreg.CloseKey(winreg.HKEY_LOCAL_MACHINE)

        >>> # must not accept keyword parameters
        >>> hive_key = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
        >>> winreg.CloseKey(hkey=winreg.HKEY_LOCAL_MACHINE)
        Traceback (most recent call last):
            ...
        TypeError: CloseKey() got some positional-only arguments passed as keyword arguments: 'hkey'

        """
        # we could recursively delete all the handles in self.py_hkey_handles by walking the fake registry keys - atm we dont bother
        # or we can get the hive name and delete all self.py_hkey_handles beginning with hive name
        # the objects are destroyed anyway when we close fake_winreg object, so we dont bother
        pass

    @check_for_kwargs
    def ConnectRegistry(self, computer_name: Union[None, str], key: int) -> PyHKEY:     # noqa
        """
        Establishes a connection to a predefined registry handle on another computer, and returns a handle object.
        computer_name : the name of the remote computer, of the form r"\\computername". If None, the local computer is used.  (NOT IMPLEMENTED)
        key: the predefined handle to connect to.
        The return value is the handle of the opened key. If the function fails, an OSError exception is raised.
        Raises an auditing event winreg.ConnectRegistry with arguments computer_name, key.


        >>> # Setup
        >>> f_registry = fake_reg.FakeRegistry()
        >>> discard = setup_fake_registry.set_minimal_windows_testvalues(f_registry)
        >>> winreg = FakeWinReg(f_registry)

        >>> # Connect
        >>> winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
        <...PyHKEY object at ...>

        >>> # Computername given
        >>> winreg.ConnectRegistry('test', winreg.HKEY_LOCAL_MACHINE)
        Traceback (most recent call last):
        ...
        FileNotFoundError: System error 53 has occurred. The network path was not found

        >>> # Invalid Handle
        >>> winreg.ConnectRegistry(None, 42)
        Traceback (most recent call last):
            ...
        OSError: [WinError 6] The handle is invalid

        >>> # must not accept keyword parameters
        >>> winreg.ConnectRegistry(computer_name=None, key=winreg.HKEY_LOCAL_MACHINE)
        Traceback (most recent call last):
            ...
        TypeError: ConnectRegistry() got some positional-only arguments passed as keyword arguments: 'computer_name, key'


        """
        if computer_name:
            raise FileNotFoundError('System error 53 has occurred. The network path was not found')
        try:
            fake_reg_handle = self.fake_registry.hive[key]
        except KeyError:
            error = OSError('[WinError 6] The handle is invalid')
            setattr(error, 'winerror', 6)
            raise error
        reg_handle = PyHKEY(data=fake_reg_handle)
        reg_handle = self.add_handle_to_hash_list_or_return_already_existing_handle(reg_handle)
        return reg_handle

    # @check_for_kwargs
    def CreateKey(self, key: Union[PyHKEY, int], sub_key: Union[str, None]) -> PyHKEY:      # noqa
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
        >>> f_registry = fake_reg.FakeRegistry()
        >>> discard = setup_fake_registry.set_minimal_windows_testvalues(f_registry)
        >>> winreg = FakeWinReg(f_registry)

        >>> # Connect
        >>> reg_handle = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)

        >>> # create key
        >>> key_handle_created = winreg.CreateKey(reg_handle, r'SOFTWARE\\xxxx\\yyyy')

        >>> # create an existing key - we get the same handle back
        >>> key_handle_existing = winreg.CreateKey(reg_handle, r'SOFTWARE\\xxxx\\yyyy')
        >>> assert key_handle_existing == key_handle_created

        >>> # provoke Error on empty subkey
        >>> key_handle_existing = winreg.CreateKey(reg_handle, r'')
        Traceback (most recent call last):
            ...
        OSError: [WinError 1010] The configuration registry key is invalid.

        >>> # Teardown
        >>> winreg.DeleteKey(reg_handle, r'SOFTWARE\\xxxx\\yyyy')
        >>> winreg.DeleteKey(reg_handle, r'SOFTWARE\\xxxx')

        """
        if not sub_key:
            error = OSError('[WinError 1010] The configuration registry key is invalid.')
            setattr(error, 'winerror', 1010)
            raise error

        key_handle = self._resolve_key(key)
        access = key_handle.access
        fake_reg_key = fake_reg.set_fake_reg_key(key_handle.data, sub_key=sub_key)
        key_handle = PyHKEY(fake_reg_key, access=access)
        key_handle = self.add_handle_to_hash_list_or_return_already_existing_handle(key_handle)
        return key_handle

    # @check_for_kwargs
    def DeleteKey(self, key: Union[PyHKEY, int], sub_key: str) -> None:         # noqa
        """
        Deletes the specified key.
        key is an already open key, or one of the predefined HKEY_* constants.
        sub_key is a string that must be a subkey of the key identified by the key parameter or ''.
        This value must not be None, and the key may not have subkeys.
        This method can not delete keys with subkeys.
        If the method succeeds, the entire key, including all of its values, is removed.

        >>> # Setup
        >>> f_registry = fake_reg.FakeRegistry()
        >>> discard = setup_fake_registry.set_minimal_windows_testvalues(f_registry)
        >>> winreg = FakeWinReg(f_registry)

        >>> reg_handle = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
        >>> key_handle_created = winreg.CreateKey(reg_handle, r'SOFTWARE\\xxxx\\yyyy\\zzz')

        >>> # Delete key without subkeys
        >>> assert r'HKEY_CURRENT_USER\\SOFTWARE\\xxxx\\yyyy\\zzz' in winreg.py_hkey_handles
        >>> winreg.DeleteKey(reg_handle, r'SOFTWARE\\xxxx\\yyyy\\zzz')
        >>> assert r'HKEY_CURRENT_USER\\SOFTWARE\\xxxx\\yyyy\\zzz' not in winreg.py_hkey_handles

        >>> # try to delete non existing key (it was deleted before)
        >>> winreg.DeleteKey(reg_handle, r'SOFTWARE\\xxxx\\yyyy\\zzz')
        Traceback (most recent call last):
            ...
        FileNotFoundError: [WinError 2] The system cannot find the file specified

        >>> # try to delete key with subkey
        >>> winreg.DeleteKey(reg_handle, r'SOFTWARE\\xxxx')
        Traceback (most recent call last):
            ...
        PermissionError: [WinError 5] Access is denied

        >>> # try to delete key with subkey = None
        >>> winreg.DeleteKey(reg_handle, None)          # noqa
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
        key_handle = self._resolve_key(key)
        try:
            fake_reg_key = fake_reg.get_fake_reg_key(fake_reg_key=key_handle.data, sub_key=sub_key)
        except FileNotFoundError:
            error = FileNotFoundError('[WinError 2] The system cannot find the file specified')
            setattr(error, 'winerror', 2)
            raise error

        if fake_reg_key.subkeys:
            permission_error = PermissionError('[WinError 5] Access is denied')
            setattr(permission_error, 'winerror', 5)
            raise permission_error

        full_key_path = fake_reg_key.full_key
        sub_key = str(full_key_path.rsplit('\\', 1)[1])
        fake_parent_key = fake_reg_key.parent_fake_registry_key
        # get rid of Optional[] mypy
        assert fake_parent_key is not None
        fake_parent_key.subkeys.pop(sub_key, None)          # delete the subkey
        self.py_hkey_handles.pop(full_key_path, None)       # delete the handle from the dict, if any

    @check_for_kwargs
    def DeleteKeyEx(self, key: Union[PyHKEY, int], sub_key: str, access: int = KEY_WOW64_64KEY, reserved: int = 0) -> None:     # noqa
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
        >>> f_registry = fake_reg.FakeRegistry()
        >>> discard = setup_fake_registry.set_minimal_windows_testvalues(f_registry)
        >>> winreg = FakeWinReg(f_registry)
        >>> reg_handle = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
        >>> key_handle_created = winreg.CreateKey(reg_handle, r'SOFTWARE\\xxxx\\yyyy\\zzz')

        >>> # Delete key without subkeys
        >>> assert r'HKEY_CURRENT_USER\\SOFTWARE\\xxxx\\yyyy\\zzz' in winreg.py_hkey_handles
        >>> winreg.DeleteKeyEx(reg_handle, r'SOFTWARE\\xxxx\\yyyy\\zzz')
        >>> assert r'HKEY_CURRENT_USER\\SOFTWARE\\xxxx\\yyyy\\zzz' not in winreg.py_hkey_handles

        >>> # try to delete non existing key (it was deleted before)
        >>> winreg.DeleteKeyEx(reg_handle, r'SOFTWARE\\xxxx\\yyyy\\zzz')
        Traceback (most recent call last):
            ...
        FileNotFoundError: [WinError 2] The system cannot find the file specified

        >>> # try to delete key with subkey
        >>> winreg.DeleteKeyEx(reg_handle, r'SOFTWARE\\xxxx')
        Traceback (most recent call last):
            ...
        PermissionError: [WinError 5] Access is denied

        >>> # try to delete key with subkey = None
        >>> winreg.DeleteKeyEx(reg_handle, None)            # noqa
        Traceback (most recent call last):
            ...
        TypeError: DeleteKey() argument 2 must be str, not None

        >>> # try to delete key with access = KEY_WOW64_32KEY
        >>> winreg.DeleteKeyEx(reg_handle, r'SOFTWARE\\xxxx\\yyyy', winreg.KEY_WOW64_32KEY)
        Traceback (most recent call last):
            ...
        NotImplementedError: we only support KEY_WOW64_64KEY

        >>> # Teardown
        >>> winreg.DeleteKeyEx(reg_handle, r'SOFTWARE\\xxxx\\yyyy')
        >>> winreg.DeleteKeyEx(reg_handle, r'SOFTWARE\\xxxx')

        """
        if access == FakeWinReg.KEY_WOW64_32KEY:
            raise NotImplementedError('we only support KEY_WOW64_64KEY')
        self.DeleteKey(key, sub_key)

    @check_for_kwargs
    def DeleteValue(self, key: Union[PyHKEY, int], value: Optional[str]) -> None:         # noqa
        """
        Removes a named value from a registry key.
        key is an already open key, or one of the predefined HKEY_* constants.
        value is a string that identifies the value to remove.
        if value is None, or '' it deletes the default Value of the Key
        Raises an auditing event winreg.DeleteValue with arguments key, value. (NOT IMPLEMENTED)

        >>> # Setup
        >>> f_registry = fake_reg.FakeRegistry()
        >>> discard = setup_fake_registry.set_minimal_windows_testvalues(f_registry)
        >>> winreg = FakeWinReg(f_registry)
        >>> reg_handle = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
        >>> key_handle = winreg.OpenKey(reg_handle, r'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion')
        >>> # winreg.SetValueEx(reg_key, 'some_test', 0, winreg.REG_SZ, 'some_test_value')

        >>> # Delete Non Existing Value
        >>> winreg.DeleteValue(key_handle, 'some_test')
        Traceback (most recent call last):
            ...
        FileNotFoundError: [WinError 2] The system cannot find the file specified

        """
        if value is None:
            value = ''

        key_handle = self._resolve_key(key)
        try:
            del key_handle.data.values[value]
        except KeyError:
            error = FileNotFoundError('[WinError 2] The system cannot find the file specified')
            setattr(error, 'winerror', 2)
            raise error

    @check_for_kwargs
    def EnumKey(self, key: Union[PyHKEY, int], index: int) -> str:              # noqa
        """
        Enumerates subkeys of an open registry key, returning a string.
        key is an already open key, or one of the predefined HKEY_* constants.
        index is an integer that identifies the index of the key to retrieve.
        The function retrieves the name of one subkey each time it is called.
        It is typically called repeatedly until an OSError exception is raised,
        indicating, no more values are available.
        Raises an auditing event winreg.EnumKey with arguments key, index. (NOT IMPLEMENTED)

        >>> # Setup
        >>> f_registry = fake_reg.FakeRegistry()
        >>> discard = setup_fake_registry.set_minimal_windows_testvalues(f_registry)
        >>> winreg = FakeWinReg(f_registry)
        >>> reg_handle = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)

        >>> # test get the first profile in the profile list
        >>> key_handle = winreg.OpenKey(reg_handle, r'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList')
        >>> assert isinstance(winreg.EnumKey(key_handle, 0), str)

        >>> # test out of index
        >>> winreg.EnumKey(key_handle, 100000000)
        Traceback (most recent call last):
            ...
        OSError: [WinError 259] No more data is available

        """
        key_handle = self._resolve_key(key)
        try:
            sub_key_str = list(key_handle.data.subkeys.keys())[index]
            return sub_key_str
        except IndexError:
            error = OSError('[WinError 259] No more data is available')
            setattr(error, 'winerror', 259)
            raise error

    @check_for_kwargs
    def EnumValue(self, key: Union[PyHKEY, int], index: int) -> Tuple[str, Union[None, bytes, str, int], int]:              # noqa
        """
        Enumerates values of an open registry key, returning a tuple.

        The result is a tuple of 3 items:
        Index       Meaning
        0           A string that identifies the value name
        1           An object that holds the value data, and whose type depends on the underlying registry type
        2           An integer giving the registry type for this value (see table in docs for SetValueEx())

        key is an already open key, or one of the predefined HKEY_* constants.
        index is an integer that identifies the index of the value to retrieve.
        The function retrieves the name of one subkey each time it is called.
        It is typically called repeatedly, until an OSError exception is raised, indicating no more values.
        Raises an auditing event winreg.EnumValue with arguments key, index. (NOT IMPLEMENTED)

        type(int)       type name                       Description
        =========================================================
        0               REG_NONE	                    No defined value type.
        1               REG_SZ	                        A null-terminated string.
        2               REG_EXPAND_SZ	                Null-terminated string containing references to environment variables (%PATH%).
                                                        (Python handles this termination automatically.)
        3               REG_BINARY	                    Binary data in any form.
        4               REG_DWORD	                    A 32-bit number.
        4               REG_DWORD_LITTLE_ENDIAN	        A 32-bit number in little-endian format.
        5               REG_DWORD_BIG_ENDIAN	        A 32-bit number in big-endian format.
        6               REG_LINK	                    A Unicode symbolic link.
        7               REG_MULTI_SZ	                A sequence of null-terminated strings, terminated by two null characters.
        8               REG_RESOURCE_LIST	            A device-driver resource list.
        9               REG_FULL_RESOURCE_DESCRIPTOR    A hardware setting.
        10              REG_RESOURCE_REQUIREMENTS_LIST  A hardware resource list.
        11              REG_QWORD                       A 64 - bit number.
        11              REG_QWORD_LITTLE_ENDIAN         A 64 - bit number in little - endian format.Equivalent to REG_QWORD.

        >>> # Setup
        >>> f_registry = fake_reg.FakeRegistry()
        >>> discard = setup_fake_registry.set_minimal_windows_testvalues(f_registry)
        >>> winreg = FakeWinReg(f_registry)
        >>> reg_handle = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)

        >>> # Read the current Version
        >>> key_handle = winreg.OpenKey(reg_handle, r'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion')
        >>> winreg.EnumValue(key_handle, 0)
        (...)

        >>> # test out of index
        >>> winreg.EnumValue(key_handle, 100000000)
        Traceback (most recent call last):
            ...
        OSError: [WinError 259] No more data is available

        """
        key_handle = self._resolve_key(key)
        try:
            value_name = list(key_handle.data.values.keys())[index]
            value_data = key_handle.data.values[value_name].value
            value_type = key_handle.data.values[value_name].value_type
            return value_name, value_data, value_type
        except IndexError:
            error = OSError('[WinError 259] No more data is available')
            setattr(error, 'winerror', 259)
            raise error

    # named arguments are allowed here !
    def OpenKey(self, key: Union[PyHKEY, int], sub_key: Union[str, None], reserved: int = 0, access: int = KEY_READ) -> PyHKEY:         # noqa
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
        >>> f_registry = fake_reg.FakeRegistry()
        >>> discard = setup_fake_registry.set_minimal_windows_testvalues(f_registry)
        >>> winreg = FakeWinReg(f_registry)
        >>> reg_handle = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)

        >>> # Open Key
        >>> key_handle = winreg.OpenKey(reg_handle, r'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion')
        >>> assert key_handle.data.full_key == r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion'

        >>> # Open Key mit subkey=None
        >>> reg_open1 = winreg.OpenKey(key_handle, None)

        >>> # Open Key mit subkey=''
        >>> reg_open2 = winreg.OpenKey(key_handle, '')

        >>> # Open the same kay again, but we get a different Handle
        >>> reg_open3 = winreg.OpenKey(key_handle, '')

        >>> assert reg_open2 != reg_open3

        >>> # Open non existing Key
        >>> winreg.OpenKey(reg_handle, r'SOFTWARE\\Microsoft\\Windows NT\\DoesNotExist')
        Traceback (most recent call last):
            ...
        FileNotFoundError: [WinError 2] The system cannot find the file specified

        """
        if sub_key is None:
            sub_key = ''

        try:
            key_handle = self._resolve_key(key)
            access = key_handle.access
            reg_key = fake_reg.get_fake_reg_key(key_handle.data, sub_key=sub_key)
            key_handle = PyHKEY(reg_key, access=access)
            # no - winreg gives a new handle, even if You open the same key twice
            # this is, because You can open it once with Read Access,
            # and a second time with different access rights
            # reg_handle = self.add_handle_to_hash_list_or_return_already_existing_handle(reg_handle)
            self.py_hkey_handles[key_handle.data.full_key] = key_handle
            return key_handle
        except FileNotFoundError:
            error = FileNotFoundError('[WinError 2] The system cannot find the file specified')
            setattr(error, 'winerror', 2)
            raise error

    # named arguments are allowed here !
    def OpenKeyEx(self, key: Union[PyHKEY, int], sub_key: str, reserved: int = 0, access: int = KEY_READ) -> PyHKEY:        # noqa
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
        >>> f_registry = fake_reg.FakeRegistry()
        >>> discard = setup_fake_registry.set_minimal_windows_testvalues(f_registry)
        >>> winreg = FakeWinReg(f_registry)
        >>> reg_handle = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)

        >>> # Open Key
        >>> key_handle = winreg.OpenKeyEx(reg_handle, r'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion')
        >>> assert key_handle.data.full_key == r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion'

        >>> # Open non existing Key
        >>> winreg.OpenKeyEx(reg_handle, r'SOFTWARE\\Microsoft\\Windows NT\\DoesNotExist')
        Traceback (most recent call last):
            ...
        FileNotFoundError: [WinError 2] The system cannot find the file specified

        """
        key_handle = self.OpenKey(key, sub_key, reserved, access)
        return key_handle

    @check_for_kwargs
    def QueryInfoKey(self, key: Union[PyHKEY, int]) -> Tuple[int, int, int]:            # noqa
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
        >>> f_registry = fake_reg.FakeRegistry()
        >>> discard = setup_fake_registry.set_minimal_windows_testvalues(f_registry)
        >>> winreg = FakeWinReg(f_registry)
        >>> reg_handle = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)

        >>> # Open Key
        >>> key_handle = winreg.OpenKeyEx(reg_handle, r'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion')

        >>> new_reg_key_without_values = winreg.CreateKey(key_handle, 'test_without_values')
        >>> new_reg_key_with_subkeys_and_values = winreg.CreateKey(key_handle, 'test_with_subkeys_and_values')
        >>> winreg.SetValueEx(new_reg_key_with_subkeys_and_values, 'test_value_name', 0, FakeWinReg.REG_SZ, 'test_value')
        >>> new_reg_key_with_subkeys_subkey = winreg.CreateKey(new_reg_key_with_subkeys_and_values, 'subkey_of_test_with_subkeys')

        >>> # Test
        >>> winreg.QueryInfoKey(new_reg_key_without_values)
        (0, 0, ...)
        >>> winreg.QueryInfoKey(new_reg_key_with_subkeys_and_values)
        (1, 1, ...)

        >>> # Teardown
        >>> winreg.DeleteKey(key_handle, 'test_without_values')
        >>> winreg.DeleteKey(new_reg_key_with_subkeys_and_values, 'subkey_of_test_with_subkeys')
        >>> winreg.DeleteKey(key_handle, 'test_with_subkeys_and_values')
        """
        reg_handle = self._resolve_key(key)
        n_subkeys = len(reg_handle.data.subkeys)
        n_values = len(reg_handle.data.values)
        last_modified_nanoseconds = reg_handle.data.last_modified_ns        # 100’s of nanoseconds since Jan 1, 1601. / 1.Jan.1970 diff = 11644473600 * 1E9
        return n_subkeys, n_values, last_modified_nanoseconds

    @check_for_kwargs
    def QueryValue(self, key: Union[PyHKEY, int], sub_key: Union[str, None]) -> str:        # noqa
        """
        Retrieves the unnamed value for a key, as a string.
        key is an already open key, or one of the predefined HKEY_* constants.
        sub_key is a string that holds the name of the subkey with which the value is associated.
        If this parameter is None or empty, the function retrieves the value set by the SetValue()
        method for the key identified by key.
        Values in the registry have name, type, and data components.
        This method retrieves the data for a key’s first value that has a NULL name.
        But the underlying API call doesn’t return the type, so always use QueryValueEx() if possible.

        * Remark : this is the Value what is shown in Regedit as "(Standard)" or "(Default)"
        it is usually not set. Nethertheless, even if the value is not set, QueryValue will deliver ''

        >>> # Setup
        >>> f_registry = fake_reg.FakeRegistry()
        >>> discard = setup_fake_registry.set_minimal_windows_testvalues(f_registry)
        >>> winreg = FakeWinReg(f_registry)
        >>> reg_handle = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
        >>> key_handle_created = winreg.CreateKey(reg_handle, r'SOFTWARE\\lib_registry_test')

        >>> # read Default Value, which is ''
        >>> assert winreg.QueryValue(reg_handle, r'SOFTWARE\\lib_registry_test') == ''

        >>> # sub key can be here None or empty !
        >>> assert winreg.QueryValue(key_handle_created, '') == ''
        >>> assert winreg.QueryValue(key_handle_created, None) == ''

        >>> # set and get default value
        >>> winreg.SetValueEx(key_handle_created, '', 0, FakeWinReg.REG_SZ, 'test1')
        >>> assert winreg.QueryValueEx(key_handle_created, '') == ('test1', 1)
        >>> assert winreg.QueryValue(reg_handle, r'SOFTWARE\\lib_registry_test') == 'test1'

        >>> # Teardown
        >>> winreg.DeleteKey(reg_handle, r'SOFTWARE\\lib_registry_test')

        """
        key_handle = self._resolve_key(key)
        key_handle = self.OpenKey(key_handle, sub_key)
        try:
            result = key_handle.data.values[''].value
            if not isinstance(result, str):
                error = OSError('[WinError 13] The data is invalid')
                setattr(error, 'winerror', 13)
                raise error
            isinstance(result, str)
            default_value = result
        except KeyError:
            default_value = ''

        return default_value

    @check_for_kwargs
    def QueryValueEx(self, key: Union[PyHKEY, int], value_name: Optional[str]) -> Tuple[Union[None, bytes, str, int], int]:     # noqa
        """
        Retrieves data and type for a specified value name associated with an open registry key.
        key is an already open key, or one of the predefined HKEY_* constants.
        value_name is a string indicating the value to query. If Value_name is '' or None,
        it queries the Default Value of the Key - this will Fail if the Default Value for the Key is not Present.
        But the Default Value might be set to "None" - then "None" will be returned.

        The result is a tuple of 2 items:
        Index       Meaning
        0           The value of the registry item.
        1           An integer giving the registry type for this value (see table in docs for SetValueEx())
        Raises an auditing event winreg.QueryValue with arguments key, sub_key, value_name. (NOT Implemented)

        type(int)       type name                       Description
        =========================================================
        0               REG_NONE	                    No defined value type.
        1               REG_SZ	                        A null-terminated string.
        2               REG_EXPAND_SZ	                Null-terminated string containing references to environment variables (%PATH%).
                                                        (Python handles this termination automatically.)
        3               REG_BINARY	                    Binary data in any form.
        4               REG_DWORD	                    A 32-bit number.
        4               REG_DWORD_LITTLE_ENDIAN	        A 32-bit number in little-endian format.
        5               REG_DWORD_BIG_ENDIAN	        A 32-bit number in big-endian format.
        6               REG_LINK	                    A Unicode symbolic link.
        7               REG_MULTI_SZ	                A sequence of null-terminated strings, terminated by two null characters.
        8               REG_RESOURCE_LIST	            A device-driver resource list.
        9               REG_FULL_RESOURCE_DESCRIPTOR    A hardware setting.
        10              REG_RESOURCE_REQUIREMENTS_LIST  A hardware resource list.
        11              REG_QWORD                       A 64 - bit number.
        11              REG_QWORD_LITTLE_ENDIAN         A 64 - bit number in little - endian format.Equivalent to REG_QWORD.

        >>> # Setup
        >>> f_registry = fake_reg.FakeRegistry()
        >>> discard = setup_fake_registry.set_minimal_windows_testvalues(f_registry)
        >>> winreg = FakeWinReg(f_registry)
        >>> reg_handle = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
        >>> key_handle = winreg.OpenKey(reg_handle, r'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion')

        >>> # Read the current Version
        >>> winreg.QueryValueEx(key_handle, 'CurrentBuild')
        ('...', 1)

        >>> # Attempt to read a non Existing Default Value
        >>> winreg.QueryValueEx(key_handle, '')
        Traceback (most recent call last):
            ...
        FileNotFoundError: [WinError 2] The system cannot find the file specified

        >>> winreg.QueryValueEx(key_handle, None)
        Traceback (most recent call last):
            ...
        FileNotFoundError: [WinError 2] The system cannot find the file specified

        >>> # Set a Default Value
        >>> winreg.SetValueEx(key_handle, '',0 , winreg.REG_SZ, 'test_default_value')
        >>> winreg.QueryValueEx(key_handle, '')
        ('test_default_value', 1)

        >>> # Delete a Default Value
        >>> winreg.DeleteValue(key_handle, None)

        """

        try:
            if value_name is None:
                value_name = ''
            key_handle = self._resolve_key(key)
            value = key_handle.data.values[value_name].value
            value_type = key_handle.data.values[value_name].value_type
            return value, value_type
        except KeyError:
            error = FileNotFoundError('[WinError 2] The system cannot find the file specified')
            setattr(error, 'winerror', 2)
            raise error

    @check_for_kwargs
    def SetValue(self, key: Union[PyHKEY, int], sub_key: Union[str, None], type: int, value: str) -> None:      # noqa
        """
        Associates a value with a specified key. (the Default Value of the Key, usually not set)
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

        * Remark : this is the Value what is shown in Regedit as "(Standard)" or "(Default)"
        it is usually not set. Nethertheless, even if the value is not set, QueryValue will deliver ''

        >>> # Done 4
        >>> # Setup
        >>> f_registry = fake_reg.FakeRegistry()
        >>> discard = setup_fake_registry.set_minimal_windows_testvalues(f_registry)
        >>> winreg = FakeWinReg(f_registry)
        >>> reg_handle = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
        >>> key_handle = winreg.CreateKey(reg_handle, r'SOFTWARE\\lib_registry_test')

        >>> # read Default Value, which is ''
        >>> assert winreg.QueryValue(reg_handle, r'SOFTWARE\\lib_registry_test') == ''

        >>> # sub key can be ''
        >>> winreg.SetValue(key_handle, '', FakeWinReg.REG_SZ, 'test1')
        >>> assert winreg.QueryValue(reg_handle, r'SOFTWARE\\lib_registry_test') == 'test1'

        >>> # sub key can be None
        >>> winreg.SetValue(key_handle, None, FakeWinReg.REG_SZ, 'test2')
        >>> assert winreg.QueryValue(reg_handle, r'SOFTWARE\\lib_registry_test') == 'test2'

        >>> # use sub key
        >>> reg_handle_software = winreg.OpenKey(reg_handle, 'SOFTWARE')
        >>> winreg.SetValue(reg_handle_software, 'lib_registry_test', FakeWinReg.REG_SZ, 'test3')
        >>> assert winreg.QueryValue(reg_handle, r'SOFTWARE\\lib_registry_test') == 'test3'

        >>> # Tear Down
        >>> winreg.DeleteKey(reg_handle,r'SOFTWARE\\lib_registry_test')

        """
        if type != FakeWinReg.REG_SZ:
            # checked - like winreg
            raise TypeError('type must be winreg.REG_SZ')

        key_handle = self._resolve_key(key)
        access = key_handle.access
        try:
            # create the key if not there
            key_handle = self.OpenKey(key_handle, sub_key, 0, access=access)
        except FileNotFoundError:
            key_handle = self.CreateKey(key_handle, sub_key=sub_key)
        self.SetValueEx(key_handle, '', 0, FakeWinReg.REG_SZ, value)

    @check_for_kwargs
    def SetValueEx(self, key: Union[PyHKEY, int], value_name: Optional[str], reserved: int, type: int, value: Union[None, bytes, str, int]) -> None:    # noqa
        """
        Stores data in the value field of an open registry key.
        key is an already open key, or one of the predefined HKEY_* constants.

        value_name is a string that names the subkey with which the value is associated.
        if value_name is None or '' it will write to the default value of the Key

        reserved can be anything – zero is always passed to the API.

        type is an integer that specifies the type of the data.

        value is a new value.

        This method can also set additional value and type information for the specified key.
        The key identified by the key parameter must have been opened with KEY_SET_VALUE access.    (NOT IMPLEMENTED))

        To open the key, use the CreateKey() or OpenKey() methods.

        Value lengths are limited by available memory. Long values (more than 2048 bytes)
        should be stored as files with the filenames stored in the configuration registry. This helps the registry perform efficiently.
        Raises an auditing event winreg.SetValue with arguments key, sub_key, type, value.          (NOT IMPLEMENTED)

        type(int)       type name                       Description
        =========================================================
        0               REG_NONE	                    No defined value type.
        1               REG_SZ	                        A null-terminated string.
        2               REG_EXPAND_SZ	                Null-terminated string containing references to environment variables (%PATH%).
                                                        (Python handles this termination automatically.)
        3               REG_BINARY	                    Binary data in any form.
        4               REG_DWORD	                    A 32-bit number.
        4               REG_DWORD_LITTLE_ENDIAN	        A 32-bit number in little-endian format.
        5               REG_DWORD_BIG_ENDIAN	        A 32-bit number in big-endian format.
        6               REG_LINK	                    A Unicode symbolic link.
        7               REG_MULTI_SZ	                A sequence of null-terminated strings, terminated by two null characters.
        8               REG_RESOURCE_LIST	            A device-driver resource list.
        9               REG_FULL_RESOURCE_DESCRIPTOR    A hardware setting.
        10              REG_RESOURCE_REQUIREMENTS_LIST  A hardware resource list.
        11              REG_QWORD                       A 64 - bit number.
        11              REG_QWORD_LITTLE_ENDIAN         A 64 - bit number in little - endian format.Equivalent to REG_QWORD.


        >>> # Setup
        >>> f_registry = fake_reg.FakeRegistry()
        >>> discard = setup_fake_registry.set_minimal_windows_testvalues(f_registry)
        >>> winreg = FakeWinReg(f_registry)
        >>> reg_handle = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
        >>> key_handle = winreg.OpenKey(reg_handle, r'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion')

        >>> # Test
        >>> winreg.SetValueEx(key_handle, 'some_test', 0, winreg.REG_SZ, 'some_test_value')
        >>> assert winreg.QueryValueEx(key_handle, 'some_test') == ('some_test_value', winreg.REG_SZ)

        >>> # Test Overwrite
        >>> winreg.SetValueEx(key_handle, 'some_test', 0, winreg.REG_SZ, 'some_test_value2')
        >>> assert winreg.QueryValueEx(key_handle, 'some_test') == ('some_test_value2', winreg.REG_SZ)

        >>> # Teardown
        >>> winreg.DeleteValue(key_handle, 'some_test')

        """
        # value name = None is the default Value of the Key
        if value_name is None:
            value_name = ''
        key_handle = self._resolve_key(key)
        fake_reg.set_fake_reg_value(key_handle.data, sub_key='', value_name=value_name, value=value, value_type=type)

    def _resolve_key(self, key: Union[int, PyHKEY]) -> PyHKEY:
        """
        Returns the full path to the key

        >>> # Setup
        >>> f_registry = fake_reg.FakeRegistry()
        >>> discard = setup_fake_registry.set_minimal_windows_testvalues(f_registry)
        >>> winreg = FakeWinReg(f_registry)

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
