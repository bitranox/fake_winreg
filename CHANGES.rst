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

x.x.x
----------
2020-xx-xx: development version
    -


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
