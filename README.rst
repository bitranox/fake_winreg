fake_winreg
===========

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

tested on linux "bionic" with python 3.6, 3.7, 3.8, 3.8-dev, pypy3

`100% code coverage <https://codecov.io/gh/bitranox/fake_winreg>`_, codestyle checking ,mypy static type checking ,tested under `Linux, macOS, Windows <https://travis-ci.org/bitranox/fake_winreg>`_, automatic daily builds and monitoring

----

- `Try it Online`_
- `Installation and Upgrade`_
- `Usage`_
- `Usage from Commandline`_
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

Installation and Upgrade
------------------------

- Before You start, its highly recommended to update pip and setup tools:


.. code-block:: bash

    python -m pip --upgrade pip
    python -m pip --upgrade setuptools
    python -m pip --upgrade wheel

- to install the latest release from PyPi via pip (recommended):

.. code-block:: bash

    # install latest release from PyPi
    python -m pip install --upgrade fake_winreg

    # test latest release from PyPi without installing (can be skipped)
    python -m pip install fake_winreg --install-option test

- to install the latest development version from github via pip:


.. code-block:: bash

    # normal install
    python -m pip install --upgrade git+https://github.com/bitranox/fake_winreg.git

    # to test without installing (can be skipped)
    python -m pip install git+https://github.com/bitranox/fake_winreg.git --install-option test

    # to install and upgrade all dependencies regardless of version number
    python -m pip install --upgrade git+https://github.com/bitranox/fake_winreg.git --upgrade-strategy eager


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

    # to test without installing (can be skipped)
    python setup.py test

    # normal install
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

ConnectRegistry
---------------

.. code-block:: python

    def ConnectRegistry(computer_name: Union[None, str], key: Union[int, HKEYType, PyHKEY]) -> PyHKEY:     # noqa
        """
        Establishes a connection to a predefined registry handle on another computer, and returns a handle object.
        the function does NOT accept named parameters, only positional parameters

        :parameter computer_name:
            the name of the remote computer (NOT IMPLEMENTED), of the form r"\\computername".
            If None, the local computer is used.

        :parameter key:
            the predefined handle to connect to, or one of the predefined HKEY_* constants.

        :returns
            the handle of the opened key. If the function fails, an OSError exception is raised.

        :raises
            FileNotFoundError: System error 53...                   , if can not connect to remote computer

            OSError: [WinError 6] The handle is invalid             , if parameter key is invalid

            TypeError: None is not a valid HKEY in this context     , if parameter key is None

            TypeError: The object is not a PyHKEY object            , if parameter key is not integer or PyHKEY type

            OverflowError: int too big to convert                   , if parameter key is > 64 Bit Integer Value

        :events
            winreg.ConnectRegistry auditing event (NOT IMPLEMENTED), with arguments computer_name, key.

CloseKey
---------------

.. code-block:: python

    def CloseKey(hkey: Union[int, HKEYType]) -> None:      # noqa
        """
        Closes a previously opened registry key.

        the function does NOT accept named parameters, only positional parameters

        Note: If hkey is not closed using this method (or via hkey.Close()), it is closed when the hkey object is destroyed by Python.

        :parameter hkey:
            the predefined handle to connect to, or one of the predefined HKEY_* constants.

        :raises
            OSError: [WinError 6] The handle is invalid             , if parameter key is invalid

            TypeError: The object is not a PyHKEY object            , if parameter key is not integer or PyHKEY type

            OverflowError: int too big to convert                   , if parameter key is > 64 Bit Integer Value

CreateKey
---------------

.. code-block:: python

    def CreateKey(key: Union[int, HKEYType, PyHKEY], sub_key: Union[str, None]) -> PyHKEY:      # noqa
        """
        Creates or opens the specified key, returning a handle object.
        The sub_key can contain a directory structure like r'Software\\xxx\\yyy' - all the parents to yyy will be created
        the function does NOT accept named parameters, only positional parameters

        :parameter key:
            an already open key, or one of the predefined HKEY_* constants.

        :parameter sub_key:
            None, or a string that names the key this method opens or creates.
            If key is one of the predefined keys, sub_key may be None. In that case,
            the handle returned is the same key handle passed in to the function.
            If the key already exists, this function opens the existing key.

        :returns
            the handle of the opened key.

        :raises
            OSError: [WinError 1010] The configuration registry key is invalid  , if the function fails to create the Key

            OSError: [WinError 6] The handle is invalid                         , if parameter key is invalid

            TypeError: None is not a valid HKEY in this context                 , if parameter key is None

            TypeError: The object is not a PyHKEY object                        , if parameter key is not integer or PyHKEY type

            OverflowError: int too big to convert                               , if parameter key is > 64 Bit Integer Value

            TypeError: CreateKey() argument 2 must be str or None, not <type>   , if the subkey is anything else then str or None

        :events:
            Raises an auditing event winreg.CreateKey with arguments key, sub_key, access. (NOT IMPLEMENTED)

            Raises an auditing event winreg.OpenKey/result with argument key. (NOT IMPLEMENTED)

DeleteKey
---------------

.. code-block:: python

    def DeleteKey(key: Union[int, HKEYType, PyHKEY], sub_key: str) -> None:         # noqa
        """
        Deletes the specified key. This method can not delete keys with subkeys.
        If the method succeeds, the entire key, including all of its values, is removed.
        the function does NOT accept named parameters, only positional parameters

        :parameter key:
            an already open key, or one of the predefined HKEY_* constants.

        :parameter sub_key:
            a string that must be a subkey of the key identified by the key parameter or ''.
            sub_key must not be None, and the key may not have subkeys.

        :raises
            OSError ...                                                                 , if it fails to Delete the Key

            PermissionError: [WinError 5] Access is denied                              , if the key specified to be deleted have subkeys

            FileNotFoundError: [WinError 2] The system cannot find the file specified   , if the Key specified to be deleted does not exist

            TypeError: DeleteKey() argument 2 must be str, not <type>                   , if parameter sub_key type is anything else but string

            OSError: [WinError 6] The handle is invalid                                 , if parameter key is invalid

            TypeError: None is not a valid HKEY in this context                         , if parameter key is None

            TypeError: The object is not a PyHKEY object                                , if parameter key is not integer or PyHKEY type

            OverflowError: int too big to convert                                       , if parameter key is > 64 Bit Integer Value

        :events:
            Raises an auditing event winreg.DeleteKey with arguments key, sub_key, access. (NOT IMPLEMENTED)

DeleteKeyEx
---------------

.. code-block:: python

    def DeleteKeyEx(key: Union[int, HKEYType, PyHKEY], sub_key: str, access: int = KEY_WOW64_64KEY, reserved: int = 0) -> None:     # noqa
        """
        Deletes the specified key. This method can not delete keys with subkeys.
        If the method succeeds, the entire key, including all of its values, is removed.
        the function does NOT accept named parameters, only positional parameters

        Note The DeleteKeyEx() function is implemented with the RegDeleteKeyEx Windows API function,
        which is specific to 64-bit versions of Windows. See the RegDeleteKeyEx documentation.

        :parameter key:
            an already open key, or one of the predefined HKEY_* constants.

        :parameter sub_key:
            a string that must be a subkey of the key identified by the key parameter or ''.
            sub_key must not be None, and the key may not have subkeys.

        :parameter access:
            a integer that specifies an access mask that describes the desired security access for the key.
            Default is KEY_WOW64_64KEY. See Access Rights for other allowed values. (NOT IMPLEMENTED)
            (any integer is accepted here in original winreg

        :parameter reserved:
            reserved is a reserved integer, and must be zero. The default is zero.

        :raises
            OSError: ...                                                                , if it fails to Delete the Key

            PermissionError: [WinError 5] Access is denied                              , if the key specified to be deleted have subkeys

            FileNotFoundError: [WinError 2] The system cannot find the file specified   , if the Key specified to be deleted does not exist

            OSError: [WinError 6] The handle is invalid                                 , if parameter key is invalid

            TypeError: None is not a valid HKEY in this context                         , if parameter key is None

            TypeError: The object is not a PyHKEY object                                , if parameter key is not integer or PyHKEY type

            OverflowError: int too big to convert                                       , if parameter key is > 64 Bit Integer Value

            NotImplementedError: On unsupported Windows versions (NOT IMPLEMENTED)

            TypeError: DeleteKey() argument 2 must be str, not <type>                   , if parameter sub_key type is anything else but string

            TypeError: an integer is required (got NoneType)                            , if parameter access is None

            TypeError: an integer is required (got type <type>)                         , if parameter access is not int

            OverflowError: Python int too large to convert to C long                    , if parameter access is > 64 Bit Integer Value

            TypeError: an integer is required (got type <type>)                         , if parameter reserved is not int

            OverflowError: Python int too large to convert to C long                    , if parameter reserved is > 64 Bit Integer Value

            OSError: WinError 87 The parameter is incorrect                             , if parameter reserved is not 0

        :events:
            Raises an auditing event winreg.DeleteKey with arguments key, sub_key, access. (NOT IMPLEMENTED)

DeleteValue
---------------

.. code-block:: python

    def DeleteValue(key: Union[int, HKEYType, PyHKEY], value: Optional[str]) -> None:         # noqa
        """
        Removes a named value from a registry key.
        the function does NOT accept named parameters, only positional parameters

        :parameter key:
            an already open key, or one of the predefined HKEY_* constants.

        :parameter value:
            None, or a string that identifies the value to remove.
            if value is None, or '' it deletes the default Value of the Key

        :raises
            FileNotFoundError: [WinError 2] The system cannot find the file specified'  , if the Value specified to be deleted does not exist

            OSError: [WinError 6] The handle is invalid                                 , if parameter key is invalid

            TypeError: None is not a valid HKEY in this context                         , if parameter key is None

            TypeError: The object is not a PyHKEY object                                , if parameter key is not integer or PyHKEY type

            OverflowError: int too big to convert                                       , if parameter key is > 64 Bit Integer Value

            TypeError: DeleteValue() argument 2 must be str or None, not <type>         , if parameter value type is anything else but string or None

        :events
            Raises an auditing event winreg.DeleteValue with arguments key, value. (NOT IMPLEMENTED)

EnumKey
---------------

.. code-block:: python

    def EnumKey(key: Union[int, HKEYType, PyHKEY], index: int) -> str:              # noqa
        """
        Enumerates subkeys of an open registry key, returning a string.
        The function retrieves the name of one subkey each time it is called.
        It is typically called repeatedly until an OSError exception is raised,
        indicating, no more values are available.
        the function does NOT accept named parameters, only positional parameters

        :parameter key:
            an already open key, or one of the predefined HKEY_* constants.

        :parameter index:
            an integer that identifies the index of the key to retrieve.

        :raises
            OSError: [WinError 259] No more data is available                           , if the index is out of Range

            OSError: [WinError 6] The handle is invalid                                 , if parameter key is invalid

            TypeError: None is not a valid HKEY in this context                         , if parameter key is None

            TypeError: The object is not a PyHKEY object                                , if parameter key is not integer or PyHKEY type

            OverflowError: int too big to convert                   , if parameter key is > 64 Bit Integer Value

            (no check for overflow of key on this method !)

            TypeError: an integer is required (got type <type>)                         , if parameter index is type different from int

            OverflowError: Python int too large to convert to C int                     , if parameter index is > 64 Bit Integer Value

        :events:
            Raises an auditing event winreg.EnumKey with arguments key, index. (NOT IMPLEMENTED)

EnumValue
---------------

.. code-block:: python

    def EnumValue(key: Union[int, HKEYType, PyHKEY], index: int) -> Tuple[str, Union[None, bytes, int, str, List[str]], int]:              # noqa
        """
        Enumerates values of an open registry key, returning a tuple.
        The function retrieves the name of one value each time it is called.
        It is typically called repeatedly, until an OSError exception is raised, indicating no more values.
        the function does NOT accept named parameters, only positional parameters

        The result is a tuple of 3 items:

        ========    ==============================================================================================
        Index       Meaning
        ========    ==============================================================================================
        0           A string that identifies the value name
        1           An object that holds the value data, and whose type depends on the underlying registry type
        2           An integer giving the registry type for this value (see table in docs for SetValueEx())
        ========    ==============================================================================================

        :parameter key:
            an already open key, or one of the predefined HKEY_* constants.

        :parameter index:
            an integer that identifies the index of the key to retrieve.

        :raises
            OSError: [WinError 259] No more data is available                           , if the index is out of Range

            OSError: [WinError 6] The handle is invalid                                 , if parameter key is invalid

            TypeError: None is not a valid HKEY in this context                         , if parameter key is None

            TypeError: The object is not a PyHKEY object                                , if parameter key is not integer or PyHKEY type

            OverflowError: int too big to convert                                       , if parameter key is > 64 Bit Integer Value

            TypeError: an integer is required (got type <type>)                         , if parameter index is type different from int

            OverflowError: Python int too large to convert to C int                     , if parameter index is > 64 Bit Integer Value

        :events
            Raises an auditing event winreg.EnumValue with arguments key, index. (NOT IMPLEMENTED)

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

        * all other integers are accepted and written to the registry and handled as binary,
        so You would be able to encode data in the REG_TYPE for stealth data not easy to spot - who would expect it.

OpenKey
---------------

.. code-block:: python

    def OpenKey(key: Union[int, HKEYType, PyHKEY], sub_key: Union[str, None], reserved: int = 0, access: int = KEY_READ) -> PyHKEY:         # noqa
        """
        Opens the specified key, the result is a new handle to the specified key.
        one of the few functions of winreg that accepts named parameters

        :parameter key:
            an already open key, or one of the predefined HKEY_* constants.

        :parameter sub_key:
            None, or a string that names the key this method opens or creates.
            If key is one of the predefined keys, sub_key may be None.

        :parameter reserved:
            reserved is a reserved integer, and should be zero. The default is zero.


        :parameter access:
            a integer that specifies an access mask that describes the desired security access for the key.
            Default is KEY_READ. See Access Rights for other allowed values. (NOT IMPLEMENTED)
            (any integer is accepted here in original winreg)

        :raises
            OSError: ...                                                                , if it fails to open the key

            OSError: [WinError 6] The handle is invalid                                 , if parameter key is invalid

            TypeError: None is not a valid HKEY in this context                         , if parameter key is None

            TypeError: The object is not a PyHKEY object                                , if parameter key is not integer or PyHKEY type

            OverflowError: int too big to convert                                       , if parameter key is > 64 Bit Integer Value

            TypeError: OpenKey() argument 2 must be str or None, not <type>             , if the sub_key is anything else then str or None

            TypeError: an integer is required (got NoneType)                            , if parameter reserved is None

            TypeError: an integer is required (got type <type>)                         , if parameter reserved is not int

            PermissionError: [WinError 5] Access denied                                 , if parameter reserved is > 3)

            OverflowError: Python int too large to convert to C long                    , if parameter reserved is > 64 Bit Integer Value

            OSError: [WinError 87] The parameter is incorrect                           , on some values (for instance 455565) NOT IMPLEMENTED

            TypeError: an integer is required (got type <type>)                         , if parameter access is not int

            OverflowError: Python int too large to convert to C long                    , if parameter access is > 64 Bit Integer Value



        :events
            Raises an auditing event winreg.OpenKey with arguments key, sub_key, access.    # not implemented
            Raises an auditing event winreg.OpenKey/result with argument key.               # not implemented

OpenKeyEx
---------------

.. code-block:: python

    def OpenKeyEx(key: Union[int, HKEYType, PyHKEY], sub_key: Optional[str], reserved: int = 0, access: int = KEY_READ) -> PyHKEY:        # noqa
        """
        Opens the specified key, the result is a new handle to the specified key.
        one of the few functions of winreg that accepts named parameters

        :parameter key:
            an already open key, or one of the predefined HKEY_* constants.

        :parameter sub_key:
            None, or a string that names the key this method opens or creates.
            If key is one of the predefined keys, sub_key may be None.

        :parameter reserved:
            reserved is a reserved integer, and should be zero. The default is zero.


        :parameter access:
            a integer that specifies an access mask that describes the desired security access for the key.
            Default is KEY_READ. See Access Rights for other allowed values. (NOT IMPLEMENTED)
            (any integer is accepted here in original winreg)

        :raises
            OSError: ...                                                                , if it fails to open the key

            OSError: [WinError 6] The handle is invalid                                 , if parameter key is invalid

            TypeError: None is not a valid HKEY in this context                         , if parameter key is None

            TypeError: The object is not a PyHKEY object                                , if parameter key is not integer or PyHKEY type

            OverflowError: int too big to convert                                       , if parameter key is > 64 Bit Integer Value

            TypeError: OpenKeyEx() argument 2 must be str or None, not <type>           , if the subkey is anything else then str or None

            TypeError: an integer is required (got NoneType)                            , if parameter reserved is None

            TypeError: an integer is required (got type <type>)                         , if parameter reserved is not int

            PermissionError: [WinError 5] Access denied                                 , if parameter reserved is > 3)

            OverflowError: Python int too large to convert to C long                    , if parameter reserved is > 64 Bit Integer Value

            OSError: [WinError 87] The parameter is incorrect                           , on some values (for instance 455565) NOT IMPLEMENTED

            TypeError: an integer is required (got type <type>)                         , if parameter access is not int

            OverflowError: Python int too large to convert to C long                    , if parameter access is > 64 Bit Integer Value


        :events
            Raises an auditing event winreg.OpenKey with arguments key, sub_key, access.    # not implemented
            Raises an auditing event winreg.OpenKey/result with argument key.               # not implemented

QueryInfoKey
---------------

.. code-block:: python

    def QueryInfoKey(key: Union[int, HKEYType, PyHKEY]) -> Tuple[int, int, int]:            # noqa
        """
        Returns information about a key, as a tuple.
        the function does NOT accept named parameters, only positional parameters

        :parameter key:
            the predefined handle to connect to, or one of the predefined HKEY_* constants.

        :returns

            The result is a tuple of 3 items:

            ======  =============================================================================================================
            Index,  Meaning
            ======  =============================================================================================================
            0       An integer giving the number of sub keys this key has.
            1       An integer giving the number of values this key has.
            2       An integer giving when the key was last modified (if available) as 100’s of nanoseconds since Jan 1, 1601.
            ======  =============================================================================================================

        :raises

            OSError: [WinError 6] The handle is invalid             , if parameter key is invalid

            TypeError: None is not a valid HKEY in this context     , if parameter key is None

            TypeError: The object is not a PyHKEY object            , if parameter key is not integer or PyHKEY type

            OverflowError: int too big to convert                   , if parameter key is > 64 Bit Integer Value

        :events
            Raises an auditing event winreg.QueryInfoKey with argument key.

QueryValue
---------------

.. code-block:: python

    def QueryValue(key: Union[int, HKEYType, PyHKEY], sub_key: Union[str, None]) -> str:        # noqa
        """
        Retrieves the unnamed value (the default value*) for a key, as string.

        * Remark : this is the Value what is shown in Regedit as "(Standard)" or "(Default)"
        it is usually not set. Nethertheless, even if the value is not set, QueryValue will deliver ''

        Values in the registry have name, type, and data components.

        This method retrieves the data for a key’s first value that has a NULL name.
        But the underlying API call doesn’t return the type, so always use QueryValueEx() if possible.

        the function does NOT accept named parameters, only positional parameters

        :parameter key:
            the predefined handle to connect to, or one of the predefined HKEY_* constants.

        :parameter sub_key:
            None, or a string that names the key this method opens or creates.
            If key is one of the predefined keys, sub_key may be None. In that case,
            the handle returned is the same key handle passed in to the function.
            If the key already exists, this function opens the existing key.

        :returns
            the unnamed value as string (if possible)

        :raises

            OSError: [WinError 13] The data is invalid                          , if the data in the unnamed value is not string

            OSError: [WinError 6] The handle is invalid                         , if parameter key is invalid

            TypeError: None is not a valid HKEY in this context                 , if parameter key is None

            TypeError: The object is not a PyHKEY object                        , if parameter key is not integer or PyHKEY type

            OverflowError: int too big to convert                               , if parameter key is > 64 Bit Integer Value

            TypeError: QueryValue() argument 2 must be str or None, not <type>  , if the subkey is anything else then str or None

        :events:
            Raises an auditing event winreg.QueryValue with arguments key, sub_key, value_name. (NOT IMPLEMENTED)

QueryValueEx
---------------

.. code-block:: python

    def QueryValueEx(key: Union[int, HKEYType, PyHKEY], value_name: Optional[str]) -> Tuple[Union[None, bytes, int, str, List[str]], int]:     # noqa
        """
        Retrieves data and type for a specified value name associated with an open registry key.

        If Value_name is '' or None, it queries the Default Value* of the Key - this will Fail if the Default Value for the Key is not Present.
        * Remark : this is the Value what is shown in Regedit as "(Standard)" or "(Default)"
        it is usually not set.

        the function does NOT accept named parameters, only positional parameters

        :parameter key:
            the predefined handle to connect to, or one of the predefined HKEY_* constants.

        :parameter value_name:
            None, or a string that identifies the value to Query
            if value is None, or '' it queries the default Value of the Key


        :raises

            OSError: [WinError 6] The handle is invalid                             , if parameter key is invalid

            TypeError: None is not a valid HKEY in this context                     , if parameter key is None

            TypeError: The object is not a PyHKEY object                            , if parameter key is not integer or PyHKEY type

            OverflowError: int too big to convert                                   , if parameter key is > 64 Bit Integer Value

            TypeError: QueryValueEx() argument 2 must be str or None, not <type>    , if the value_name is anything else then str or None


        :events
            Raises an auditing event winreg.QueryValue with arguments key, sub_key, value_name. (NOT Implemented)


        The result is a tuple of 2 items:

        ==========  =====================================================================================================
        Index       Meaning
        ==========  =====================================================================================================
        0           The value of the registry item.
        1           An integer giving the registry type for this value see table
        ==========  =====================================================================================================


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

        * all other integers are accepted and written to the registry and handled as binary,
        so You would be able to encode data in the REG_TYPE for stealth data not easy to spot - who would expect it.

SetValue
---------------

.. code-block:: python

    def SetValue(key: Union[int, HKEYType, PyHKEY], sub_key: Union[str, None], type: int, value: str) -> None:      # noqa
        """
        Associates a value with a specified key. (the Default Value* of the Key, usually not set)

        * Remark : this is the Value what is shown in Regedit as "(Standard)" or "(Default)"
        it is usually not set. Nethertheless, even if the value is not set, QueryValue will deliver ''

        the function does NOT accept named parameters, only positional parameters


        :parameter key:
            the predefined handle to connect to, or one of the predefined HKEY_* constants.

        :parameter sub_key:
            None, or a string that names the key this method sets the default value
            If the key specified by the sub_key parameter does not exist, the SetValue function creates it.

        :parameter type:
            an integer that specifies the type of the data. Currently this must be REG_SZ,
            meaning only strings are supported. Use the SetValueEx() function for support for other data types.

        :parameter value:
            a string that specifies the new value.
            Value lengths are limited by available memory. Long values (more than 2048 bytes) should be stored
            as files with the filenames stored in the configuration registry. This helps the registry perform efficiently.
            The key identified by the key parameter must have been opened with KEY_SET_VALUE access.    (NOT IMPLEMENTED)

        :raises

            OSError: [WinError 6] The handle is invalid                         , if parameter key is invalid

            TypeError: None is not a valid HKEY in this context                 , if parameter key is None

            TypeError: The object is not a PyHKEY object                        , if parameter key is not integer or PyHKEY type

            OverflowError: int too big to convert                               , if parameter key is > 64 Bit Integer Value

            TypeError: SetValue() argument 2 must be str or None, not <type>    , if the subkey is anything else then str or None

            TypeError: SetValue() argument 3 must be int not None               , if the type is None

            TypeError: SetValue() argument 3 must be int not <type>             , if the type is anything else but int

            TypeError: type must be winreg.REG_SZ                               , if the type is not string (winreg.REG_SZ)

            TypeError: SetValue() argument 4 must be str not None               , if the value is None

            TypeError: SetValue() argument 4 must be str not <type>             , if the value is anything else but str

        :events
            Raises an auditing event winreg.SetValue with arguments key, sub_key, type, value. (NOT IMPLEMENTED)

SetValueEx
---------------

.. code-block:: python

    def SetValueEx(key: Union[int, HKEYType, PyHKEY], value_name: Optional[str], reserved: int, type: int, value: Union[None, bytes, int, str, List[str]]) -> None:    # noqa
        """
        Stores data in the value field of an open registry key.

        value_name is a string that names the subkey with which the value is associated.
        if value is None, or '' it sets the default value* of the Key

        the function does NOT accept named parameters, only positional parameters

        :parameter key:
            the predefined handle to connect to, or one of the predefined HKEY_* constants.
            The key identified by the key parameter must have been opened with KEY_SET_VALUE access.    (NOT IMPLEMENTED))
            To open the key, use the CreateKey() or OpenKey() methods.

        :parameter value_name:
            None, or a string that identifies the value to set
            if value is None, or '' it sets the default value* of the Key

            * Remark : this is the Value what is shown in Regedit as "(Standard)" or "(Default)"
            it is usually not set, but You can set it to any data and datatype - but then it will
            only be readable with QueryValueEX, not with QueryValue

        :parameter reserved:
            reserved is a reserved integer, and should be zero. reserved can be anything – zero is always passed to the API.

        :parameter type:
            type is an integer that specifies the type of the data. (see table)

        :parameter value:
            value is a new value.
            Value lengths are limited by available memory. Long values (more than 2048 bytes)
            should be stored as files with the filenames stored in the configuration registry. This helps the registry perform efficiently.


        :raises

            OSError: [WinError 6] The handle is invalid                         , if parameter key is invalid

            TypeError: None is not a valid HKEY in this context                 , if parameter key is None

            TypeError: The object is not a PyHKEY object                        , if parameter key is not integer or PyHKEY type

            OverflowError: int too big to convert                               , if parameter key is > 64 Bit Integer Value

            TypeError: SetValueEx() argument 2 must be str or None, not <type>  , if the value_name is anything else then str or None

            TypeError: SetValueEx() argument 4 must be int not None             , if the type is None

            TypeError: SetValueEx() argument 4 must be int not <type>           , if the type is anything else but int

        :events
            Raises an auditing event winreg.SetValue with arguments key, sub_key, type, value.          (NOT IMPLEMENTED)

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

        * all other integers are accepted and written to the registry and handled as binary,
        so You would be able to encode data in the REG_TYPE for stealth data not easy to spot - who would expect it.

Usage from Commandline
------------------------

.. code-block:: bash

   Usage: fake_winreg [OPTIONS] COMMAND [ARGS]...

     fake winreg, in order to test registry related functions on linux

   Options:
     --version   Show the version and exit.
     -h, --help  Show this message and exit.

   Commands:
     info  get program informations

Requirements
------------
following modules will be automatically installed :

.. code-block:: bash

    ## Project Requirements
    click
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

0.3.1
-----
2020-07-12 : patch release
    - corrected types

0.3.0
-----
2020-07-12 : feature release
    - raise Errors on SetValueEx if type is not appropriate
    - raise Errors on wrong parameter types like original winreg
    - comprehensive documentation

0.2.0
-----
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

0.1.1
-----
2020-07-08 : patch release
    - new click CLI
    - use PizzaCutter Template
    - added jupyter notebook
    - reorganized modules and import
    - updated documentation

0.1.0
-----
2020-06-17: initial public release
    - with all docs in place

