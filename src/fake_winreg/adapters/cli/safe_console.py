"""Encode-safe console output.

Purpose
-------
Wraps :func:`click.echo` so a console whose codepage cannot represent a glyph
degrades that glyph instead of aborting the command.

Why
---
Console output is a sink with an encoding the program does not choose. Python
hands stdout to a Windows console at codepage 1252 with ``errors="strict"``, so
writing ``✓`` raises ``UnicodeEncodeError: 'charmap' codec can't encode
character '\\u2713'`` and the command exits non-zero -- after its real work has
already succeeded, which is the part that misleads. ``click.echo`` does not
protect against this; the exception propagates.

Degrading at the SINK keeps the glyphs where they are wanted: an email body or
a UTF-8 terminal still receives ``✓``, and only a stream that genuinely cannot
encode it sees ``[OK]``. Callers therefore write the glyph they mean and never
branch on the platform.

Contents
--------
* :data:`ASCII_FALLBACKS` - the glyph-to-ASCII map
* :func:`ascii_fallback` - transliterate text for a target encoding
* :func:`encode_safe` - degrade text only when the encoding rejects it
* :func:`echo` - the :func:`click.echo` replacement every module uses
* :func:`safe_stream` - the same protection for a writer this module does not
  own, such as the one a :class:`rich.console.Console` writes through
"""

from __future__ import annotations

import codecs
import sys
from typing import IO, TYPE_CHECKING, Any, Final, TextIO

import rich_click as click

if TYPE_CHECKING:
    from collections.abc import Callable

ASCII_FALLBACKS: Final[dict[str, str]] = {
    "✓": "[OK]",  # check mark
    "✔": "[OK]",  # heavy check mark
    "✅": "[OK]",  # white heavy check mark
    "✗": "[X]",  # ballot X
    "✘": "[X]",  # heavy ballot X
    "❌": "[X]",  # cross mark
    "⚠": "[!]",  # warning sign
    "️": "",  # variation selector 16, trails an emoji glyph and carries no text
    "•": "-",  # bullet
    "≥": ">=",
    "≤": "<=",
    "→": "->",
    "←": "<-",
    # The quotation marks are spelled as escapes on purpose: written literally
    # they are indistinguishable from ASCII ' and " in most editors, which is
    # exactly the confusion ruff's RUF001 exists to flag.
    "\u2018": "'",  # left single quotation mark
    "\u2019": "'",  # right single quotation mark
    "\u201c": '"',  # left double quotation mark
    "\u201d": '"',  # right double quotation mark
    "…": "...",
}

#: The prefix of the codec error handlers :func:`ascii_fallback` encodes with, one per stream
#: error handler (``<prefix>+strict``, ``<prefix>+surrogateescape``, ...). A codec calls it only
#: for the characters it cannot encode, so everything the stream can print stays as written.
_FALLBACK_ERROR_HANDLER: Final[str] = "fake_winreg.safe_console.ascii_fallback"

#: The stream error handlers a fallback handler has been registered for, by handler name.
_REGISTERED: dict[str, str] = {}


def _streams_own_replacement(error: UnicodeEncodeError, stream_errors: str) -> str | bytes:
    """What the stream's own error handler writes for the first rejected character, else ``?``.

    ``surrogateescape`` turns a lone surrogate back into the path byte it came from and
    ``backslashreplace`` spells the character out; a ``strict`` stream, or a handler that
    cannot take this character (surrogateescape and a CJK glyph), gets ``?``.
    """
    if stream_errors == "strict":
        return "?"
    single = UnicodeEncodeError(error.encoding, error.object, error.start, error.start + 1, error.reason)
    try:
        replacement, _ = codecs.lookup_error(stream_errors)(single)
    except (UnicodeError, LookupError):
        return "?"
    return replacement


def _replacing_unencodable(stream_errors: str) -> Callable[[UnicodeError], tuple[str | bytes, int]]:
    """Build the codec error handler for a stream that uses `stream_errors`.

    It handles one rejected character per call: its ASCII form from :data:`ASCII_FALLBACKS`
    when the table has one, otherwise whatever the stream's own handler would write.
    """

    def _replace(error: UnicodeError) -> tuple[str | bytes, int]:
        if not isinstance(error, UnicodeEncodeError):
            raise error
        ascii_form = ASCII_FALLBACKS.get(error.object[error.start])
        if ascii_form is not None:
            return ascii_form, error.start + 1
        return _streams_own_replacement(error, stream_errors), error.start + 1

    return _replace


def _fallback_handler(stream_errors: str) -> str:
    """Return the name of the fallback codec error handler for `stream_errors`, registering it once."""
    name = _REGISTERED.get(stream_errors)
    if name is None:
        name = f"{_FALLBACK_ERROR_HANDLER}+{stream_errors}"
        codecs.register_error(name, _replacing_unencodable(stream_errors))
        _REGISTERED[stream_errors] = name
    return name


def _stream_encoding(file: IO[Any] | None, *, err: bool = False) -> str | None:
    """Return the target stream's encoding, or None when it cannot be determined.

    An unknown encoding means the caller gets the original text: guessing would
    degrade output that may well have been fine.

    With no explicit `file` the answer comes from ``sys.stdout``/``sys.stderr``,
    which is what :func:`click.echo` resolves its own default target from. click
    exposes no supported way to ask for that stream: ``get_text_stream`` was
    deprecated in click 8.5.0 and is removed in 9.0, its documented replacement
    being to let ``echo`` resolve the stream itself.
    """
    encoding = getattr(_target_stream(file, err=err), "encoding", None)
    return encoding if isinstance(encoding, str) else None


def _target_stream(file: IO[Any] | None, *, err: bool) -> object:
    return file if file is not None else (sys.stderr if err else sys.stdout)


def _stream_errors(stream: object) -> str | None:
    """Return the stream's own encoding error handler (``strict``, ``surrogateescape``, ...), or None."""
    errors = getattr(stream, "errors", None)
    return errors if isinstance(errors, str) else None


def ascii_fallback(text: str, encoding: str, errors: str | None = None) -> str:
    """Rewrite `text` so it survives `encoding`.

    Only the characters `encoding` cannot represent are replaced: a known glyph
    by its ASCII equivalent from :data:`ASCII_FALLBACKS`, anything else by what
    the stream's own error handler writes for it (`errors`), or ``?`` for a
    ``strict`` stream. Every other character is kept, so a glyph the stream can
    print is never rewritten because another one in the same text could not be.

    Parameters
    ----------
    text:
        The message as the caller wrote it.
    encoding:
        The target stream's encoding, e.g. ``"cp1252"``.
    errors:
        The target stream's error handler, e.g. ``"surrogateescape"``; None means
        ``strict``.

    Returns
    -------
    str
        A string the stream writes without raising: a lone surrogate is kept for a
        ``surrogateescape`` stream, which writes the original path byte for it.
    """
    stream_errors = errors or "strict"
    try:
        encoded = text.encode(encoding, errors=_fallback_handler(stream_errors))
        return encoded.decode(encoding, errors=stream_errors)
    except UnicodeError:
        # The stream's own handler produced something this codec cannot carry (raw bytes
        # into utf-16/32); degrade those characters as for a strict stream.
        return text.encode(encoding, errors=_fallback_handler("strict")).decode(encoding)


def encode_safe(text: str, encoding: str | None, errors: str | None = None) -> str:
    """Return `text` if `encoding` accepts it, else its fallback for a stream using `errors`.

    The check runs BEFORE the write on purpose. Writing first and catching
    ``UnicodeEncodeError`` would leave the already-encoded prefix on the stream,
    so the retry would duplicate it. No encoding is exempt from the check: a
    lone surrogate encodes in none of them, utf-8 included. The check itself is
    strict, so a known glyph still gets its ASCII form on a stream whose own
    handler would have escaped it; see :func:`ascii_fallback` for the rest.
    """
    if encoding is None:
        return text
    try:
        text.encode(encoding)
    except UnicodeEncodeError:
        return ascii_fallback(text, encoding, errors)
    return text


def echo(message: object = "", *, file: IO[Any] | None = None, err: bool = False, nl: bool = True) -> None:
    """Write `message` to the console, degrading anything it cannot encode.

    Drop-in for :func:`click.echo` for the arguments this project uses.

    Parameters
    ----------
    message:
        The text to write. Non-string values are stringified as click does.
    file:
        Target stream. Defaults to click's stdout (or stderr when `err`).
    err:
        Write to stderr instead of stdout.
    nl:
        Append a newline.

    Side Effects
    ------------
    Writes to the given stream.
    """
    text = message if isinstance(message, str) else str(message)
    errors = _stream_errors(_target_stream(file, err=err))
    click.echo(encode_safe(text, _stream_encoding(file, err=err), errors), file=file, err=err, nl=nl)


class _SafeWriter:
    """A text stream that degrades what the wrapped stream cannot encode.

    Why
        Rich renders through a writer this module does not control, and it
        raises the same ``UnicodeEncodeError`` on a legacy codepage rather than
        substituting. Wrapping the writer applies the fallback to every segment
        rich emits without rich needing to know.

        With no explicit stream the target is resolved at WRITE time, not at
        construction. A module-level ``Console(file=safe_stream())`` built at
        import would otherwise capture the interpreter's original stdout, and
        anything that later swaps ``sys.stdout`` - click's ``CliRunner``,
        ``contextlib.redirect_stdout``, pytest's capture - would be bypassed
        and its buffer would come back empty.
    """

    def __init__(self, stream: TextIO | None) -> None:
        self._stream = stream

    def _target(self) -> TextIO:
        return self._stream if self._stream is not None else sys.stdout

    def write(self, text: str) -> int:
        """Write `text`, degrading anything the current target cannot encode."""
        target = self._target()
        encoding = getattr(target, "encoding", None)
        return target.write(encode_safe(text, encoding if isinstance(encoding, str) else None, _stream_errors(target)))

    def flush(self) -> None:
        """Flush the current target."""
        self._target().flush()

    def isatty(self) -> bool:
        """Report the target's tty-ness, so rich keeps its styling."""
        return self._target().isatty()

    @property
    def encoding(self) -> str | None:
        """Expose the target's encoding; rich inspects it."""
        encoding = getattr(self._target(), "encoding", None)
        return encoding if isinstance(encoding, str) else None


def safe_stream(stream: TextIO | None = None) -> Any:  # rich accepts any writer with this shape
    """Wrap a stream so unencodable text degrades instead of raising.

    Use for a writer handed to a third-party renderer. For this project's own
    output use :func:`echo` instead.

    Parameters
    ----------
    stream:
        The destination text stream. Omit it (or pass None) to follow
        ``sys.stdout`` as it is at each write, which is what a module-level
        renderer needs so test harnesses can still capture the output.

    Returns
    -------
    Any
        A writer with ``write``/``flush``/``isatty``/``encoding``.
    """
    return _SafeWriter(stream)


__all__ = [
    "ASCII_FALLBACKS",
    "ascii_fallback",
    "echo",
    "encode_safe",
    "safe_stream",
]
