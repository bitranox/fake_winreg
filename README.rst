fake_winreg
===========


Version v1.5.7 as of 2021-12-16 see `Changelog`_

|travis_build| |license| |jupyter| |pypi|

|codecov| |better_code| |cc_maintain| |cc_issues| |cc_coverage| |snyk|


.. |travis_build| image:: https://img.shields.io/travis/bitranox/fake_winreg/master.svg
   :target: https://travis-ci.org/bitranox/fake_winreg

.. |license| image:: https://img.shields.io/github/license/webcomics/pywine.svg
   :target: http://en.wikipedia.org/wiki/MIT_License

.. |jupyter| image:: https://mybinder.org/badge_logo.svg
 :target: https://mybinder.org/v2/gh/bitranox/fake_winreg/master?filepath=fake_winreg.ipynb

.. for the pypi status link note the dashes, not the underscore !
.. |pypi| image:: https://img.shields.io/pypi/status/fake-winreg?label=PyPI%20Package
   :target: https://badge.fury.io/py/fake_winreg

.. |codecov| image:: https://img.shields.io/codecov/c/github/bitranox/fake_winreg
   :target: https://codecov.io/gh/bitranox/fake_winreg

.. |better_code| image:: https://bettercodehub.com/edge/badge/bitranox/fake_winreg?branch=master
   :target: https://bettercodehub.com/results/bitranox/fake_winreg

.. |cc_maintain| image:: https://img.shields.io/codeclimate/maintainability-percentage/bitranox/fake_winreg?label=CC%20maintainability
   :target: https://codeclimate.com/github/bitranox/fake_winreg/maintainability
   :alt: Maintainability

.. |cc_issues| image:: https://img.shields.io/codeclimate/issues/bitranox/fake_winreg?label=CC%20issues
   :target: https://codeclimate.com/github/bitranox/fake_winreg/maintainability
   :alt: Maintainability

.. |cc_coverage| image:: https://img.shields.io/codeclimate/coverage/bitranox/fake_winreg?label=CC%20coverage
   :target: https://codeclimate.com/github/bitranox/fake_winreg/test_coverage
   :alt: Code Coverage

.. |snyk| image:: https://img.shields.io/snyk/vulnerabilities/github/bitranox/fake_winreg
   :target: https://snyk.io/test/github/bitranox/fake_winreg

.. |black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black

FUNCTION
========

test winreg functions on a fake registry on windows and linux, without messing up Your real registry.

Fully type annotated and documented, so You can enjoy the type hints in Your favorit IDE

This is perfect for TDD, creating registry related code and covering most issues before You hit a real registry with Your tests.

If You want to see real life examples, check out `lib_registry <https://github.com/bitranox/lib_registry>`_

- get all winreg function names, type hints and constants, even on linux in Your favorite IDE
- you plug in this "fake _winreg" and can test all Your Registry related functions on linux, wine, windows
- all the predefined HKEY\_*, REG\_*, KEY\_* constants are there.
- You might even test against a set of different fake registries
- you can use (almost) all winreg functions against a "fake" registry
- it behaves very much like the real "winreg" (version 3.3),
  like not accepting keyword arguments for most functions,
  accepting sub_keys to be "None" or "blank" in some, but not all functions, etc.
- it raises the same Exceptions like winreg
- read, write registry values and keys, etc.

LIMITATIONS
===========

- there are no access rights - sam is not supported.
  That means You can read/write/delete Keys and values in the fake registry,
  even if You opened the key with access right "KEY_READ".
  You can Delete Keys and Values in HKEY_LOCAL_MACHINE and so on, even if You dont have Admin Rights.
  That is not an security issue, since You test against a fake registry - and You test mostly Your own software.
  If You need it, contributions are welcome ! (somehow it would make sense for TDD to have it)
- you can not dump a real registry at the moment and save it, in order to use it as a fake registry - that means
  all the keys You need, You have to set manually at the moment.
  I will polish up my old project "fingerprint" and make a compatible file format to dump / read / write registry branches.
- some (few) winreg functions are not implemented - if You miss out something, give me a note, i will integrate it
- obviously we can not connect to the registry of another windows computer over the network
- KEY_WOW64_32KEY is not supported. We show always the same ...
- auditing event's are not supported

----

automated tests, Travis Matrix, Documentation, Badges, etc. are managed with `PizzaCutter <https://github
.com/bitranox/PizzaCutter>`_ (cookiecutter on steroids)

Python version required: 3.6.0 or newer

tested on linux "bionic" with python 3.6, 3.7, 3.8, 3.9-dev, pypy3 - architectures: amd64, ppc64le, s390x, arm64

`100% code coverage <https://codecov.io/gh/bitranox/fake_winreg>`_, flake8 style checking ,mypy static type checking ,tested under `Linux, macOS, Windows <https://travis-ci.org/bitranox/fake_winreg>`_, automatic daily builds and monitoring

----

- `Try it Online`_
- `Usage`_
- `Usage from Commandline`_
- `Installation and Upgrade`_
- `Requirements`_
- `Acknowledgements`_
- `Contribute`_
- `Report Issues <https://github.com/bitranox/fake_winreg/blob/master/ISSUE_TEMPLATE.md>`_
- `Pull Request <https://github.com/bitranox/fake_winreg/blob/master/PULL_REQUEST_TEMPLATE.md>`_
- `Code of Conduct <https://github.com/bitranox/fake_winreg/blob/master/CODE_OF_CONDUCT.md>`_
- `License`_
- `Changelog`_

----

Try it Online
-------------

You might try it right away in Jupyter Notebook by using the "launch binder" badge, or click `here <https://mybinder.org/v2/gh/{{rst_include.
repository_slug}}/master?filepath=fake_winreg.ipynb>`_

Usage
-----------

.. code-block:: python

        import fake_winreg as winreg

        # setup a fake registry for windows
        fake_registry = winreg.fake_reg_tools.get_minimal_windows_testregistry()

        # load the fake registry into fake winreg
        winreg.load_fake_registry(fake_registry)

        # try the fake registry
        reg_handle = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)

        # Open Key
        reg_key = winreg.OpenKey(reg_handle, r'SOFTWARE\Microsoft\Windows NT\CurrentVersion')
        winreg.QueryValueEx(reg_key, 'CurrentBuild')


here a more comprehensive description of the winreg methods (which are implemented by fake registry)

following custom data types are defined:

.. code-block:: python

    # the possible types of a handle that can be passed to winreg functions
    Handle = Union[int, HKEYType, PyHKEY]

.. code-block:: python

    # the possible types of data that we can receive or write to registry values
    RegData = Union[None, bytes, int, str, List[str]]

ConnectRegistry
---------------

.. code-block:: python

    def ConnectRegistry(computer_name: Optional[str], key: Handle) -> PyHKEY:     # noqa
        """
        Establishes a connection to a predefined registry handle on another computer, and returns a new handle object.
        the function does NOT accept named parameters, only positional parameters



        Parameter
        ---------

        computer_name:
            the name of the remote computer, of the form r"\\computername" or simply "computername"
            If None or '', the local computer is used.

            if the computer name can not be resolved on the network,fake_winreg will deliver:
             "OSError: [WinError 1707] The network address is invalid"

            if the computer_name given can be reached, we finally raise:
            "SystemError: System error 53 has occurred. The network path was not found"


        key:
            the predefined handle to connect to, or one of the predefined HKEY_* constants.



        Returns
        -------

        the handle of the opened key. If the function fails, an OSError exception is raised.



        Exceptions
        ----------

        OSError: [WinError 1707] The network address is invalid
            if the computer name can not be resolved

        FileNotFoundError: [WinError 53] The network path was not found
            if the network path is invalid

        OSError: [WinError 6] The handle is invalid
            if parameter key is invalid

        TypeError: None is not a valid HKEY in this context
            if parameter key is None


        TypeError: The object is not a PyHKEY object
            if parameter key is not integer or PyHKEY type

        OverflowError: int too big to convert
            if parameter key is > 64 Bit Integer Value

        TypeError: ConnectRegistry() got some positional-only arguments passed as keyword arguments: '<key>'
            if a keyword (named) parameter was passed



        Events
        ------

        winreg.ConnectRegistry auditing event (NOT IMPLEMENTED), with arguments computer_name, key.



        Examples
        --------

        >>> # Setup
        >>> fake_registry = fake_reg_tools.get_minimal_windows_testregistry()
        >>> load_fake_registry(fake_registry)

        >>> # Connect
        >>> ConnectRegistry(None, HKEY_LOCAL_MACHINE)
        <...PyHKEY object at ...>

        >>> # Try to connect to computer
        >>> ConnectRegistry('HAL', HKEY_LOCAL_MACHINE)
        Traceback (most recent call last):
            ...
        OSError: [WinError 1707] The network address is invalid

        >>> # Try connect to computer, but invalid network path
        >>> ConnectRegistry(r'localhost\\invalid\\path', HKEY_LOCAL_MACHINE)
        Traceback (most recent call last):
            ...
        FileNotFoundError: [WinError 53] The network path was not found

        >>> # provoke wrong key type Error
        >>> ConnectRegistry('fake_registry_test_computer', 'fake_registry_key')  # noqa
        Traceback (most recent call last):
            ...
        TypeError: The object is not a PyHKEY object

        >>> # provoke Invalid Handle Error
        >>> ConnectRegistry(None, 42)
        Traceback (most recent call last):
            ...
        OSError: [WinError 6] The handle is invalid

        >>> # must not accept keyword parameters
        >>> ConnectRegistry(computer_name=None, key=HKEY_LOCAL_MACHINE)
        Traceback (most recent call last):
            ...
        TypeError: ConnectRegistry() got some positional-only arguments passed as keyword arguments: 'computer_name, key'

        """

CloseKey
---------------

.. code-block:: python

    def CloseKey(hkey: Union[int, HKEYType]) -> None:      # noqa
        """
        Closes a previously opened registry key.

        the function does NOT accept named parameters, only positional parameters

        Note: If hkey is not closed using this method (or via hkey.Close()), it is closed when the hkey object is destroyed by Python.



        Parameter
        ---------

        hkey:
            the predefined handle to connect to, or one of the predefined HKEY_* constants.



        Exceptions
        ----------

        OSError: [WinError 6] The handle is invalid
            if parameter key is invalid

        TypeError: The object is not a PyHKEY object
            if parameter key is not integer or PyHKEY type

        OverflowError: int too big to convert
            if parameter key is > 64 Bit Integer Value

        TypeError: CloseKey() got some positional-only arguments passed as keyword arguments: '<key>'
            if a keyword (named) parameter was passed



        Examples
        --------

        >>> # Setup
        >>> fake_registry = fake_reg_tools.get_minimal_windows_testregistry()
        >>> load_fake_registry(fake_registry)

        >>> # Test
        >>> hive_key = ConnectRegistry(None, HKEY_LOCAL_MACHINE)
        >>> CloseKey(HKEY_LOCAL_MACHINE)

        >>> # Test hkey = None
        >>> hive_key = ConnectRegistry(None, HKEY_LOCAL_MACHINE)
        >>> CloseKey(None)  # noqa

        >>> # does not accept keyword parameters
        >>> hive_key = ConnectRegistry(None, HKEY_LOCAL_MACHINE)
        >>> CloseKey(hkey=HKEY_LOCAL_MACHINE)
        Traceback (most recent call last):
            ...
        TypeError: CloseKey() got some positional-only arguments passed as keyword arguments: 'hkey'

        """

CreateKey
---------------

.. code-block:: python

    def CreateKey(key: Handle, sub_key: Optional[str]) -> PyHKEY:      # noqa
        """
        Creates or opens the specified key.

        The sub_key can contain a directory structure like r'Software\\xxx\\yyy' - all the parents to yyy will be created

        the function does NOT accept named parameters, only positional parameters


        Result
        ------

        If key is one of the predefined keys, sub_key may be None or empty string,
        and a new handle will be returned with access KEY_WRITE

        If the key already exists, this function opens the existing key.
        otherwise it will return the handle to the new created key with access KEY_WRITE


        From original winreg description (this is wrong):
            If key is one of the predefined keys, sub_key may be None.
            In that case, the handle returned is the same key handle passed in to the function.
            I always get back a different handle, this seems to be wrong (needs testing)

        Parameter
        ---------

        key:
            an already open key, or one of the predefined HKEY_* constants.

        sub_key:
            a string that names the key this method opens or creates.
            sub_key can be None or empty string when the key is one of the predefined hkeys


        Exceptions
        ----------

        PermissionError: [WinError 5] Access is denied
            if You dont have the right to Create the Key (at least KEY_CREATE_SUBKEY)

        OSError: [WinError 1010] The configuration registry key is invalid
            if the function fails to create the Key

        OSError: [WinError 6] The handle is invalid
            if parameter key is invalid

        TypeError: None is not a valid HKEY in this context
            if parameter key is None

        TypeError: The object is not a PyHKEY object
            if parameter key is not integer or PyHKEY type

        OverflowError: int too big to convert
            if parameter key is > 64 Bit Integer Value

        TypeError: CreateKey() argument 2 must be str or None, not <type>
            if the subkey is anything else then str or None

        OSError: [WinError 1010] The configuration registry key is invalid
            if the subkey is None or empty string, and key is not one of the predefined HKEY Constants

        TypeError: CreateKey() got some positional-only arguments passed as keyword arguments: '<key>'
            if a keyword (named) parameter was passed



        Events
        ------

        Raises an auditing event winreg.CreateKey with arguments key, sub_key, access. (NOT IMPLEMENTED)

        Raises an auditing event winreg.OpenKey/result with argument key. (NOT IMPLEMENTED)



        Examples
        --------

        >>> # Setup
        >>> fake_registry = fake_reg_tools.get_minimal_windows_testregistry()
        >>> load_fake_registry(fake_registry)

        >>> # Connect
        >>> reg_handle = ConnectRegistry(None, HKEY_CURRENT_USER)

        >>> # create key
        >>> key_handle_created = CreateKey(reg_handle, r'SOFTWARE\\xxxx\\yyyy')

        >>> # create an existing key - we should NOT get the same handle back
        >>> key_handle_existing = CreateKey(reg_handle, r'SOFTWARE\\xxxx\\yyyy')
        >>> assert key_handle_existing != key_handle_created

        >>> # provoke Error key None
        >>> CreateKey(None, r'SOFTWARE\\xxxx\\yyyy')    # noqa
        Traceback (most recent call last):
            ...
        TypeError: None is not a valid HKEY in this context

        >>> # provoke Error key wrong type
        >>> CreateKey('test_fake_key_invalid', r'SOFTWARE\\xxxx\\yyyy')    # noqa
        Traceback (most recent call last):
            ...
        TypeError: The object is not a PyHKEY object

        >>> # provoke Error key >= 2 ** 64
        >>> CreateKey(2 ** 64, r'SOFTWARE\\xxxx\\yyyy')
        Traceback (most recent call last):
            ...
        OverflowError: int too big to convert

        >>> # provoke invalid handle
        >>> CreateKey(42, r'SOFTWARE\\xxxx\\yyyy')
        Traceback (most recent call last):
        ...
        OSError: [WinError 6] The handle is invalid

        >>> # provoke Error on empty subkey
        >>> key_handle_existing = CreateKey(key_handle_created, r'')
        Traceback (most recent call last):
            ...
        OSError: [WinError 1010] The configuration registry key is invalid

        >>> # provoke Error subkey wrong type
        >>> key_handle_existing = CreateKey(reg_handle, 1)  # noqa
        Traceback (most recent call last):
            ...
        TypeError: CreateKey() argument 2 must be str or None, not int

        >>> # Test subkey=None with key as predefined HKEY - that should pass
        >>> # the actual behaviour is different to the winreg documentation !
        >>> key_handle_hkcu = CreateKey(HKEY_CURRENT_USER, None)
        >>> key_handle_hkcu2 = CreateKey(key_handle_hkcu, None)
        >>> assert key_handle_hkcu != key_handle_hkcu2

        >>> # Test subkey='' with key as predefined HKEY - that should pass
        >>> # the actual behaviour is different to the winreg documentation !
        >>> key_handle_hkcu = CreateKey(HKEY_CURRENT_USER, '')
        >>> key_handle_hkcu2 = CreateKey(key_handle_hkcu, '')
        >>> assert key_handle_hkcu != key_handle_hkcu2

        >>> # Teardown
        >>> DeleteKey(reg_handle, r'SOFTWARE\\xxxx\\yyyy')
        >>> DeleteKey(reg_handle, r'SOFTWARE\\xxxx')

        """

CreateKeyEx
---------------

.. code-block:: python

    def CreateKeyEx(key: Handle, sub_key: str, reserved: int = 0, access: int = KEY_WRITE) -> PyHKEY:      # noqa
        """
        Creates or opens the specified key, returning a handle object with access as passed in the parameter

        The sub_key can contain a directory structure like r'Software\\xxx\\yyy' - all the parents to yyy will be created

        the function does NOT accept named parameters, only positional parameters



        Parameter
        ---------

        key:
            an already open key, or one of the predefined HKEY_* constants.

        sub_key:
            a string (can be empty) that names the key this method opens or creates.
            the sub_key must not be None.

        reserved:
            reserved is a reserved integer, and has to be zero. The default is zero.

        access:
            a integer that specifies an access mask that describes the desired security access for returned key handle
            Default is KEY_WRITE. See Access Rights for other allowed values.
            (any integer is accepted here in original winreg, bit masked against KEY_* access parameters)


        Returns
        -------

        the handle of the opened key.



        Exceptions
        ----------

        OSError: [WinError 1010] The configuration registry key is invalid
            if the function fails to create the Key

        OSError: [WinError 6] The handle is invalid
            if parameter key is invalid

        TypeError: None is not a valid HKEY in this context
            if parameter key is None

        TypeError: The object is not a PyHKEY object
            if parameter key is not integer or PyHKEY type

        OverflowError: int too big to convert
            if parameter key is > 64 Bit Integer Value

        OSError: [WinError 1010] The configuration registry key is invalid
            if the subkey is None

        TypeError: CreateKeyEx() argument 2 must be str or None, not <type>
            if the subkey is anything else then str

        TypeError: CreateKeyEx() got some positional-only arguments passed as keyword arguments: '<key>'
            if a keyword (named) parameter was passed



        Events
        ------

        Raises an auditing event winreg.CreateKey with arguments key, sub_key, access. (NOT IMPLEMENTED)

        Raises an auditing event winreg.OpenKey/result with argument key. (NOT IMPLEMENTED)



        Examples
        --------

        >>> # Setup
        >>> fake_registry = fake_reg_tools.get_minimal_windows_testregistry()
        >>> load_fake_registry(fake_registry)

        >>> # Connect
        >>> reg_handle = ConnectRegistry(None, HKEY_CURRENT_USER)

        >>> # create key
        >>> key_handle_created = CreateKeyEx(reg_handle, r'SOFTWARE\\xxxx\\yyyy', 0, KEY_WRITE)

        >>> # create an existing key - we get a new handle back
        >>> key_handle_existing = CreateKeyEx(reg_handle, r'SOFTWARE\\xxxx\\yyyy', 0, KEY_WRITE)
        >>> assert key_handle_existing != key_handle_created

        >>> # provoke Error key None
        >>> CreateKeyEx(None, r'SOFTWARE\\xxxx\\yyyy', 0 ,  KEY_WRITE)   # noqa
        Traceback (most recent call last):
            ...
        TypeError: None is not a valid HKEY in this context

        >>> # provoke Error key wrong type
        >>> CreateKeyEx('test_fake_key_invalid', r'SOFTWARE\\xxxx\\yyyy', 0 ,  KEY_WRITE)  # noqa
        Traceback (most recent call last):
            ...
        TypeError: The object is not a PyHKEY object

        >>> # provoke Error key >= 2 ** 64
        >>> CreateKeyEx(2 ** 64, r'SOFTWARE\\xxxx\\yyyy', 0 ,  KEY_WRITE)
        Traceback (most recent call last):
            ...
        OverflowError: int too big to convert

        >>> # provoke invalid handle
        >>> CreateKeyEx(42, r'SOFTWARE\\xxxx\\yyyy', 0 ,  KEY_WRITE)
        Traceback (most recent call last):
        ...
        OSError: [WinError 6] The handle is invalid

        >>> # subkey empty is valid
        >>> discard = key_handle_existing = CreateKeyEx(reg_handle, r'', 0 ,  KEY_WRITE)

        >>> # subkey None is invalid
        >>> discard = key_handle_existing = CreateKeyEx(reg_handle, None, 0 ,  KEY_WRITE)  # noqa
        Traceback (most recent call last):
            ...
        OSError: [WinError 1010] The configuration registry key is invalid


        >>> # provoke Error subkey wrong type
        >>> key_handle_existing = CreateKeyEx(reg_handle, 1, 0 ,  KEY_WRITE)  # noqa
        Traceback (most recent call last):
            ...
        TypeError: CreateKeyEx() argument 2 must be str or None, not int

        >>> # Teardown
        >>> DeleteKey(reg_handle, r'SOFTWARE\\xxxx\\yyyy')
        >>> DeleteKey(reg_handle, r'SOFTWARE\\xxxx')

        """

DeleteKey
---------------

.. code-block:: python

    def DeleteKey(key: Handle, sub_key: str) -> None:         # noqa
        """
        Deletes the specified key. This method can not delete keys with subkeys.
        If the method succeeds, the entire key, including all of its values, is removed.
        the function does NOT accept named parameters, only positional parameters

        Parameter
        ---------

        key:
            an already open key, or one of the predefined HKEY_* constants.

        sub_key:
            a string that must be a subkey of the key identified by the key parameter or ''.
            sub_key must not be None, and the key may not have subkeys.



        Exceptions
        ----------

        OSError ...
            if it fails to Delete the Key

        PermissionError: [WinError 5] Access is denied
            if the key specified to be deleted have subkeys

        FileNotFoundError: [WinError 2] The system cannot find the file specified
            if the Key specified to be deleted does not exist

        TypeError: DeleteKey() argument 2 must be str, not <type>
            if parameter sub_key type is anything else but string

        OSError: [WinError 6] The handle is invalid
            if parameter key is invalid

        TypeError: None is not a valid HKEY in this context
            if parameter key is None

        TypeError: The object is not a PyHKEY object
            if parameter key is not integer or PyHKEY type

        OverflowError: int too big to convert
            if parameter key is > 64 Bit Integer Value

        TypeError: DeleteKey() got some positional-only arguments passed as keyword arguments: '<key>'
            if a keyword (named) parameter was passed



        Events
        ------

        Raises an auditing event winreg.DeleteKey with arguments key, sub_key, access. (NOT IMPLEMENTED)



        Examples
        --------

        >>> # Setup
        >>> fake_registry = fake_reg_tools.get_minimal_windows_testregistry()
        >>> load_fake_registry(fake_registry)

        >>> reg_handle = ConnectRegistry(None, HKEY_CURRENT_USER)
        >>> key_handle_created = CreateKey(reg_handle, r'SOFTWARE\\xxxx\\yyyy\\zzz')

        >>> # Delete key without subkeys
        >>> # assert __key_in_py_hive_handles(r'HKEY_CURRENT_USER\\SOFTWARE\\xxxx\\yyyy\\zzz')

        >>> DeleteKey(reg_handle, r'SOFTWARE\\xxxx\\yyyy\\zzz')
        >>> # assert not __key_in_py_hive_handles(r'HKEY_CURRENT_USER\\SOFTWARE\\xxxx\\yyyy\\zzz')

        >>> # try to delete non existing key (it was deleted before)
        >>> DeleteKey(reg_handle, r'SOFTWARE\\xxxx\\yyyy\\zzz')
        Traceback (most recent call last):
            ...
        FileNotFoundError: [WinError 2] The system cannot find the file specified

        >>> # try to delete key with subkey
        >>> DeleteKey(reg_handle, r'SOFTWARE\\xxxx')
        Traceback (most recent call last):
            ...
        PermissionError: [WinError 5] Access is denied

        >>> # provoke error subkey = None
        >>> DeleteKey(reg_handle, None)  # noqa
        Traceback (most recent call last):
            ...
        TypeError: DeleteKey() argument 2 must be str, not None

        >>> # subkey = '' is allowed here
        >>> reg_handle_sub = OpenKey(reg_handle, r'SOFTWARE\\xxxx\\yyyy')
        >>> DeleteKey(reg_handle_sub, '')

        >>> # Teardown
        >>> DeleteKey(reg_handle, r'SOFTWARE\\xxxx')

        """

DeleteKeyEx
---------------

.. code-block:: python

    def DeleteKeyEx(key: Handle, sub_key: str, access: int = KEY_WOW64_64KEY, reserved: int = 0) -> None:     # noqa
        """
        Deletes the specified key. This method can not delete keys with subkeys.
        If the method succeeds, the entire key, including all of its values, is removed.
        the function does NOT accept named parameters, only positional parameters

        Note The DeleteKeyEx() function is implemented with the RegDeleteKeyEx Windows API function,
        which is specific to 64-bit versions of Windows. See the RegDeleteKeyEx documentation.



        Parameter
        ---------

        key:
            an already open key, or one of the predefined HKEY_* constants.

        sub_key:
            a string that must be a subkey of the key identified by the key parameter or ''.
            sub_key must not be None, and the key may not have subkeys.

        access:
            a integer that specifies an access mask that describes the desired security access for the key.
            Default is KEY_WOW64_64KEY. See Access Rights for other allowed values. (NOT IMPLEMENTED)
            (any integer is accepted here in original winreg

        reserved:
            reserved is a reserved integer, and must be zero. The default is zero.



        Exceptions
        ----------

        OSError: ...
            if it fails to Delete the Key

        PermissionError: [WinError 5] Access is denied
            if the key specified to be deleted have subkeys

        FileNotFoundError: [WinError 2] The system cannot find the file specified
            if the Key specified to be deleted does not exist

        OSError: [WinError 6] The handle is invalid
            if parameter key is invalid

        TypeError: None is not a valid HKEY in this context
            if parameter key is None

        TypeError: The object is not a PyHKEY object
            if parameter key is not integer or PyHKEY type

        OverflowError: int too big to convert
            if parameter key is > 64 Bit Integer Value

        NotImplementedError:
            On unsupported Windows versions (NOT IMPLEMENTED)

        TypeError: DeleteKeyEx() argument 2 must be str, not <type>
            if parameter sub_key type is anything else but string

        TypeError: an integer is required (got NoneType)
            if parameter access is None

        TypeError: an integer is required (got type <type>)
            if parameter access is not int

        OverflowError: Python int too large to convert to C long
            if parameter access is > 64 Bit Integer Value

        TypeError: an integer is required (got type <type>)
            if parameter reserved is not int

        OverflowError: Python int too large to convert to C long
            if parameter reserved is > 64 Bit Integer Value

        OSError: WinError 87 The parameter is incorrect
            if parameter reserved is not 0

        TypeError: DeleteKeyEx() got some positional-only arguments passed as keyword arguments: '<key>'
            if a keyword (named) parameter was passed



        Events
        ------

        Raises an auditing event winreg.DeleteKey with arguments key, sub_key, access. (NOT IMPLEMENTED)



        Examples
        --------

        >>> # Setup
        >>> fake_registry = fake_reg_tools.get_minimal_windows_testregistry()
        >>> load_fake_registry(fake_registry)
        >>> reg_handle = ConnectRegistry(None, HKEY_CURRENT_USER)
        >>> key_handle_created = CreateKey(reg_handle, r'Software\\xxxx\\yyyy\\zzz')

        >>> # Delete key without subkeys
        >>> # assert __key_in_py_hive_handles(r'HKEY_CURRENT_USER\\SOFTWARE\\xxxx\\yyyy\\zzz')
        >>> DeleteKeyEx(reg_handle, r'Software\\xxxx\\yyyy\\zzz')
        >>> # assert not __key_in_py_hive_handles(r'HKEY_CURRENT_USER\\SOFTWARE\\xxxx\\yyyy\\zzz')

        >>> # try to delete non existing key (it was deleted before)
        >>> DeleteKeyEx(reg_handle, r'Software\\xxxx\\yyyy\\zzz')
        Traceback (most recent call last):
            ...
        FileNotFoundError: [WinError 2] The system cannot find the file specified

        >>> # try to delete key with subkey
        >>> DeleteKeyEx(reg_handle, r'Software\\xxxx')
        Traceback (most recent call last):
            ...
        PermissionError: [WinError 5] Access is denied

        >>> # try to delete key with subkey = None
        >>> DeleteKeyEx(reg_handle, None)            # noqa
        Traceback (most recent call last):
            ...
        TypeError: DeleteKeyEx() argument 2 must be str, not None

        >>> # try to delete key with access = KEY_WOW64_32KEY
        >>> DeleteKeyEx(reg_handle, r'Software\\xxxx\\yyyy', KEY_WOW64_32KEY)
        Traceback (most recent call last):
            ...
        NotImplementedError: we only support KEY_WOW64_64KEY

        >>> # Teardown
        >>> DeleteKeyEx(reg_handle, r'Software\\xxxx\\yyyy')
        >>> DeleteKeyEx(reg_handle, r'Software\\xxxx')

        """

DeleteValue
---------------

.. code-block:: python

    def DeleteValue(key: Handle, value: Optional[str]) -> None:         # noqa
        """
        Removes a named value from a registry key.
        the function does NOT accept named parameters, only positional parameters



        Parameter
        ---------

        key:
            an already open key, or one of the predefined HKEY_* constants.

        value:
            None, or a string that identifies the value to remove.
            if value is None, or '' it deletes the default Value of the Key



        Exceptions
        ----------

        FileNotFoundError: [WinError 2] The system cannot find the file specified'
            if the Value specified to be deleted does not exist

        OSError: [WinError 6] The handle is invalid
            if parameter key is invalid

        TypeError: None is not a valid HKEY in this context
            if parameter key is None

        TypeError: The object is not a PyHKEY object
            if parameter key is not integer or PyHKEY type

        OverflowError: int too big to convert
            if parameter key is > 64 Bit Integer Value

        TypeError: DeleteValue() argument 2 must be str or None, not <type>
            if parameter value type is anything else but string or None

        TypeError: DeleteValue() got some positional-only arguments passed as keyword arguments: '<key>'
            if a keyword (named) parameter was passed



        Events
        ------

        Raises an auditing event winreg.DeleteValue with arguments key, value. (NOT IMPLEMENTED)



        Examples
        --------

        >>> # Setup
        >>> fake_registry = fake_reg_tools.get_minimal_windows_testregistry()
        >>> load_fake_registry(fake_registry)

        >>> reg_handle = ConnectRegistry(None, HKEY_LOCAL_MACHINE)
        >>> key_handle = OpenKey(reg_handle, r'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion')
        >>> SetValueEx(key_handle, 'some_test', 0, REG_SZ, 'some_test_value')

        >>> # Delete Default Value, value_name NONE (not set, therefore Error
        >>> DeleteValue(key_handle, None)
        Traceback (most recent call last):
            ...
        FileNotFoundError: [WinError 2] The system cannot find the file specified

        >>> # Delete Default Value, value_name '' (not set, therefore Error
        >>> DeleteValue(key_handle, '')
        Traceback (most recent call last):
            ...
        FileNotFoundError: [WinError 2] The system cannot find the file specified

        >>> # Delete Non Existing Value
        >>> DeleteValue(key_handle, 'some_test')

        """

EnumKey
---------------

.. code-block:: python

    def EnumKey(key: Handle, index: int) -> str:              # noqa
        """
        Enumerates subkeys of an open registry key, returning a string.
        The function retrieves the name of one subkey each time it is called.
        It is typically called repeatedly until an OSError exception is raised,
        indicating, no more values are available.
        the function does NOT accept named parameters, only positional parameters



        Parameter
        ---------

        key:
            an already open key, or one of the predefined HKEY_* constants.

        index:
            an integer that identifies the index of the key to retrieve.



        Exceptions:
        -----------

        OSError: [WinError 259] No more data is available
            if the index is out of Range

        OSError: [WinError 6] The handle is invalid
            if parameter key is invalid

        TypeError: None is not a valid HKEY in this context
            if parameter key is None

        TypeError: The object is not a PyHKEY object
            if parameter key is not integer or PyHKEY type

        OverflowError: int too big to convert
            if parameter key is > 64 Bit Integer Value

        TypeError: an integer is required (got type <type>)
            if parameter index is type different from int

        OverflowError: Python int too large to convert to C int
            if parameter index is > 64 Bit Integer Value

        TypeError: EnumKey() got some positional-only arguments passed as keyword arguments: '<key>'
            if a keyword (named) parameter was passed



        Events
        ------

        Raises an auditing event winreg.EnumKey with arguments key, index. (NOT IMPLEMENTED)



        Examples
        --------

        >>> # Setup
        >>> fake_registry = fake_reg_tools.get_minimal_windows_testregistry()
        >>> load_fake_registry(fake_registry)
        >>> reg_handle = ConnectRegistry(None, HKEY_LOCAL_MACHINE)

        >>> # test get the first profile in the profile list
        >>> key_handle = OpenKey(reg_handle, r'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList')
        >>> assert isinstance(EnumKey(key_handle, 0), str)

        >>> # provoke error test out of index
        >>> EnumKey(key_handle, 100000000)
        Traceback (most recent call last):
            ...
        OSError: [WinError 259] No more data is available

        >>> # provoke error wrong key handle
        >>> EnumKey(42, 0)
        Traceback (most recent call last):
            ...
        OSError: [WinError 6] The handle is invalid

        >>> # no check for overflow here !
        >>> EnumKey(2 ** 64, 0)
        Traceback (most recent call last):
            ...
        OverflowError: int too big to convert

        """

EnumValue
---------------

.. code-block:: python

    def EnumValue(key: Handle, index: int) -> Tuple[str, RegData, int]:              # noqa
        """
        Enumerates values of an open registry key, returning a tuple.
        The function retrieves the name of one value each time it is called.
        It is typically called repeatedly, until an OSError exception is raised, indicating no more values.
        the function does NOT accept named parameters, only positional parameters



        Parameter
        ---------

        key:
            an already open key, or one of the predefined HKEY_* constants.

        index:
            an integer that identifies the index of the key to retrieve.



        Result
        ------

        The result is a tuple of 3 items:

        ========    ==============================================================================================
        Index       Meaning
        ========    ==============================================================================================
        0           A string that identifies the value name
        1           An object that holds the value data, and whose type depends on the underlying registry type
        2           An integer giving the registry type for this value (see table in docs for SetValueEx())
        ========    ==============================================================================================



        Exceptions
        ----------

        OSError: [WinError 259] No more data is available
            if the index is out of Range

        OSError: [WinError 6] The handle is invalid
            if parameter key is invalid

        TypeError: None is not a valid HKEY in this context
            if parameter key is None

        TypeError: The object is not a PyHKEY object
            if parameter key is not integer or PyHKEY type

        OverflowError: int too big to convert
            if parameter key is > 64 Bit Integer Value

        TypeError: an integer is required (got type <type>)
            if parameter index is type different from int

        OverflowError: Python int too large to convert to C int
            if parameter index is > 64 Bit Integer Value

        TypeError: EnumValue() got some positional-only arguments passed as keyword arguments: '<key>'
            if a keyword (named) parameter was passed



        Events
        ------

        Raises an auditing event winreg.EnumValue with arguments key, index. (NOT IMPLEMENTED)



        Registry Types
        --------------

        ==============  ==============================  ==============================  ==========================================================================
        type(int)       type name                       accepted python Types           Description
        ==============  ==============================  ==============================  ==========================================================================
        0               REG_NONE	                     None, bytes                     No defined value type.
        1               REG_SZ	                        None, str                       A null-terminated string.
        2               REG_EXPAND_SZ	                None, str                       Null-terminated string containing references to
                                                                                        environment variables (%PATH%).
                                                                                        (Python handles this termination automatically.)
        3               REG_BINARY	                    None, bytes                     Binary data in any form.
        4               REG_DWORD	                    None, int                       A 32-bit number.
        4               REG_DWORD_LITTLE_ENDIAN	        None, int                       A 32-bit number in little-endian format.
        5               REG_DWORD_BIG_ENDIAN	        None, bytes                     A 32-bit number in big-endian format.
        6               REG_LINK	                    None, bytes                     A Unicode symbolic link.
        7               REG_MULTI_SZ	                None, List[str]                 A sequence of null-terminated strings, terminated by two null characters.
        8               REG_RESOURCE_LIST	            None, bytes                     A device-driver resource list.
        9               REG_FULL_RESOURCE_DESCRIPTOR    None, bytes                     A hardware setting.
        10              REG_RESOURCE_REQUIREMENTS_LIST  None, bytes                     A hardware resource list.
        11              REG_QWORD                       None, bytes                     A 64 - bit number.
        11              REG_QWORD_LITTLE_ENDIAN         None, bytes                     A 64 - bit number in little - endian format.Equivalent to REG_QWORD.
        ==============  ==============================  ==============================  ==========================================================================

        * all other integers for REG_TYPE are accepted, and written to the registry. The value is handled as binary.
        by that way You would be able to encode data in the REG_TYPE for stealth data not easy to spot - who would expect it.



        Examples
        --------

        >>> # Setup
        >>> fake_registry = fake_reg_tools.get_minimal_windows_testregistry()
        >>> load_fake_registry(fake_registry)
        >>> reg_handle = ConnectRegistry(None, HKEY_LOCAL_MACHINE)

        >>> # Read the current Version
        >>> key_handle = OpenKey(reg_handle, r'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion')
        >>> EnumValue(key_handle, 0)
        (...)

        >>> # test out of index
        >>> EnumValue(key_handle, 100000000)
        Traceback (most recent call last):
            ...
        OSError: [WinError 259] No more data is available

        """

OpenKey
---------------

.. code-block:: python

    def OpenKey(key: Handle, sub_key: Union[str, None], reserved: int = 0, access: int = KEY_READ) -> PyHKEY:         # noqa
        """
        Opens the specified key, the result is a new handle to the specified key.
        one of the few functions of winreg that accepts named parameters



        Parameter
        ---------

        key:
            an already open key, or one of the predefined HKEY_* constants.

        sub_key:
            None, or a string that names the key this method opens or creates.
            If key is one of the predefined keys, sub_key may be None.

        reserved:
            reserved is a reserved integer, and should be zero. The default is zero.

        access:
            a integer that specifies an access mask that describes the desired security access for the key.
            Default is KEY_READ. See Access Rights for other allowed values.
            (any integer is accepted here in original winreg, bit masked against KEY_* access parameters)



        Exceptions
        ----------

        OSError: ...
            if it fails to open the key

        OSError: [WinError 6] The handle is invalid
            if parameter key is invalid

        TypeError: None is not a valid HKEY in this context
            if parameter key is None

        TypeError: The object is not a PyHKEY object
            if parameter key is not integer or PyHKEY type

        OverflowError: int too big to convert
            if parameter key is > 64 Bit Integer Value

        TypeError: OpenKey() argument 2 must be str or None, not <type>
            if the sub_key is anything else then str or None

        TypeError: an integer is required (got NoneType)
            if parameter reserved is None

        TypeError: an integer is required (got type <type>)
            if parameter reserved is not int

        PermissionError: [WinError 5] Access denied
            if parameter reserved is > 3)

        OverflowError: Python int too large to convert to C long
            if parameter reserved is > 64 Bit Integer Value

        OSError: [WinError 87] The parameter is incorrect
            on some values for reserved (for instance 455565) NOT IMPLEMENTED

        TypeError: an integer is required (got type <type>)
            if parameter access is not int

        OverflowError: Python int too large to convert to C long
            if parameter access is > 64 Bit Integer Value



        Events
        ------

        Raises an auditing event winreg.OpenKey with arguments key, sub_key, access.    # not implemented
        Raises an auditing event winreg.OpenKey/result with argument key.               # not implemented



        Examples
        --------

        >>> # Setup
        >>> fake_registry = fake_reg_tools.get_minimal_windows_testregistry()
        >>> load_fake_registry(fake_registry)
        >>> reg_handle = ConnectRegistry(None, HKEY_LOCAL_MACHINE)

        >>> # Open Key
        >>> key_handle = OpenKey(reg_handle, r'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion')
        >>> assert key_handle.handle.full_key == r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion'

        >>> # Open Key mit subkey=None
        >>> reg_open1 = OpenKey(key_handle, None)

        >>> # Open Key mit subkey=''
        >>> reg_open2 = OpenKey(key_handle, '')

        >>> # Open the same kay again, but we get a different Handle
        >>> reg_open3 = OpenKey(key_handle, '')

        >>> assert reg_open2 != reg_open3

        >>> # Open non existing Key
        >>> OpenKey(reg_handle, r'SOFTWARE\\Microsoft\\Windows NT\\DoesNotExist')
        Traceback (most recent call last):
            ...
        FileNotFoundError: [WinError 2] The system cannot find the file specified

        """

OpenKeyEx
---------------

.. code-block:: python

    def OpenKeyEx(key: Handle, sub_key: Optional[str], reserved: int = 0, access: int = KEY_READ) -> PyHKEY:        # noqa
        """
        Opens the specified key, the result is a new handle to the specified key with the given access.
        one of the few functions of winreg that accepts named parameters



        Parameter
        ---------

        key:
            an already open key, or one of the predefined HKEY_* constants.

        sub_key:
            None, or a string that names the key this method opens or creates.
            If key is one of the predefined keys, sub_key may be None.

        reserved:
            reserved is a reserved integer, and should be zero. The default is zero.

        access:
            a integer that specifies an access mask that describes the desired security access for the key.
            Default is KEY_READ. See Access Rights for other allowed values.
            (any integer is accepted here in original winreg, bit masked against KEY_* access parameters)



        Exceptions
        ----------

        OSError: ...
            if it fails to open the key

        OSError: [WinError 6] The handle is invalid
            if parameter key is invalid

        TypeError: None is not a valid HKEY in this context
            if parameter key is None

        TypeError: The object is not a PyHKEY object
            if parameter key is not integer or PyHKEY type

        OverflowError: int too big to convert
            if parameter key is > 64 Bit Integer Value

        TypeError: OpenKeyEx() argument 2 must be str or None, not <type>
            if the subkey is anything else then str or None

        TypeError: an integer is required (got NoneType)
            if parameter reserved is None

        TypeError: an integer is required (got type <type>)
            if parameter reserved is not int

        PermissionError: [WinError 5] Access denied
            if parameter reserved is > 3)

        OverflowError: Python int too large to convert to C long
            if parameter reserved is > 64 Bit Integer Value

        OSError: [WinError 87] The parameter is incorrect
            on some values for reserved (for instance 455565) NOT IMPLEMENTED

        TypeError: an integer is required (got type <type>)
            if parameter access is not int

        OverflowError: Python int too large to convert to C long
            if parameter access is > 64 Bit Integer Value



        Events
        ------

        Raises an auditing event winreg.OpenKey with arguments key, sub_key, access.    # not implemented
        Raises an auditing event winreg.OpenKey/result with argument key.               # not implemented



        Examples
        --------

        >>> # Setup
        >>> fake_registry = fake_reg_tools.get_minimal_windows_testregistry()
        >>> load_fake_registry(fake_registry)
        >>> reg_handle = ConnectRegistry(None, HKEY_LOCAL_MACHINE)

        >>> # Open Key
        >>> key_handle = OpenKeyEx(reg_handle, r'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion')
        >>> assert key_handle.handle.full_key == r'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion'

        >>> # Open non existing Key
        >>> OpenKeyEx(reg_handle, r'SOFTWARE\\Microsoft\\Windows NT\\DoesNotExist')
        Traceback (most recent call last):
            ...
        FileNotFoundError: [WinError 2] The system cannot find the file specified

        """

QueryInfoKey
---------------

.. code-block:: python

    def QueryInfoKey(key: Handle) -> Tuple[int, int, int]:            # noqa
        """
        Returns information about a key, as a tuple.
        the function does NOT accept named parameters, only positional parameters



        Parameter
        ---------

        key:
            the predefined handle to connect to, or one of the predefined HKEY_* constants.



        Result
        ------

        The result is a tuple of 3 items:

        ======  =============================================================================================================
        Index,  Meaning
        ======  =============================================================================================================
        0       An integer giving the number of sub keys this key has.
        1       An integer giving the number of values this key has.
        2       An integer giving when the key was last modified (if available) as 100’s of nanoseconds since Jan 1, 1601.
        ======  =============================================================================================================



        Exceptions
        ----------

        OSError: [WinError 6] The handle is invalid
            if parameter key is invalid

        TypeError: None is not a valid HKEY in this context
            if parameter key is None

        TypeError: The object is not a PyHKEY object
            if parameter key is not integer or PyHKEY type

        OverflowError: int too big to convert
            if parameter key is > 64 Bit Integer Value

        TypeError: QueryInfoKey() got some positional-only arguments passed as keyword arguments: '<key>'
            if a keyword (named) parameter was passed



        Events
        ------

        Raises an auditing event winreg.QueryInfoKey with argument key.



        Examples and Tests:
        -------------------


        >>> # Setup
        >>> fake_registry = fake_reg_tools.get_minimal_windows_testregistry()
        >>> load_fake_registry(fake_registry)
        >>> reg_handle = ConnectRegistry(None, HKEY_LOCAL_MACHINE)

        >>> # Open Key
        >>> key_handle = OpenKeyEx(reg_handle, r'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion')

        >>> new_reg_key_without_values = CreateKey(key_handle, 'test_without_values')
        >>> new_reg_key_with_subkeys_and_values = CreateKey(key_handle, 'test_with_subkeys_and_values')
        >>> SetValueEx(new_reg_key_with_subkeys_and_values, 'test_value_name', 0, REG_SZ, 'test_value')
        >>> new_reg_key_with_subkeys_subkey = CreateKey(new_reg_key_with_subkeys_and_values, 'subkey_of_test_with_subkeys')

        >>> # Test
        >>> QueryInfoKey(new_reg_key_without_values)
        (0, 0, ...)
        >>> QueryInfoKey(new_reg_key_with_subkeys_and_values)
        (1, 1, ...)

        >>> # Teardown
        >>> DeleteKey(key_handle, 'test_without_values')
        >>> DeleteKey(new_reg_key_with_subkeys_and_values, 'subkey_of_test_with_subkeys')
        >>> DeleteKey(key_handle, 'test_with_subkeys_and_values')

        """

QueryValue
---------------

.. code-block:: python

    def QueryValue(key: Handle, sub_key: Union[str, None]) -> str:        # noqa
        """
        Retrieves the unnamed value (the default value*) for a key, as string.

        * Remark : this is the Value what is shown in Regedit as "(Standard)" or "(Default)"
        it is usually not set. Nethertheless, even if the value is not set, QueryValue will deliver ''

        Values in the registry have name, type, and data components.

        This method retrieves the data for a key’s first value that has a NULL name.
        But the underlying API call doesn’t return the type, so always use QueryValueEx() if possible.

        the function does NOT accept named parameters, only positional parameters


        Parameter
        ---------

        key:
            the predefined handle to connect to, or one of the predefined HKEY_* constants.

        sub_key:
            None, or a string that names the key this method opens or creates.
            If key is one of the predefined keys, sub_key may be None. In that case,
            the handle returned is the same key handle passed in to the function.
            If the key already exists, this function opens the existing key.



        Result
        ------

        the unnamed value as string (if possible)



        Exceptions
        ----------

        OSError: [WinError 13] The data is invalid
            if the data in the unnamed value is not string

        OSError: [WinError 6] The handle is invalid
            if parameter key is invalid

        TypeError: None is not a valid HKEY in this context
            if parameter key is None

        TypeError: The object is not a PyHKEY object
            if parameter key is not integer or PyHKEY type

        OverflowError: int too big to convert
            if parameter key is > 64 Bit Integer Value

        TypeError: QueryValue() argument 2 must be str or None, not <type>
            if the subkey is anything else then str or None

        TypeError: QueryValue() got some positional-only arguments passed as keyword arguments: '<key>'
            if a keyword (named) parameter was passed



        Events:
        -------

        Raises an auditing event winreg.QueryValue with arguments key, sub_key, value_name. (NOT IMPLEMENTED)



        Examples
        --------

        >>> # Setup
        >>> fake_registry = fake_reg_tools.get_minimal_windows_testregistry()
        >>> load_fake_registry(fake_registry)
        >>> reg_handle = ConnectRegistry(None, HKEY_CURRENT_USER)
        >>> key_handle_created = CreateKey(reg_handle, r'SOFTWARE\\lib_registry_test')

        >>> # read Default Value, which is ''
        >>> assert QueryValue(reg_handle, r'SOFTWARE\\lib_registry_test') == ''

        >>> # sub key can be here None or empty !
        >>> assert QueryValue(key_handle_created, '') == ''
        >>> assert QueryValue(key_handle_created, None) == ''

        >>> # set and get default value
        >>> SetValueEx(key_handle_created, '', 0, REG_SZ, 'test1')
        >>> assert QueryValueEx(key_handle_created, '') == ('test1', REG_SZ)
        >>> assert QueryValue(reg_handle, r'SOFTWARE\\lib_registry_test') == 'test1'

        >>> # set the default value to non-string type, and try to get it with Query Value
        >>> SetValueEx(key_handle_created, '', 0, REG_DWORD, 42)
        >>> assert QueryValueEx(key_handle_created, '') == (42, REG_DWORD)
        >>> QueryValue(reg_handle, r'SOFTWARE\\lib_registry_test')
        Traceback (most recent call last):
            ...
        OSError: [WinError 13] The data is invalid

        >>> # Teardown
        >>> DeleteKey(reg_handle, r'SOFTWARE\\lib_registry_test')

        """

QueryValueEx
---------------

.. code-block:: python

    def QueryValueEx(key: Handle, value_name: Optional[str]) -> Tuple[RegData, int]:     # noqa
        """
        Retrieves data and type for a specified value name associated with an open registry key.

        If Value_name is '' or None, it queries the Default Value* of the Key - this will Fail if the Default Value for the Key is not Present.
        * Remark : this is the Value what is shown in Regedit as "(Standard)" or "(Default)"
        it is usually not set.

        the function does NOT accept named parameters, only positional parameters



        Parameter
        ---------

        key:
            the predefined handle to connect to, or one of the predefined HKEY_* constants.

        value_name:
            None, or a string that identifies the value to Query
            if value is None, or '' it queries the default Value of the Key



        Result
        ------

        The result is a tuple of 2 items:

        ==========  =====================================================================================================
        Index       Meaning
        ==========  =====================================================================================================
        0           The value of the registry item.
        1           An integer giving the registry type for this value see table
        ==========  =====================================================================================================



        Registry Types
        --------------

        ==============  ==============================  ==============================  ==========================================================================
        type(int)       type name                       accepted python Types           Description
        ==============  ==============================  ==============================  ==========================================================================
        0               REG_NONE	                    None, bytes                     No defined value type.
        1               REG_SZ	                        None, str                       A null-terminated string.
        2               REG_EXPAND_SZ	                None, str                       Null-terminated string containing references to
                                                                                        environment variables (%PATH%).
                                                                                        (Python handles this termination automatically.)
        3               REG_BINARY	                    None, bytes                     Binary data in any form.
        4               REG_DWORD	                    None, int                       A 32-bit number.
        4               REG_DWORD_LITTLE_ENDIAN	        None, int                       A 32-bit number in little-endian format.
        5               REG_DWORD_BIG_ENDIAN	        None, bytes                     A 32-bit number in big-endian format.
        6               REG_LINK	                    None, bytes                     A Unicode symbolic link.
        7               REG_MULTI_SZ	                None, List[str]                 A sequence of null-terminated strings, terminated by two null characters.
        8               REG_RESOURCE_LIST	            None, bytes                     A device-driver resource list.
        9               REG_FULL_RESOURCE_DESCRIPTOR    None, bytes                     A hardware setting.
        10              REG_RESOURCE_REQUIREMENTS_LIST  None, bytes                     A hardware resource list.
        11              REG_QWORD                       None, bytes                     A 64 - bit number.
        11              REG_QWORD_LITTLE_ENDIAN         None, bytes                     A 64 - bit number in little - endian format.Equivalent to REG_QWORD.
        ==============  ==============================  ==============================  ==========================================================================

        * all other integers for REG_TYPE are accepted, and written to the registry. The value is handled as binary.
        by that way You would be able to encode data in the REG_TYPE for stealth data not easy to spot - who would expect it.



        Exceptions
        ----------

        OSError: [WinError 6] The handle is invalid
            if parameter key is invalid

        TypeError: None is not a valid HKEY in this context
            if parameter key is None

        TypeError: The object is not a PyHKEY object
            if parameter key is not integer or PyHKEY type

        OverflowError: int too big to convert
            if parameter key is > 64 Bit Integer Value

        TypeError: QueryValueEx() argument 2 must be str or None, not <type>
            if the value_name is anything else then str or None

        TypeError: QueryValueEx() got some positional-only arguments passed as keyword arguments: '<key>'
            if a keyword (named) parameter was passed



        Events
        ------

        Raises an auditing event winreg.QueryValue with arguments key, sub_key, value_name. (NOT Implemented)



        Examples
        --------

        >>> # Setup
        >>> fake_registry = fake_reg_tools.get_minimal_windows_testregistry()
        >>> load_fake_registry(fake_registry)
        >>> reg_handle = ConnectRegistry(None, HKEY_LOCAL_MACHINE)
        >>> key_handle = OpenKey(reg_handle, r'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion')

        >>> # Read the current Version
        >>> QueryValueEx(key_handle, 'CurrentBuild')
        ('...', 1)

        >>> # Attempt to read a non Existing Default Value
        >>> QueryValueEx(key_handle, '')
        Traceback (most recent call last):
            ...
        FileNotFoundError: [WinError 2] The system cannot find the file specified

        >>> QueryValueEx(key_handle, None)
        Traceback (most recent call last):
            ...
        FileNotFoundError: [WinError 2] The system cannot find the file specified

        >>> # Set a Default Value
        >>> SetValueEx(key_handle, '',0 , REG_SZ, 'test_default_value')
        >>> QueryValueEx(key_handle, '')
        ('test_default_value', 1)

        >>> # Delete a Default Value
        >>> DeleteValue(key_handle, None)

        """

SetValue
---------------

.. code-block:: python

    def SetValue(key: Handle, sub_key: Union[str, None], type: int, value: str) -> None:      # noqa
        """
        Associates a value with a specified key. (the Default Value* of the Key, usually not set)

        * Remark : this is the Value what is shown in Regedit as "(Standard)" or "(Default)"
        it is usually not set. Nethertheless, even if the value is not set, QueryValue will deliver ''

        the function does NOT accept named parameters, only positional parameters


        Parameter
        ---------

        key:
            the predefined handle to connect to, or one of the predefined HKEY_* constants.

        sub_key:
            None, or a string that names the key this method sets the default value
            If the key specified by the sub_key parameter does not exist, the SetValue function creates it.

        type:
            an integer that specifies the type of the data. Currently this must be REG_SZ,
            meaning only strings are supported. Use the SetValueEx() function for support for other data types.

        value:
            a string that specifies the new value.
            Value lengths are limited by available memory. Long values (more than 2048 bytes) should be stored
            as files with the filenames stored in the configuration registry. This helps the registry perform efficiently.
            The key identified by the key parameter must have been opened with KEY_SET_VALUE access.    (NOT IMPLEMENTED)



        Exceptions
        ----------

        TypeError: Could not convert the data to the specified type.
            for REG_SZ and REG_EXPAND_SZ, if the data is not NoneType or str,
            for REG_DWORD and REG_EXPREG_QWORDAND_SZ, if the data is not NoneType or int,
            for REG_MULTI_SZ, if the data is not List[str]:

        TypeError: Objects of type '<data_type>' can not be used as binary registry values
            for all other REG_* types, if the data is not NoneType or bytes

        OSError: [WinError 6] The handle is invalid
            if parameter key is invalid

        TypeError: None is not a valid HKEY in this context
            if parameter key is None

        TypeError: The object is not a PyHKEY object
            if parameter key is not integer or PyHKEY type

        OverflowError: int too big to convert
            if parameter key is > 64 Bit Integer Value

        TypeError: SetValue() argument 2 must be str or None, not <type>
            if the subkey is anything else then str or None

        TypeError: SetValue() argument 3 must be int not None
            if the type is None

        TypeError: SetValue() argument 3 must be int not <type>
            if the type is anything else but int

        TypeError: type must be winreg.REG_SZ
            if the type is not string (winreg.REG_SZ)

        TypeError: SetValue() argument 4 must be str not None
            if the value is None

        TypeError: SetValue() argument 4 must be str not <type>
            if the value is anything else but str

        TypeError: SetValue() got some positional-only arguments passed as keyword arguments: '<key>'
            if a keyword (named) parameter was passed



        Events
        ------

        Raises an auditing event winreg.SetValue with arguments key, sub_key, type, value. (NOT IMPLEMENTED)



        Examples
        --------

        >>> # Setup
        >>> fake_registry = fake_reg_tools.get_minimal_windows_testregistry()
        >>> load_fake_registry(fake_registry)
        >>> reg_handle = ConnectRegistry(None, HKEY_CURRENT_USER)
        >>> key_handle = CreateKey(reg_handle, r'SOFTWARE\\lib_registry_test')

        >>> # read Default Value, which is ''
        >>> assert QueryValue(reg_handle, r'SOFTWARE\\lib_registry_test') == ''

        >>> # sub key can be ''
        >>> SetValue(key_handle, '', REG_SZ, 'test1')
        >>> assert QueryValue(reg_handle, r'SOFTWARE\\lib_registry_test') == 'test1'

        >>> # sub key can be None
        >>> SetValue(key_handle, None, REG_SZ, 'test2')
        >>> assert QueryValue(reg_handle, r'SOFTWARE\\lib_registry_test') == 'test2'

        >>> # use sub key
        >>> reg_handle_software = OpenKey(reg_handle, 'SOFTWARE')
        >>> SetValue(reg_handle_software, 'lib_registry_test', REG_SZ, 'test3')
        >>> assert QueryValue(reg_handle, r'SOFTWARE\\lib_registry_test') == 'test3'

        >>> # SetValue creates keys on the fly if they do not exist
        >>> reg_handle_software = OpenKey(reg_handle, 'SOFTWARE')
        >>> SetValue(reg_handle_software, r'lib_registry_test\\ham\\spam', REG_SZ, 'wonderful spam')
        >>> assert QueryValue(reg_handle, r'SOFTWARE\\lib_registry_test\\ham\\spam') == 'wonderful spam'

        >>> # You can not use other types as string here
        >>> SetValue(key_handle, '', REG_DWORD, "42")     # noqa
        Traceback (most recent call last):
            ...
        TypeError: type must be winreg.REG_SZ

        >>> # Tear Down
        >>> DeleteKey(reg_handle,r'SOFTWARE\\lib_registry_test\\ham\\spam')
        >>> DeleteKey(reg_handle,r'SOFTWARE\\lib_registry_test\\ham')
        >>> DeleteKey(reg_handle,r'SOFTWARE\\lib_registry_test')

        """

SetValueEx
---------------

.. code-block:: python

    def SetValueEx(key: Handle, value_name: Optional[str], reserved: int, type: int, value: RegData) -> None:    # noqa
        """
        Stores data in the value field of an open registry key.

        value_name is a string that names the subkey with which the value is associated.
        if value is None, or '' it sets the default value* of the Key

        the function does NOT accept named parameters, only positional parameters

        Parameter
        ---------

        key:
            the predefined handle to connect to, or one of the predefined HKEY_* constants.
            The key identified by the key parameter must have been opened with KEY_SET_VALUE access.    (NOT IMPLEMENTED))
            To open the key, use the CreateKey() or OpenKey() methods.

        value_name:
            None, or a string that identifies the value to set
            if value is None, or '' it sets the default value* of the Key

            * Remark : this is the Value what is shown in Regedit as "(Standard)" or "(Default)"
            it is usually not set, but You can set it to any data and datatype - but then it will
            only be readable with QueryValueEX, not with QueryValue

        reserved:
            reserved is a reserved integer, and should be zero. reserved can be anything – zero is always passed to the API.

        type:
            type is an integer that specifies the type of the data. (see table)

        value:
            value is a new value.
            Value lengths are limited by available memory. Long values (more than 2048 bytes)
            should be stored as files with the filenames stored in the configuration registry. This helps the registry perform efficiently.


        Registry Types

        ==============  ==============================  ==============================  ==========================================================================
        type(int)       type name                       accepted python Types           Description
        ==============  ==============================  ==============================  ==========================================================================
        0               REG_NONE	                    None, bytes                     No defined value type.
        1               REG_SZ	                        None, str                       A null-terminated string.
        2               REG_EXPAND_SZ	                None, str                       Null-terminated string containing references to
                                                                                        environment variables (%PATH%).
                                                                                        (Python handles this termination automatically.)
        3               REG_BINARY	                    None, bytes                     Binary data in any form.
        4               REG_DWORD	                    None, int                       A 32-bit number.
        4               REG_DWORD_LITTLE_ENDIAN	        None, int                       A 32-bit number in little-endian format.
        5               REG_DWORD_BIG_ENDIAN	        None, bytes                     A 32-bit number in big-endian format.
        6               REG_LINK	                    None, bytes                     A Unicode symbolic link.
        7               REG_MULTI_SZ	                None, List[str]                 A sequence of null-terminated strings, terminated by two null characters.
        8               REG_RESOURCE_LIST	            None, bytes                     A device-driver resource list.
        9               REG_FULL_RESOURCE_DESCRIPTOR    None, bytes                     A hardware setting.
        10              REG_RESOURCE_REQUIREMENTS_LIST  None, bytes                     A hardware resource list.
        11              REG_QWORD                       None, bytes                     A 64 - bit number.
        11              REG_QWORD_LITTLE_ENDIAN         None, bytes                     A 64 - bit number in little - endian format.Equivalent to REG_QWORD.
        ==============  ==============================  ==============================  ==========================================================================

        * all other integers for REG_TYPE are accepted, and written to the registry. The value is handled as binary.
        by that way You would be able to encode data in the REG_TYPE for stealth data not easy to spot - who would expect it.



        Exceptions
        ----------

        OSError: [WinError 6] The handle is invalid
            if parameter key is invalid

        TypeError: None is not a valid HKEY in this context
            if parameter key is None

        TypeError: The object is not a PyHKEY object
            if parameter key is not integer or PyHKEY type

        OverflowError: int too big to convert
            if parameter key is > 64 Bit Integer Value

        TypeError: SetValueEx() argument 2 must be str or None, not <type>
            if the value_name is anything else then str or None

        TypeError: SetValueEx() argument 4 must be int not None
            if the type is None

        TypeError: SetValueEx() argument 4 must be int not <type>
            if the type is anything else but int

        TypeError: SetValueEx() got some positional-only arguments passed as keyword arguments: '<key>'
            if a keyword (named) parameter was passed



        Events
        ------

        Raises an auditing event winreg.SetValue with arguments key, sub_key, type, value.          (NOT IMPLEMENTED)



        Examples
        --------

        >>> # Setup
        >>> fake_registry = fake_reg_tools.get_minimal_windows_testregistry()
        >>> load_fake_registry(fake_registry)
        >>> reg_handle = ConnectRegistry(None, HKEY_CURRENT_USER)
        >>> key_handle = CreateKey(reg_handle, r'Software\\lib_registry_test')

        >>> # Test
        >>> SetValueEx(key_handle, 'some_test', 0, REG_SZ, 'some_test_value')
        >>> assert QueryValueEx(key_handle, 'some_test') == ('some_test_value', REG_SZ)

        >>> # Test Overwrite
        >>> SetValueEx(key_handle, 'some_test', 0, REG_SZ, 'some_test_value2')
        >>> assert QueryValueEx(key_handle, 'some_test') == ('some_test_value2', REG_SZ)

        >>> # Test write Default Value of the Key, with value_name None
        >>> SetValueEx(key_handle, None, 0, REG_SZ, 'default_value')
        >>> assert QueryValue(key_handle, '') == 'default_value'

        >>> # Test write Default Value of the Key, with value_name ''
        >>> SetValueEx(key_handle, '', 0, REG_SZ, 'default_value_overwritten')
        >>> assert QueryValue(key_handle, '') == 'default_value_overwritten'

        >>> # Teardown
        >>> DeleteValue(key_handle, 'some_test')
        >>> DeleteKey(key_handle, '')

        """

Usage from Commandline
------------------------

.. code-block:: bash

   Usage: fake_winreg [OPTIONS] COMMAND [ARGS]...

     fake winreg, in order to test registry related functions on linux

   Options:
     --version                     Show the version and exit.
     --traceback / --no-traceback  return traceback information on cli
     -h, --help                    Show this message and exit.

   Commands:
     info  get program informations

Installation and Upgrade
------------------------

- Before You start, its highly recommended to update pip and setup tools:


.. code-block:: bash

    python -m pip --upgrade pip
    python -m pip --upgrade setuptools

- to install the latest release from PyPi via pip (recommended):

.. code-block:: bash

    python -m pip install --upgrade fake_winreg

- to install the latest version from github via pip:


.. code-block:: bash

    python -m pip install --upgrade git+https://github.com/bitranox/fake_winreg.git


- include it into Your requirements.txt:

.. code-block:: bash

    # Insert following line in Your requirements.txt:
    # for the latest Release on pypi:
    fake_winreg

    # for the latest development version :
    fake_winreg @ git+https://github.com/bitranox/fake_winreg.git

    # to install and upgrade all modules mentioned in requirements.txt:
    python -m pip install --upgrade -r /<path>/requirements.txt


- to install the latest development version from source code:

.. code-block:: bash

    # cd ~
    $ git clone https://github.com/bitranox/fake_winreg.git
    $ cd fake_winreg
    python setup.py install

- via makefile:
  makefiles are a very convenient way to install. Here we can do much more,
  like installing virtual environments, clean caches and so on.

.. code-block:: shell

    # from Your shell's homedirectory:
    $ git clone https://github.com/bitranox/fake_winreg.git
    $ cd fake_winreg

    # to run the tests:
    $ make test

    # to install the package
    $ make install

    # to clean the package
    $ make clean

    # uninstall the package
    $ make uninstall

Requirements
------------
following modules will be automatically installed :

.. code-block:: bash

    ## Project Requirements
    click
    cli_exit_tools @ git+https://github.com/bitranox/cli_exit_tools.git
    wrapt

Acknowledgements
----------------

- special thanks to "uncle bob" Robert C. Martin, especially for his books on "clean code" and "clean architecture"

Contribute
----------

I would love for you to fork and send me pull request for this project.
- `please Contribute <https://github.com/bitranox/fake_winreg/blob/master/CONTRIBUTING.md>`_

License
-------

This software is licensed under the `MIT license <http://en.wikipedia.org/wiki/MIT_License>`_

---

Changelog
=========

- new MAJOR version for incompatible API changes,
- new MINOR version for added functionality in a backwards compatible manner
- new PATCH version for backwards compatible bug fixes

planned:
    - KEY_* Permissions on SetValue, ReadValue, etc ...
    - test matrix on windows to compare fake and original winreg in detail
    - auditing events
    - investigate SYSWOW32/64 Views
    - Admin Permissions

v1.5.7
--------
2021-12-16: feature release
    - allow PyHKEY to act as a context manager

v1.5.6
--------
2020-10-09: service release
    - update travis build matrix for linux 3.9-dev
    - update travis build matrix (paths) for windows 3.9 / 3.10

v1.5.5
--------
2020-08-08: service release
    - fix documentation
    - fix travis
    - deprecate pycodestyle
    - implement flake8

v1.5.4
---------
2020-08-01: fix pypi deploy

v1.5.3
--------
2020-07-31: fix travis build


v0.5.2
--------
2020-07-29: feature release
    - use the new pizzacutter template
    - use cli_exit_tools

v0.5.1
--------
2020-07-16 : patch release
    - fix cli test
    - enable traceback option on cli errors

v0.5.0
--------
2020-07-13 : feature release
    - CreateKeyEx added
    - access rights on CreateKey, CreateKeyEx, OpenKey, OpenKeyEX added

v0.4.1
--------
2020-07-13 : patch release
    - 100% coverage
    - raise correct Exception when try to connect to Network Computer

v0.4.0
--------
2020-07-13 : feature release
    - raise [WinError 1707] The network address is invalid if computername is given
    - make HKEYType int convertible
    - make type aliases for better readability
    - coverage

v0.3.1
--------
2020-07-12 : patch release
    - corrected types

v0.3.0
--------
2020-07-12 : feature release
    - raise Errors on SetValueEx if type is not appropriate
    - raise Errors on wrong parameter types like original winreg
    - comprehensive documentation

v0.2.0
--------
2020-07-11 : feature release
    - added EnumValue
    - added Close() and Detach() for PyHKEY Class
    - more consistent naming in internal methods
    - added winerror attributes and values in exceptions
    - corrected handling of default key values
    - corrected race condition when deleting keys
    - corrected decorator to check for names arguments
    - added stub file for wrapt
    - added more REG_* Types

v0.1.1
--------
2020-07-08 : patch release
    - new click CLI
    - use PizzaCutter Template
    - added jupyter notebook
    - reorganized modules and import
    - updated documentation

v0.1.0
--------
2020-06-17: initial public release
    - with all docs in place

