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

this is perfect for TDD, creating registry related code and covering most issues before You hit a real registry with Your tests.

If You want to see real life examples, check out `lib_registry <https://github.com/bitranox/lib_registry>`_

- get all winreg function names, type hints and constants, even on linux in Your favorite IDE
- you plug in this "fake _winreg" and can test all Your Registry related functions on linux, wine, windows
- all the predefined HKEY\_*, REG\_*, KEY\_* constants are there.
- You might even test against a set of different fake registries
- you can use (almost) all winreg functions against a "fake" registry
- it behaves very much like the real "winreg" (version 3.3),
  like not accepting keyword arguments for most functions,
  accepting sub_keys to be "None" or "blank" in some, but not all functions, etc.
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
- some (few) winreg functions are not implemented - if You need it, give me a note
- obviously we can not connect to the registry of another windows computer over the network
- KEY_WOW64_32KEY is not supported. We show always the same ...
- obviously auditing event's are not supported

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

        from lib_fake_registry import *

        # Setup the registry values - see file "set_fake_registry_testvalues" how it is done
        fake_registry_windows = set_fake_test_registry_windows()
        fake_registry_wine = set_fake_test_registry_wine()

        # initialize the fake winreg with a fake registry
        winreg = FakeWinReg(fake_registry_windows)

        # do Your testing against that fake registry
        hive_key = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
        winreg.CloseKey(winreg.HKEY_LOCAL_MACHINE)

        # initialize the fake winreg with another fake registry
        winreg = FakeWinReg(fake_registry_wine)

        # do Your testing against that other fake registry
        hive_key = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
        winreg.CloseKey(winreg.HKEY_LOCAL_MACHINE)

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

put the usage of the project under CHANGES.rst

0.1.0
-----
2020-06-17: initial public release
    - with all docs in place

