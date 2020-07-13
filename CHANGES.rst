Changelog
=========

- new MAJOR version for incompatible API changes,
- new MINOR version for added functionality in a backwards compatible manner
- new PATCH version for backwards compatible bug fixes

planned:
    - test matrix parameter errors
    - auditing events

0.3.2
-----
2020-07-13 : patch release
    - raise [WinError 1707] The network address is invalid if computername is given
    - make HKEYType int convertible
    - make type aliases for better readability

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
