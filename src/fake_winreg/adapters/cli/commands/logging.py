"""Logging demonstration CLI command.

Provides a command to preview log output using lib_log_rich's logdemo facility.

Contents:
    * :func:`cli_logdemo` - Run a logging demonstration.
"""

from __future__ import annotations

import rich_click as click
from lib_log_rich.domain import ConsoleTheme

from fake_winreg.adapters.logging.setup import InvalidLoggingConfigError, run_logdemo

from .. import safe_console
from ..config_load import report_load_failure
from ..constants import click_context_settings
from ..context import get_cli_context
from ..exit_codes import ExitCode
from ..typed_click import option


def _to_console_theme(_ctx: click.Context, _param: click.Parameter, value: str) -> ConsoleTheme:
    """The ``--theme`` callback: the choice click accepted, as lib_log_rich's theme enum.

    The ``click.Choice`` lists the enum's ``str`` values, never its members (click matches an
    Enum member on its ``.name``), and returns the matching value in its own spelling.
    """
    return ConsoleTheme(value)


@click.command("logdemo", context_settings=click_context_settings())
@option(
    "--theme",
    # The library's own theme list, so an unknown name is a usage error (exit 2) rather than the
    # ValueError logdemo() raises, which main() would turn into an OS-specific errno.
    type=click.Choice([member.value for member in ConsoleTheme], case_sensitive=False),
    default=ConsoleTheme.CLASSIC.value,
    callback=_to_console_theme,
    help="Logging theme to preview",
)
@click.pass_context
def cli_logdemo(ctx: click.Context, theme: ConsoleTheme) -> None:
    """Run a logging demonstration to preview log output.

    A ``LOG_*`` variable lib_log_rich refuses ends the command with exit 78 and lib_log_rich's
    own line, as it ends ``config``.
    """
    try:
        result = run_logdemo(theme)
    except InvalidLoggingConfigError as exc:
        report_load_failure(exc, show_traceback=get_cli_context(ctx).traceback)
        ctx.exit(ExitCode.CONFIG_ERROR)
    safe_console.echo(f"\nLog demo completed (theme: {result.theme})")


__all__ = ["cli_logdemo"]
