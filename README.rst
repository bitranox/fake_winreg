lib_registry
============

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

a more pythonic way to access the windows registry as winreg

command line interface is prepared - if someone needs to use it via commandline, give me a note.

----

automated tests, Travis Matrix, Documentation, Badges, etc. are managed with `PizzaCutter <https://github
.com/bitranox/PizzaCutter>`_ (cookiecutter on steroids)

Python version required: 3.6.0 or newer

tested on linux "bionic" with python 3.6, 3.7, 3.8, 3.8-dev, pypy3

`100% code coverage <https://codecov.io/gh/bitranox/lib_registry>`_, codestyle checking ,mypy static type checking ,tested under `Linux, macOS, Windows <https://travis-ci.org/bitranox/lib_registry>`_, automatic daily builds and monitoring

----

- `Try it Online`_
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

Try it Online
-------------

You might try it right away in Jupyter Notebook by using the "launch binder" badge, or click `here <https://mybinder.org/v2/gh/{{rst_include.
repository_slug}}/master?filepath=lib_registry.ipynb>`_

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
    python -m pip install --upgrade lib_registry

    # test latest release from PyPi without installing (can be skipped)
    python -m pip install lib_registry --install-option test

- to install the latest development version from github via pip:


.. code-block:: bash

    # normal install
    python -m pip install --upgrade git+https://github.com/bitranox/lib_registry.git

    # to test without installing (can be skipped)
    python -m pip install git+https://github.com/bitranox/lib_registry.git --install-option test

    # to install and upgrade all dependencies regardless of version number
    python -m pip install --upgrade git+https://github.com/bitranox/lib_registry.git --upgrade-strategy eager


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

    # to test without installing (can be skipped)
    python setup.py test

    # normal install
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

   Usage: lib_registry [OPTIONS] COMMAND [ARGS]...

     a more pythonic way to access the windows registry as winreg

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

2.0.0
----------
2020-07-14 : feature release
    - fix setup.py for deploy on pypi
    - fix travis for pypi deploy testing

2.0.0-alpha
-----------
2020-07-13 : intermediate release
    - start to implement additional pathlib-like interface
    - implement fake-winreg to be able to develop and test under linux

1.0.4
-----
2020-07-08 : patch release
    - new click CLI
    - use PizzaCutter Template
    - added jupyter notebook
    - reorganized modules and import
    - updated documentation

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

