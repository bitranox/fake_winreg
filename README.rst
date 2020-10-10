lib_registry
============


Version v2.0.7 as of 2020-10-10 see `Changelog`_

|travis_build| |license| |jupyter| |pypi|

|codecov| |better_code| |cc_maintain| |cc_issues| |cc_coverage| |snyk|


.. |travis_build| image:: https://img.shields.io/travis/bitranox/lib_registry/master.svg
   :target: https://travis-ci.org/bitranox/lib_registry

.. |license| image:: https://img.shields.io/github/license/webcomics/pywine.svg
   :target: http://en.wikipedia.org/wiki/MIT_License

.. |jupyter| image:: https://mybinder.org/badge_logo.svg
 :target: https://mybinder.org/v2/gh/bitranox/lib_registry/master?filepath=lib_registry.ipynb

.. for the pypi status link note the dashes, not the underscore !
.. |pypi| image:: https://img.shields.io/pypi/status/lib-registry?label=PyPI%20Package
   :target: https://badge.fury.io/py/lib_registry

.. |codecov| image:: https://img.shields.io/codecov/c/github/bitranox/lib_registry
   :target: https://codecov.io/gh/bitranox/lib_registry

.. |better_code| image:: https://bettercodehub.com/edge/badge/bitranox/lib_registry?branch=master
   :target: https://bettercodehub.com/results/bitranox/lib_registry

.. |cc_maintain| image:: https://img.shields.io/codeclimate/maintainability-percentage/bitranox/lib_registry?label=CC%20maintainability
   :target: https://codeclimate.com/github/bitranox/lib_registry/maintainability
   :alt: Maintainability

.. |cc_issues| image:: https://img.shields.io/codeclimate/issues/bitranox/lib_registry?label=CC%20issues
   :target: https://codeclimate.com/github/bitranox/lib_registry/maintainability
   :alt: Maintainability

.. |cc_coverage| image:: https://img.shields.io/codeclimate/coverage/bitranox/lib_registry?label=CC%20coverage
   :target: https://codeclimate.com/github/bitranox/lib_registry/test_coverage
   :alt: Code Coverage

.. |snyk| image:: https://img.shields.io/snyk/vulnerabilities/github/bitranox/lib_registry
   :target: https://snyk.io/test/github/bitranox/lib_registry

.. |black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black

a more pythonic way to access the windows registry as winreg

command line interface is prepared - if someone needs to use it via commandline, give me a note.

----

automated tests, Travis Matrix, Documentation, Badges, etc. are managed with `PizzaCutter <https://github
.com/bitranox/PizzaCutter>`_ (cookiecutter on steroids)

Python version required: 3.6.0 or newer

tested on linux "bionic" with python 3.6, 3.7, 3.8, 3.9-dev, pypy3 - architectures: amd64, ppc64le, s390x, arm64

`100% code coverage <https://codecov.io/gh/bitranox/lib_registry>`_, flake8 style checking ,mypy static type checking ,tested under `Linux, macOS, Windows <https://travis-ci.org/bitranox/lib_registry>`_, automatic daily builds and monitoring

----

- `Try it Online`_
- `Usage`_
- `Usage from Commandline`_
- `Installation and Upgrade`_
- `Requirements`_
- `Acknowledgements`_
- `Contribute`_
- `Report Issues <https://github.com/bitranox/lib_registry/blob/master/ISSUE_TEMPLATE.md>`_
- `Pull Request <https://github.com/bitranox/lib_registry/blob/master/PULL_REQUEST_TEMPLATE.md>`_
- `Code of Conduct <https://github.com/bitranox/lib_registry/blob/master/CODE_OF_CONDUCT.md>`_
- `License`_
- `Changelog`_

----

Try it Online
-------------

You might try it right away in Jupyter Notebook by using the "launch binder" badge, or click `here <https://mybinder.org/v2/gh/{{rst_include.
repository_slug}}/master?filepath=lib_registry.ipynb>`_

Usage
-----------

python methods:

- Registry Object

.. code-block:: python

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

- create_key

.. code-block:: python

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

- delete_key

.. code-block:: python

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

- key_exists

.. code-block:: python

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

Usage from Commandline
------------------------

.. code-block:: bash

   Usage: lib_registry [OPTIONS] COMMAND [ARGS]...

     a more pythonic way to access the windows registry as winreg

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

    python -m pip install --upgrade lib_registry

- to install the latest version from github via pip:


.. code-block:: bash

    python -m pip install --upgrade git+https://github.com/bitranox/lib_registry.git


- include it into Your requirements.txt:

.. code-block:: bash

    # Insert following line in Your requirements.txt:
    # for the latest Release on pypi:
    lib_registry

    # for the latest development version :
    lib_registry @ git+https://github.com/bitranox/lib_registry.git

    # to install and upgrade all modules mentioned in requirements.txt:
    python -m pip install --upgrade -r /<path>/requirements.txt


- to install the latest development version from source code:

.. code-block:: bash

    # cd ~
    $ git clone https://github.com/bitranox/lib_registry.git
    $ cd lib_registry
    python setup.py install

- via makefile:
  makefiles are a very convenient way to install. Here we can do much more,
  like installing virtual environments, clean caches and so on.

.. code-block:: shell

    # from Your shell's homedirectory:
    $ git clone https://github.com/bitranox/lib_registry.git
    $ cd lib_registry

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
    fake_winreg @ git+https://github.com/bitranox/fake_winreg.git

Acknowledgements
----------------

- special thanks to "uncle bob" Robert C. Martin, especially for his books on "clean code" and "clean architecture"

Contribute
----------

I would love for you to fork and send me pull request for this project.
- `please Contribute <https://github.com/bitranox/lib_registry/blob/master/CONTRIBUTING.md>`_

License
-------

This software is licensed under the `MIT license <http://en.wikipedia.org/wiki/MIT_License>`_

---

Changelog
=========

- new MAJOR version for incompatible API changes,
- new MINOR version for added functionality in a backwards compatible manner
- new PATCH version for backwards compatible bug fixes

tasks:
    - test if caching of handles make sense, especially on network
    - documentation update
    - pathlib-like Interface
    - jupyter notebook update

v2.0.7
--------
2020-10-10: fix minor bugs

v2.0.6
--------
2020-10-09: service release
    - update travis build matrix for linux 3.9-dev
    - update travis build matrix (paths) for windows 3.9 / 3.10

v2.0.5
--------
2020-08-08: service release
    - fix documentation
    - fix travis
    - deprecate pycodestyle
    - implement flake8

v2.0.4
---------
2020-08-01: fix pypi deploy

v2.0.3
--------
2020-07-31: fix travis build

v2.0.2
--------
2020-07-29: feature release
    - use the new pizzacutter template
    - use cli_exit_tools

v2.0.1
--------
2020-07-16: feature release
    - fix cli test
    - enable traceback option on cli errors
    - corrected error in DeleteKey, missing_ok

v2.0.0
--------
2020-07-14 : feature release
    - fix setup.py for deploy on pypi
    - fix travis for pypi deploy testing

v2.0.0a0
--------
2020-07-13 : intermediate release
    - start to implement additional pathlib-like interface
    - implement fake-winreg to be able to develop and test under linux

v1.0.4
--------
2020-07-08 : patch release
    - new click CLI
    - use PizzaCutter Template
    - added jupyter notebook
    - reorganized modules and import
    - updated documentation

v1.0.3
--------
2019-09-02: strict mypy type checking, housekeeping

v1.0.2
--------
2019-04-10: initial PyPi release

v1.0.1
--------
2019-03-29: prevent import error when importing under linux

v1.0.0
--------
2019-03-28: Initial public release

