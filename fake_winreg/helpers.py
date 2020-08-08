import socket


def strip_backslashes(input_string: str) -> str:
    """
    >>> strip_backslashes(r'\\test\\\\')
    'test'
    """
    input_string = input_string.strip('\\')
    return input_string


def get_first_part_of_the_key(key_name: str) -> str:
    """
    >>> get_first_part_of_the_key('')
    ''
    >>> get_first_part_of_the_key(r'something\\more')
    'something'
    >>> get_first_part_of_the_key(r'nothing')
    'nothing'

    """
    key_name = strip_backslashes(key_name)
    key_name = key_name.split('\\', 1)[0]
    return key_name


def is_computer_reachable(computer_name: str) -> bool:
    """
    >>> assert is_computer_reachable('www.google.com')
    >>> assert is_computer_reachable(r'localhost\\test\\test2')
    >>> assert not is_computer_reachable('unknown_host')
    """
    computer_name = strip_backslashes(computer_name)
    computer_name = get_first_part_of_the_key(computer_name)
    return hostname_found_in_dns(computer_name)


def hostname_found_in_dns(hostname: str) -> bool:
    """
    >>> assert hostname_found_in_dns('www.google.com')
    >>> assert not hostname_found_in_dns('unknown_host')
    """
    try:
        socket.gethostbyname(hostname)
        return True
    except Exception:   # noqa
        return False
