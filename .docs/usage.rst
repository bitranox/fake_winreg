.. code-block:: python

        import fake_winreg as winreg

        # setup a fake registry for windows
        fake_registry = winreg.fake_reg_tools.get_minimal_windows_testregistry()

        # load the fake registry into fake winreg
        winreg.load_fake_registry(fake_registry)

        # try the fake registry
        reg_handle = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)

        # Open Key
        reg_key = winreg.OpenKey(reg_handle, r'SOFTWARE\Microsoft\Windows NT\CurrentVersion')
        winreg.QueryValueEx(reg_key, 'CurrentBuild')
