"""Codex (OpenAI) agent adapter.

Config: ~/.codex/config.toml + ~/.codex/auth.json
Fields: OPENAI_API_KEY in auth.json, model_providers in config.toml

Codex uses OpenAI's Responses API, which most third-party providers don't support.
A proxy is required to translate Responses API → Chat Completions API.

Currently depends on CC Switch (https://github.com/nicepkg/cc-switch) running
on 127.0.0.1:15721. Future versions may include a built-in proxy.
"""

from __future__ import annotations

import json
import logging

from apm.agents.base import AgentAdapter, is_port_open
from apm.config import CC_SWITCH_PORT, CC_SWITCH_URL, CODEX_AUTH, CODEX_CONFIG

logger = logging.getLogger(__name__)

CC_SWITCH_INSTALL_URL = "https://github.com/nicepkg/cc-switch"


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

        # For non-OpenAI providers, check CC Switch proxy
        if not is_openai:
            cc_running = is_port_open(CC_SWITCH_PORT)
            if cc_running:
                base_for_codex = CC_SWITCH_URL
                logger.info("CC Switch detected, routing Codex through proxy")
            else:
                base_for_codex = provider["base_url"]
                # Print warning to user
                print()
                print("  ⚠  Codex requires a proxy for non-OpenAI providers")
                print("     Codex uses Responses API, which most providers don't support.")
                print()
                print("     Option 1: Install CC Switch (recommended)")
                print(f"       → {CC_SWITCH_INSTALL_URL}")
                print("       → Enable Codex routing in CC Switch settings")
                print(f"       → Proxy runs on {CC_SWITCH_URL}")
                print()
                print("     Option 2: Use OpenAI directly")
                print("       → apm provider add openai --key sk-xxx")
                print()
                print("     Config written anyway — will work once proxy is running.")
                print()
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
