"""Cursor agent adapter.

Config: ~/.cursor/settings.json
Fields: openai.baseUrl / openai.apiKey / openai.model (OpenAI-compatible)

Cursor BYOK custom keys only work in Ask/Plan mode.
Agent mode (Composer, inline edit, autocomplete) is locked to Cursor's backend.
"""

from __future__ import annotations

import json
import logging

from apm.agents.base import AgentAdapter
from apm.config import CURSOR_SETTINGS, atomic_write

logger = logging.getLogger(__name__)


class CursorAdapter(AgentAdapter):
    name = "cursor"

    def is_installed(self) -> bool:
        return CURSOR_SETTINGS.parent.exists()

    def read_provider(self) -> dict | None:
        if not CURSOR_SETTINGS.exists():
            return None
        with open(CURSOR_SETTINGS) as f:
            data = json.load(f)

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

        atomic_write(
            CURSOR_SETTINGS,
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        )

        from apm.colors import dim, yellow
        print(
            f"  {yellow('Note:')} Cursor BYOK keys only work in "
            f"Ask/Plan mode.{dim(' Agent mode uses Cursor built-in.')}"
        )
