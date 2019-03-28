lib_registry
============

|Build Status| |Pypi Status| |Codecov Status| |Better Code| |snyk security|

some convenience functions to access the windows registry - to be extended.

supports python 2.7 - python 3.7 and possibly other dialects.

`100% code coverage <https://codecov.io/gh/bitranox/lib_registry>`_, tested under `Windows <https://travis-ci.org/bitranox/lib_registry>`_

-----


`Report Issues <https://github.com/bitranox/lib_registry/blob/master/ISSUE_TEMPLATE.md>`_

`Contribute <https://github.com/bitranox/lib_registry/blob/master/CONTRIBUTING.md>`_

`Pull Request <https://github.com/bitranox/lib_registry/blob/master/PULL_REQUEST_TEMPLATE.md>`_

`Code of Conduct <https://github.com/bitranox/lib_registry/blob/master/CODE_OF_CONDUCT.md>`_


-----


Installation and Upgrade
------------------------

From source code:

::

    python setup.py install
    python setup.py test

via pip (preferred):

::

    pip install --upgrade https://github.com/bitranox/lib_registry/archive/master.zip

via requirements.txt:

::

    Insert following line in Your requirements.txt:
    https://github.com/bitranox/lib_registry/archive/master.zip

    to install and upgrade all modules mentioned in requirements.txt:
    pip install --upgrade -r /<path>/requirements.txt

via python:

::

    python -m pip install --upgrade https://github.com/bitranox/lib_registry/archive/master.zip


Basic Usage
-----------

::

    >>> from lib_registry import *
    >>> import winreg

    >>> # get the SID´s of all Windows users
    >>> get_ls_user_sids()
    ['.DEFAULT', 'S-1-5-18', 'S-1-5-19', 'S-1-5-20', ...]

    >>> # get the Username from SID
    >>> get_username_from_sid(sid='S-1-5-20')
    'NetworkService'

    >>> # Read a Subkey from the Registry
    >>> key =  'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList\\S-1-5-20'
    >>> get_value(key_name=key, subkey_name='ProfileImagePath')
    '%systemroot%\\\\ServiceProfiles\\\\NetworkService'

    >>> key_exist('HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList\\S-1-5-20'
    True
    >>> key_exist('HKEY_LOCAL_MACHINE\\Software\\Wine')
    False




Requirements
------------

PYTEST, see : https://github.com/pytest-dev/pytest

Acknowledgement
---------------

special thanks to Robert C. Martin, especially for his books on "clean code" and "clean architecture"

Contribute
----------

I would love for you to fork and send me pull request for this project.
Please contribute.

License
-------

This software is licensed under the `MIT license <http://en.wikipedia.org/wiki/MIT_License>`_

See `License file <https://github.com/bitranox/wrapt-timeout-decorator/blob/master/LICENSE.txt>`_

.. |Build Status| image:: https://travis-ci.org/bitranox/lib_registry.svg?branch=master
   :target: https://travis-ci.org/bitranox/lib_registry
.. |Pypi Status| image:: https://badge.fury.io/py/lib_registry.svg
   :target: https://badge.fury.io/py/lib_registry
.. |Codecov Status| image:: https://codecov.io/gh/bitranox/lib_registry/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/bitranox/lib_registry
.. |Better Code| image:: https://bettercodehub.com/edge/badge/bitranox/lib_registry?branch=master
   :target: https://bettercodehub.com/results/bitranox/lib_registry
.. |snyk security| image:: https://snyk.io/test/github/bitranox/lib_registry/badge.svg
   :target: https://snyk.io/test/github/bitranox/lib_registry
