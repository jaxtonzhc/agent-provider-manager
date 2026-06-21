"""Terminal color helpers — auto-detects tty support."""

from __future__ import annotations

import os
import sys


def _supports_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


_COLOR = _supports_color()

# ponytail: simple ANSI codes, no dependency needed
_CODES = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "dim": "\033[2m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "cyan": "\033[36m",
}


def _wrap(code: str, text: str) -> str:
    if not _COLOR:
        return text
    return f"{_CODES[code]}{text}{_CODES['reset']}"


def green(text: str) -> str:
    return _wrap("green", text)


def red(text: str) -> str:
    return _wrap("red", text)


def yellow(text: str) -> str:
    return _wrap("yellow", text)


def blue(text: str) -> str:
    return _wrap("blue", text)


def cyan(text: str) -> str:
    return _wrap("cyan", text)


def bold(text: str) -> str:
    return _wrap("bold", text)


def dim(text: str) -> str:
    return _wrap("dim", text)


def ok(text: str) -> str:
    return green(f"✓ {text}")


def err(text: str) -> str:
    return red(f"✗ {text}")


def warn(text: str) -> str:
    return yellow(f"⚠ {text}")


def skip(text: str) -> str:
    return dim(f"⊘ {text}")
