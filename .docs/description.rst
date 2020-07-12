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
