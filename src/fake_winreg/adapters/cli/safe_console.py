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

import sys
from typing import IO, Any, Final, TextIO

import rich_click as click

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

#: Encodings that represent every code point, so the check can be skipped.
_UNIVERSAL_ENCODINGS: Final[frozenset[str]] = frozenset({"utf-8", "utf8", "utf-16", "utf16", "utf-32", "utf32"})


def _stream_encoding(file: IO[Any] | None) -> str | None:
    """Return the target stream's encoding, or None when it cannot be determined.

    An unknown encoding means the caller gets the original text: guessing would
    degrade output that may well have been fine.
    """
    stream = file if file is not None else click.get_text_stream("stdout")
    encoding = getattr(stream, "encoding", None)
    return encoding if isinstance(encoding, str) else None


def ascii_fallback(text: str, encoding: str) -> str:
    """Rewrite `text` so it survives `encoding`.

    Known glyphs become their ASCII equivalent from :data:`ASCII_FALLBACKS`;
    anything else the codec still cannot represent becomes ``?``. Text the
    encoding already accepts is returned unchanged.

    Parameters
    ----------
    text:
        The message as the caller wrote it.
    encoding:
        The target stream's encoding, e.g. ``"cp1252"``.

    Returns
    -------
    str
        A string that :meth:`str.encode` accepts for `encoding`.
    """
    mapped = "".join(ASCII_FALLBACKS.get(character, character) for character in text)
    return mapped.encode(encoding, errors="replace").decode(encoding)


def encode_safe(text: str, encoding: str | None) -> str:
    """Return `text` if `encoding` accepts it, else its ASCII fallback.

    The check runs BEFORE the write on purpose. Writing first and catching
    ``UnicodeEncodeError`` would leave the already-encoded prefix on the stream,
    so the retry would duplicate it.
    """
    if encoding is None or encoding.lower() in _UNIVERSAL_ENCODINGS:
        return text
    try:
        text.encode(encoding)
    except UnicodeEncodeError:
        return ascii_fallback(text, encoding)
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
    target = file if file is not None else click.get_text_stream("stderr" if err else "stdout")
    click.echo(encode_safe(text, _stream_encoding(target)), file=target, nl=nl)


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
        return target.write(encode_safe(text, encoding if isinstance(encoding, str) else None))

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
