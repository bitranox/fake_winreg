"""Network adapter for DNS-based computer reachability checks.

Used by ConnectRegistry to validate remote computer names.
"""

from __future__ import annotations

import socket

from fake_winreg.domain.helpers import get_first_part_of_the_key, strip_backslashes


def is_computer_reachable(computer_name: str) -> bool:
    """Check whether a computer name can be resolved via DNS.

    >>> assert is_computer_reachable(r'localhost\\test\\test2')
    """
    computer_name = strip_backslashes(computer_name)
    computer_name = get_first_part_of_the_key(computer_name)
    return hostname_found_in_dns(computer_name)


def hostname_found_in_dns(hostname: str) -> bool:
    """Return True if the hostname resolves via DNS lookup."""
    try:
        socket.gethostbyname(hostname)
        return True
    except Exception:
        return False


__all__ = [
    "hostname_found_in_dns",
    "is_computer_reachable",
]
