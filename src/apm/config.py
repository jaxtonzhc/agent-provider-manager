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

# Agent config paths
CLAUDE_CODE_CONFIG = HOME / ".claude" / "settings.json"
CODEX_CONFIG = HOME / ".codex" / "config.toml"
CODEX_AUTH = HOME / ".codex" / "auth.json"
HERMES_CONFIG = HOME / ".hermes" / "config.yaml"
HERMES_ENV = HOME / ".hermes" / ".env"
OPENCLAW_CONFIG = HOME / ".openclaw" / "openclaw.json"
ZCODE_CONFIG = HOME / ".zcode" / "v2" / "config.json"
WORKBUDDY_CONFIG = HOME / ".workbuddy" / "models.json"
CURSOR_SETTINGS = HOME / ".cursor" / "settings.json"
AIDER_CONFIG = HOME / ".aider.conf.yml"
AIDER_ENV = HOME / ".aider.env"

# CC Switch proxy
CC_SWITCH_PORT = 15721
CC_SWITCH_URL = f"http://127.0.0.1:{CC_SWITCH_PORT}"

# Agent config path registry — single source of truth
AGENT_CONFIG_PATHS: dict[str, list[Path]] = {
    "claude-code": [CLAUDE_CODE_CONFIG],
    "codex": [CODEX_CONFIG, CODEX_AUTH],
    "hermes": [HERMES_CONFIG, HERMES_ENV],
    "openclaw": [OPENCLAW_CONFIG],
    "zcode": [ZCODE_CONFIG],
    "workbuddy": [WORKBUDDY_CONFIG],
    "cursor": [CURSOR_SETTINGS],
    "aider": [AIDER_CONFIG, AIDER_ENV],
}


def atomic_write(path: Path, content: str, mode: int = 0o644) -> None:
    """Write content to a file atomically via temp-file + rename."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        os.write(fd, content.encode("utf-8"))
        os.close(fd)
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    except BaseException:
        os.close(fd) if not os.get_inheritable(fd) else None  # noqa: E501
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
