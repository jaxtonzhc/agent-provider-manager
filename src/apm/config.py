"""Centralized path configuration."""

from __future__ import annotations

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

# CC Switch proxy
CC_SWITCH_PORT = 15721
CC_SWITCH_URL = f"http://127.0.0.1:{CC_SWITCH_PORT}"
