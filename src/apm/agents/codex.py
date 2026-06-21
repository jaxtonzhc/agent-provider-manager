"""Codex (OpenAI) agent adapter.

Config: ~/.codex/config.toml + ~/.codex/auth.json
Fields: OPENAI_API_KEY in auth.json, model_providers in config.toml
Note: Non-OpenAI providers require CC Switch proxy for Response API translation.
"""

from __future__ import annotations

import json

from apm.agents.base import AgentAdapter, is_port_open
from apm.config import CC_SWITCH_PORT, CC_SWITCH_URL, CODEX_AUTH, CODEX_CONFIG


class CodexAdapter(AgentAdapter):
    name = "codex"

    def is_installed(self) -> bool:
        return CODEX_CONFIG.exists() or CODEX_AUTH.exists()

    def read_provider(self) -> dict | None:
        if not CODEX_AUTH.exists():
            return None
        with open(CODEX_AUTH) as f:
            auth = json.load(f)
        key = auth.get("OPENAI_API_KEY")
        if not key:
            return None

        protocol = "openai-compatible"
        if CODEX_CONFIG.exists():
            text = CODEX_CONFIG.read_text()
            if 'wire_api = "responses"' in text:
                protocol = "responses"

        return {
            "base_url": "https://api.openai.com/v1",
            "api_key": key,
            "model": None,
            "protocol": protocol,
        }

    def write_provider(self, provider: dict) -> None:
        # Write auth.json
        self.backup(CODEX_AUTH)
        with open(CODEX_AUTH, "w") as f:
            json.dump({"OPENAI_API_KEY": provider["api_key"]}, f, indent=2)

        # Update config.toml
        self.backup(CODEX_CONFIG)
        text = CODEX_CONFIG.read_text() if CODEX_CONFIG.exists() else ""

        is_openai = "openai.com" in provider.get("base_url", "")
        wire_api = "responses" if is_openai else "chat_completions"

        # For non-OpenAI providers, route through CC Switch proxy if available
        if not is_openai and is_port_open(CC_SWITCH_PORT):
            base_for_codex = CC_SWITCH_URL
        elif not is_openai:
            base_for_codex = provider["base_url"]
        else:
            base_for_codex = ""

        lines = ['model_provider = "custom"\n', "\n"]
        lines.append("[model_providers.custom]\n")
        lines.append('name = "OpenAI"\n')
        lines.append("requires_openai_auth = true\n")
        lines.append("supports_websockets = true\n")
        lines.append(f'wire_api = "{wire_api}"\n')

        if base_for_codex:
            lines.append(f'base_url = "{base_for_codex}"\n')

        CODEX_CONFIG.write_text("".join(lines))
