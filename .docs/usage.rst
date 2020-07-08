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
