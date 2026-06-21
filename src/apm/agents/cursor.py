"""Cursor agent adapter.

Config: ~/.cursor/settings.json
Fields: Uses OpenAI-compatible env vars similar to Claude Code.

Cursor reads provider config from its settings.json, supporting
custom API endpoints via environment variables.
"""

from __future__ import annotations

import json

from apm.agents.base import AgentAdapter
from apm.config import CURSOR_SETTINGS, atomic_write


class CursorAdapter(AgentAdapter):
    name = "cursor"

    def is_installed(self) -> bool:
        return CURSOR_SETTINGS.parent.exists()

    def read_provider(self) -> dict | None:
        if not CURSOR_SETTINGS.exists():
            return None
        with open(CURSOR_SETTINGS) as f:
            data = json.load(f)

        # Cursor stores overrides in openai.* keys
        url = data.get("openai.baseUrl", "")
        key = data.get("openai.apiKey", "")
        model = data.get("openai.model", "")
        if not key and not url:
            return None
        return {
            "base_url": url,
            "api_key": key,
            "model": model,
            "protocol": "openai-compatible",
        }

    def write_provider(self, provider: dict) -> None:
        if CURSOR_SETTINGS.exists():
            self.backup(CURSOR_SETTINGS)
            with open(CURSOR_SETTINGS) as f:
                data = json.load(f)
        else:
            data = {}

        base_url = provider["base_url"].rstrip("/")
        data["openai.baseUrl"] = base_url
        data["openai.apiKey"] = provider["api_key"]

        models = provider.get("models", [])
        if models:
            data["openai.model"] = models[0]

        atomic_write(CURSOR_SETTINGS, json.dumps(data, indent=2, ensure_ascii=False) + "\n")
