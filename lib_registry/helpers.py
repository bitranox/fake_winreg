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
