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
