"""Logging configuration for apm."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from apm.config import APM_DIR

LOG_FILE = APM_DIR / "apm.log"


def setup_logging(debug: bool = False) -> None:
    """Configure logging for apm.

    Args:
        debug: Enable debug level logging
    """
    # Check env var
    if os.environ.get("APM_DEBUG", "").lower() in ("1", "true", "yes"):
        debug = True

    level = logging.DEBUG if debug else logging.WARNING

    # Root logger
    root = logging.getLogger("apm")
    root.setLevel(level)

    # Console handler (only warnings+ unless debug)
    console = logging.StreamHandler(sys.stderr)
    console.setLevel(logging.DEBUG if debug else logging.WARNING)
    console_fmt = logging.Formatter("  [%(levelname)s] %(message)s")
    console.setFormatter(console_fmt)
    root.addHandler(console)

    # File handler (always debug level for troubleshooting)
    try:
        APM_DIR.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_fmt = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
        file_handler.setFormatter(file_fmt)
        root.addHandler(file_handler)
    except Exception:
        pass  # Silently ignore if can't write log file


def get_log_file() -> Path:
    """Return the log file path."""
    return LOG_FILE


def tail_logs(n: int = 20) -> list[str]:
    """Return the last n lines of the log file efficiently."""
    if not LOG_FILE.exists():
        return []
    # ponytail: read from end of file to avoid loading entire file
    try:
        with open(LOG_FILE, "rb") as f:
            f.seek(0, 2)
            size = f.tell()
            # Read last ~4KB per line as a rough heuristic
            chunk = min(size, n * 4096)
            f.seek(max(0, size - chunk))
            data = f.read().decode("utf-8", errors="replace")
        lines = data.splitlines()
        return lines[-n:]
    except OSError:
        return []
