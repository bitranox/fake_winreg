"""Shared CLI constants.

Centralizes configuration values used across CLI modules to ensure consistency.

Contents:
    * :func:`click_context_settings` - A fresh Click settings dict for one command.
    * :data:`TRACEBACK_SUMMARY_LIMIT` - Character budget for truncated tracebacks.
    * :data:`TRACEBACK_VERBOSE_LIMIT` - Character budget for verbose tracebacks.
"""

from __future__ import annotations

from typing import Any, Final

#: The help flags every command answers, so help output stays consistent across commands.
_HELP_OPTION_NAMES: Final[tuple[str, ...]] = ("-h", "--help")

#: Character budget used when printing truncated tracebacks.
TRACEBACK_SUMMARY_LIMIT: Final[int] = 500

#: Character budget used when verbose tracebacks are enabled.
TRACEBACK_VERBOSE_LIMIT: Final[int] = 10_000


def click_context_settings() -> dict[str, Any]:
    """Return a new Click ``context_settings`` dict for one command.

    A function rather than one shared dict: click keeps the dict a command is given as that
    command's own, and rich_click's decorators ``update()`` it in place, so a single module-level
    dict would carry one command's settings into every other command.

    Returns:
        The settings dict; ``Any`` values because that is how click declares the mapping.

    Example:
        >>> click_context_settings()
        {'help_option_names': ('-h', '--help')}
        >>> click_context_settings() is click_context_settings()
        False
    """
    return {"help_option_names": _HELP_OPTION_NAMES}


__all__ = [
    "TRACEBACK_SUMMARY_LIMIT",
    "TRACEBACK_VERBOSE_LIMIT",
    "click_context_settings",
]
