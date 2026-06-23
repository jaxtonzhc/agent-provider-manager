"""Centralized path configuration."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

HOME = Path.home()

# apm data directory
APM_DIR = HOME / ".apm"
PROVIDERS_FILE = APM_DIR / "providers.json"
SYNC_STATE_FILE = APM_DIR / "sync-state.json"
LOG_FILE = APM_DIR / "apm.log"

# Agent config paths (supported agents only)
CLAUDE_CODE_CONFIG = HOME / ".claude" / "settings.json"
OPENCODE_CONFIG = HOME / ".config" / "opencode" / "opencode.json"
ZCODE_CONFIG = HOME / ".zcode" / "v2" / "config.json"
HERMES_CONFIG = HOME / ".hermes" / "config.yaml"
PI_CONFIG = HOME / ".pi" / "agent" / "models.json"
PI_AUTH = HOME / ".pi" / "agent" / "auth.json"
PI_SETTINGS = HOME / ".pi" / "agent" / "settings.json"
OMP_CONFIG = HOME / ".omp" / "agent" / "models.json"
OMP_AUTH = HOME / ".omp" / "agent" / "auth.json"
OMP_SETTINGS = HOME / ".omp" / "agent" / "settings.json"

# Agent config path registry — single source of truth
AGENT_CONFIG_PATHS: dict[str, list[Path]] = {
    "claude-code": [CLAUDE_CODE_CONFIG],
    "opencode": [OPENCODE_CONFIG],
    "zcode": [ZCODE_CONFIG],
    "hermes": [HERMES_CONFIG],
    "pi": [PI_CONFIG, PI_AUTH],
    "omp": [OMP_CONFIG, OMP_AUTH],
}


def atomic_write(path: Path, content: str, mode: int = 0o644) -> None:
    """Write content to a file atomically via temp-file + rename."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    closed = False
    try:
        os.write(fd, content.encode("utf-8"))
        os.close(fd)
        closed = True
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    except BaseException:
        if not closed:
            os.close(fd)
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
