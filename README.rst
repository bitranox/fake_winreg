lib_registry
============

|Pypi Status| |license| |maintenance|

|Build Status| |Codecov Status| |Better Code| |code climate| |code climate coverage| |snyk security|

.. |license| image:: https://img.shields.io/github/license/webcomics/pywine.svg
   :target: http://en.wikipedia.org/wiki/MIT_License
.. |maintenance| image:: https://img.shields.io/maintenance/yes/2021.svg
.. |Build Status| image:: https://travis-ci.org/bitranox/lib_registry.svg?branch=master
   :target: https://travis-ci.org/bitranox/lib_registry
.. for the pypi status link note the dashes, not the underscore !
.. |Pypi Status| image:: https://badge.fury.io/py/lib-registry.svg
   :target: https://badge.fury.io/py/lib_registry
.. |Codecov Status| image:: https://codecov.io/gh/bitranox/lib_registry/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/bitranox/lib_registry
.. |Better Code| image:: https://bettercodehub.com/edge/badge/bitranox/lib_registry?branch=master
   :target: https://bettercodehub.com/results/bitranox/lib_registry
.. |snyk security| image:: https://snyk.io/test/github/bitranox/lib_registry/badge.svg
   :target: https://snyk.io/test/github/bitranox/lib_registry
.. |code climate| image:: https://api.codeclimate.com/v1/badges/affaa3b099c55c69950c/maintainability
   :target: https://codeclimate.com/github/bitranox/lib_registry/maintainability
   :alt: Maintainability
.. |code climate coverage| image:: https://api.codeclimate.com/v1/badges/affaa3b099c55c69950c/test_coverage
   :target: https://codeclimate.com/github/bitranox/lib_registry/test_coverage
   :alt: Code Coverage

some convenience functions to access the windows registry - to be extended.

command line interface is prepared - if someone needs to use it via commandline, give me a note.

automated tests, Travis Matrix, Documentation, Badges for this Project are managed with `lib_travis_template <https://github
.com/bitranox/lib_travis_template>`_ - check it out

supports python 3.6-3.8, pypy3 and possibly other dialects.

`100% code coverage <https://codecov.io/gh/bitranox/lib_registry>`_, mypy static type checking, tested under `Linux, macOS, Windows and Wine <https://travis-ci
.org/bitranox/lib_registry>`_, automatic daily builds  and monitoring

----

- `Installation and Upgrade`_
- `Usage`_
- `Usage from Commandline`_
- `Requirements`_
- `Acknowledgements`_
- `Contribute`_
- `Report Issues <https://github.com/bitranox/lib_registry/blob/master/ISSUE_TEMPLATE.md>`_
- `Pull Request <https://github.com/bitranox/lib_registry/blob/master/PULL_REQUEST_TEMPLATE.md>`_
- `Code of Conduct <https://github.com/bitranox/lib_registry/blob/master/CODE_OF_CONDUCT.md>`_
- `License`_
- `Changelog`_

----



Installation and Upgrade
------------------------

Before You start, its highly recommended to update pip and setup tools:


.. code-block:: bash

    python3 -m pip --upgrade pip
    python3 -m pip --upgrade setuptools
    python3 -m pip --upgrade wheel


install latest version with pip (recommended):

.. code-block:: bash

    # upgrade all dependencies regardless of version number (PREFERRED)
    python3 -m pip install --upgrade git+https://github.com/bitranox/lib_registry.git --upgrade-strategy eager

    # test without installing (can be skipped)
    python3 -m pip install git+https://github.com/bitranox/lib_registry.git --install-option test

    # normal install
    python3 -m pip install --upgrade git+https://github.com/bitranox/lib_registry.git


install latest pypi Release (if there is any):

.. code-block:: bash

    # latest Release from pypi
    python3 -m pip install --upgrade lib_registry

    # test without installing (can be skipped)
    python3 -m pip install lib_registry --install-option test

    # normal install
    python3 -m pip install --upgrade lib_registry



include it into Your requirements.txt:

.. code-block:: bash

    # Insert following line in Your requirements.txt:
    # for the latest Release on pypi (if any):
    lib_registry
    # for the latest Development Version :
    lib_registry @ git+https://github.com/bitranox/lib_registry.git

    # to install and upgrade all modules mentioned in requirements.txt:
    python3 -m pip install --upgrade -r /<path>/requirements.txt


Install from source code:

.. code-block:: bash

    # cd ~
    $ git clone https://github.com/bitranox/lib_registry.git
    $ cd lib_registry

    # test without installing (can be skipped)
    python3 setup.py test

    # normal install
    python3 setup.py install


via makefile:

if You are on linux, makefiles are a very convenient way to install. Here we can do much more, like installing virtual environment, clean caches and so on.
This is still in development and not recommended / working at the moment:

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

Usage
-----------

.. code-block:: py

    >>> from lib_registry import *

    >>> # Read a Value from the Registry
    >>> key =  'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList\\S-1-5-20'
    >>> get_value(key_name=key, value_name='ProfileImagePath')
    '%systemroot%\\\\ServiceProfiles\\\\NetworkService'

    >>> # Create a Key
    >>> create_key(r'HKCU\\Software\\lib_registry_test')

    >>> # Delete a Key
    >>> delete_key(r'HKCU\\Software\\lib_registry_test')


    >>> # Write a Value to the Registry
    >>> create_key(r'HKCU\\Software\\lib_registry_test')
    >>> set_value(key_name=r'HKCU\\Software\\lib_registry_test', value_name='test_name', value='test_string', value_type=REG_SZ)
    >>> result = get_value(key_name=r'HKCU\\Software\\lib_registry_test', value_name='test_name')
    >>> assert result == 'test_string'

    >>> # Delete a Value from the Registry
    >>> delete_value(key_name=r'HKCU\\Software\\lib_registry_test', value_name='test_name')
    >>> delete_key(r'HKCU\\Software\\lib_registry_test')

    >>> # Check if a key exists
    >>> key_exist('HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList\\S-1-5-20'
    True
    >>> key_exist('HKEY_LOCAL_MACHINE\\Software\\DoesNotExist')
    False

    >>> # get the SIDs of all Windows users
    >>> get_ls_user_sids()
    ['.DEFAULT', 'S-1-5-18', 'S-1-5-19', 'S-1-5-20', ...]

    >>> # get the Username from SID
    >>> get_username_from_sid(sid='S-1-5-20')
    'NetworkService'

Usage from Commandline
------------------------

.. code-block:: bash

   Usage:
       lib_registry (-h | -v | -i)

   Options:
       -h, --help          show help
       -v, --version       show version
       -i, --info          show Info

   this module exposes no other useful functions to the commandline

Requirements
------------
following modules will be automatically installed :

.. code-block:: bash

    ## Project Requirements
    docopt

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

1.0.3
-----
2019-09-02: strict mypy type checking, housekeeping

1.0.2
-----
2019-04-10: initial PyPi release

1.0.1
-----
2019-03-29: prevent import error when importing under linux

1.0.0
-----
2019-03-28: Initial public release

