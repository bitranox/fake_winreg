lib_registry
============

|Pypi Status| |license| |maintenance|

|Build Status| |Codecov Status| |Better Code| |code climate| |snyk security|

some convenience functions to access the windows registry - to be extended.

supports python 2.7 - python 3.7 and possibly other dialects.

`100% code coverage <https://codecov.io/gh/bitranox/lib_registry>`_, tested under `Windows and Wine <https://travis-ci.org/bitranox/lib_registry>`_

-----


`Report Issues <https://github.com/bitranox/lib_registry/blob/master/ISSUE_TEMPLATE.md>`_

`Contribute <https://github.com/bitranox/lib_registry/blob/master/CONTRIBUTING.md>`_

`Pull Request <https://github.com/bitranox/lib_registry/blob/master/PULL_REQUEST_TEMPLATE.md>`_

`Code of Conduct <https://github.com/bitranox/lib_registry/blob/master/CODE_OF_CONDUCT.md>`_


-----


Installation and Upgrade
------------------------

From source code:

.. code-block:: bash

    # normal install
    python setup.py install
    # test without installing
    python setup.py test

via pip latest Release:

.. code-block:: bash

    # latest Release from pypi
    pip install lib_registry

via pip latest Development Version:

.. code-block:: bash

    # upgrade all dependencies regardless of version number (PREFERRED)
    pip install --upgrade https://github.com/bitranox/lib_registry/archive/master.zip --upgrade-strategy eager
    # normal install
    pip install --upgrade https://github.com/bitranox/lib_registry/archive/master.zip
    # test without installing
    pip install --upgrade https://github.com/bitranox/lib_registry/archive/master.zip  --install-option test

via requirements.txt:

.. code-block:: bash

    # Insert following line in Your requirements.txt:
    # for the latest Release:
    lib_registry
    # for the latest Development Version :
    https://github.com/bitranox/lib_registry/archive/master.zip

    # to install and upgrade all modules mentioned in requirements.txt:
    pip install --upgrade -r /<path>/requirements.txt

via python:

.. code-block:: bash

    python -m pip install --upgrade lib_registry


Basic Usage
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

    >>> # get the SID´s of all Windows users
    >>> get_ls_user_sids()
    ['.DEFAULT', 'S-1-5-18', 'S-1-5-19', 'S-1-5-20', ...]

    >>> # get the Username from SID
    >>> get_username_from_sid(sid='S-1-5-20')
    'NetworkService'


Requirements
------------

pytest, see : https://github.com/pytest-dev/pytest

typing, see : https://pypi.org/project/typing/

Acknowledgement
---------------

and special thanks to "uncle bob" Robert C. Martin, especially for his books on "clean code" and "clean architecture"

Contribute
----------

I would love for you to fork and send me pull request for this project.
Please contribute.

License
-------

This software is licensed under the `MIT license <http://en.wikipedia.org/wiki/MIT_License>`_

See `License file <https://github.com/bitranox/lib_registry/blob/master/LICENSE.txt>`_

.. |license| image:: https://img.shields.io/github/license/webcomics/pywine.svg
   :target: http://en.wikipedia.org/wiki/MIT_License
.. |maintenance| image:: https://img.shields.io/maintenance/yes/2019.svg
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
