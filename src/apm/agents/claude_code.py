"""Claude Code agent adapter.

Config: ~/.claude/settings.json
Fields: env.ANTHROPIC_AUTH_TOKEN, env.ANTHROPIC_BASE_URL, env.ANTHROPIC_MODEL
"""

from __future__ import annotations

import json

from apm.agents.base import AgentAdapter
from apm.config import CLAUDE_CODE_CONFIG, atomic_write


class ClaudeCodeAdapter(AgentAdapter):
    name = "claude-code"

    def is_installed(self) -> bool:
        return CLAUDE_CODE_CONFIG.exists()

    def read_provider(self) -> dict | None:
        if not CLAUDE_CODE_CONFIG.exists():
            return None
        with open(CLAUDE_CODE_CONFIG) as f:
            data = json.load(f)
        env = data.get("env", {})
        key = env.get("ANTHROPIC_AUTH_TOKEN")
        url = env.get("ANTHROPIC_BASE_URL")
        model = env.get("ANTHROPIC_MODEL")
        if not key and not url:
            return None
        return {"base_url": url, "api_key": key, "model": model, "protocol": "anthropic"}

    def write_provider(self, provider: dict) -> None:
        if CLAUDE_CODE_CONFIG.exists():
            self.backup(CLAUDE_CODE_CONFIG)
            with open(CLAUDE_CODE_CONFIG) as f:
                data = json.load(f)
        else:
            data = {}

        env = data.setdefault("env", {})

        # Prefer explicit anthropic URL if available
        anthro_url = provider.get("anthropic_base_url", "")
        if anthro_url:
            base_url = anthro_url.rstrip("/")
        else:
            base_url = provider["base_url"].rstrip("/")
            if provider.get("protocol") == "openai-compatible":
                if not base_url.endswith("/anthropic"):
                    import re
                    base_url = re.sub(r"/v\d+$", "/anthropic", base_url)
                    if not base_url.endswith("/anthropic"):
                        base_url += "/anthropic"

        env["ANTHROPIC_AUTH_TOKEN"] = provider["api_key"]
        env["ANTHROPIC_BASE_URL"] = base_url

        models = provider.get("models", [])
        if models:
            env["ANTHROPIC_MODEL"] = models[0]
            env["ANTHROPIC_DEFAULT_SONNET_MODEL"] = models[0]
            env["ANTHROPIC_DEFAULT_OPUS_MODEL"] = models[0]
            env["ANTHROPIC_DEFAULT_HAIKU_MODEL"] = models[-1] if len(models) > 1 else models[0]

        atomic_write(CLAUDE_CODE_CONFIG, json.dumps(data, indent=2, ensure_ascii=False) + "\n")
