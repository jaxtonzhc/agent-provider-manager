"""Codex (OpenAI) agent adapter.

Config: ~/.codex/config.toml + ~/.codex/auth.json
Fields: OPENAI_API_KEY in auth.json, model_providers in config.toml

Codex uses OpenAI's Responses API, which most third-party providers don't support.
A proxy is required to translate Responses API → Chat Completions API.
"""

from __future__ import annotations

import json
import logging
import re

from apm.agents.base import AgentAdapter, is_port_open
from apm.config import CC_SWITCH_PORT, CC_SWITCH_URL, CODEX_AUTH, CODEX_CONFIG, atomic_write

logger = logging.getLogger(__name__)

CC_SWITCH_INSTALL_URL = "https://github.com/farion1231/cc-switch"


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
        base_url = "https://api.openai.com/v1"
        if CODEX_CONFIG.exists():
            text = CODEX_CONFIG.read_text()
            if 'wire_api = "responses"' in text:
                protocol = "responses"
            m = re.search(r'base_url\s*=\s*"([^"]+)"', text)
            if m:
                base_url = m.group(1)

        return {
            "base_url": base_url,
            "api_key": key,
            "model": None,
            "protocol": protocol,
        }

    def write_provider(self, provider: dict) -> None:
        if CODEX_AUTH.exists():
            self.backup(CODEX_AUTH)
        CODEX_AUTH.parent.mkdir(parents=True, exist_ok=True)
        auth_data = json.dumps({"OPENAI_API_KEY": provider["api_key"]}, indent=2)
        atomic_write(CODEX_AUTH, auth_data + "\n")

        if CODEX_CONFIG.exists():
            self.backup(CODEX_CONFIG)

        is_openai = "openai.com" in provider.get("base_url", "")
        wire_api = "responses" if is_openai else "chat_completions"

        if not is_openai:
            cc_running = is_port_open(CC_SWITCH_PORT)
            if cc_running:
                base_for_codex = CC_SWITCH_URL
                logger.info("CC Switch detected, routing Codex through proxy")
            else:
                base_for_codex = provider["base_url"]
                from apm.colors import bold, red, yellow
                print()
                title = bold("Codex needs CC Switch for non-OpenAI APIs")
                url_line = f"Install: {yellow(CC_SWITCH_INSTALL_URL)}"
                note = "Config written — will work once proxy is running."
                print(f"  {red('┌──────────────────────────────────────────────┐')}")
                print(f"  {red('│')} {title}")
                print(f"  {red('│')} {url_line}")
                print(f"  {red('│')} {note}")
                print(f"  {red('└──────────────────────────────────────────────┘')}")
                print()
        else:
            base_for_codex = ""

        # Preserve existing config, only update provider-related fields
        text = CODEX_CONFIG.read_text() if CODEX_CONFIG.exists() else ""
        if "[model_providers.custom]" in text:
            text = re.sub(r'wire_api\s*=\s*"[^"]*"', f'wire_api = "{wire_api}"', text)
            if base_for_codex:
                if "base_url" in text:
                    text = re.sub(r'base_url\s*=\s*"[^"]*"', f'base_url = "{base_for_codex}"', text)
                else:
                    text = text.rstrip() + f'\nbase_url = "{base_for_codex}"\n'
            elif "base_url" in text and is_openai:
                text = re.sub(r'base_url\s*=\s*"[^"]*"\n?', "", text)
        else:
            lines = ['model_provider = "custom"\n', "\n", "[model_providers.custom]\n",
                     'name = "OpenAI"\n', "requires_openai_auth = true\n",
                     "supports_websockets = true\n", f'wire_api = "{wire_api}"\n']
            if base_for_codex:
                lines.append(f'base_url = "{base_for_codex}"\n')
            text = "".join(lines)

        atomic_write(CODEX_CONFIG, text)
