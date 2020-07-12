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


here a more comprehensive description of the winreg methods (which are implemented by fake registry)

ConnectRegistry
---------------

.. include:: ../fake_winreg/fake_winreg.py
    :code: python
    :start-after: # ConnectRegistry{{{
    :end-before: # ConnectRegistry}}}

CloseKey
---------------

.. include:: ../fake_winreg/fake_winreg.py
    :code: python
    :start-after: # CloseKey{{{
    :end-before: # CloseKey}}}

CreateKey
---------------

.. include:: ../fake_winreg/fake_winreg.py
    :code: python
    :start-after: # CreateKey{{{
    :end-before: # CreateKey}}}


DeleteKey
---------------

.. include:: ../fake_winreg/fake_winreg.py
    :code: python
    :start-after: # DeleteKey{{{
    :end-before: # DeleteKey}}}


DeleteKeyEx
---------------

.. include:: ../fake_winreg/fake_winreg.py
    :code: python
    :start-after: # DeleteKeyEx{{{
    :end-before: # DeleteKeyEx}}}


DeleteValue
---------------

.. include:: ../fake_winreg/fake_winreg.py
    :code: python
    :start-after: # DeleteValue{{{
    :end-before: # DeleteValue}}}


EnumKey
---------------

.. include:: ../fake_winreg/fake_winreg.py
    :code: python
    :start-after: # EnumKey{{{
    :end-before: # EnumKey}}}


EnumValue
---------------

.. include:: ../fake_winreg/fake_winreg.py
    :code: python
    :start-after: # EnumValue{{{
    :end-before: # EnumValue}}}


OpenKey
---------------

.. include:: ../fake_winreg/fake_winreg.py
    :code: python
    :start-after: # OpenKey{{{
    :end-before: # OpenKey}}}


OpenKeyEx
---------------

.. include:: ../fake_winreg/fake_winreg.py
    :code: python
    :start-after: # OpenKeyEx{{{
    :end-before: # OpenKeyEx}}}


QueryInfoKey
---------------

.. include:: ../fake_winreg/fake_winreg.py
    :code: python
    :start-after: # QueryInfoKey{{{
    :end-before: # QueryInfoKey}}}


QueryValue
---------------

.. include:: ../fake_winreg/fake_winreg.py
    :code: python
    :start-after: # QueryValue{{{
    :end-before: # QueryValue}}}


QueryValueEx
---------------

.. include:: ../fake_winreg/fake_winreg.py
    :code: python
    :start-after: # QueryValueEx{{{
    :end-before: # QueryValueEx}}}


SetValue
---------------

.. include:: ../fake_winreg/fake_winreg.py
    :code: python
    :start-after: # SetValue{{{
    :end-before: # SetValue}}}


SetValueEx
---------------

.. include:: ../fake_winreg/fake_winreg.py
    :code: python
    :start-after: # SetValueEx{{{
    :end-before: # SetValueEx}}}
