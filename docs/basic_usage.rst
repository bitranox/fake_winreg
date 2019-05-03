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

    >>> # get the SIDs of all Windows users
    >>> get_ls_user_sids()
    ['.DEFAULT', 'S-1-5-18', 'S-1-5-19', 'S-1-5-20', ...]

    >>> # get the Username from SID
    >>> get_username_from_sid(sid='S-1-5-20')
    'NetworkService'
