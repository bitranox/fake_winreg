"""Pure string helper functions for registry key path manipulation."""

from __future__ import annotations


def strip_backslashes(input_string: str) -> str:
    r"""Remove leading and trailing backslashes.

    >>> strip_backslashes(r'\\test\\\\')
    'test'
    """
    return input_string.strip("\\")


def get_first_part_of_the_key(key_name: str) -> str:
    r"""Extract the first segment before the first backslash.

    >>> get_first_part_of_the_key('')
    ''
    >>> get_first_part_of_the_key(r'something\\more')
    'something'
    >>> get_first_part_of_the_key(r'nothing')
    'nothing'
    """
    key_name = strip_backslashes(key_name)
    return key_name.split("\\", 1)[0]


__all__ = [
    "get_first_part_of_the_key",
    "strip_backslashes",
]
