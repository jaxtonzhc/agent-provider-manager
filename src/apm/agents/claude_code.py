"""Claude Code agent adapter.

Config: ~/.claude/settings.json
Fields: env.ANTHROPIC_AUTH_TOKEN, env.ANTHROPIC_BASE_URL, env.ANTHROPIC_MODEL

Claude Code is single-provider: write_provider and activate_provider are the same
(it always uses whatever env vars are set).
"""

from __future__ import annotations

import json

from apm.agents.base import AgentAdapter
from apm.config import CLAUDE_CODE_CONFIG, atomic_write


class ClaudeCodeAdapter(AgentAdapter):
    name = "claude-code"

    def is_installed(self) -> bool:
        return CLAUDE_CODE_CONFIG.exists()

    def _load(self) -> dict:
        if not CLAUDE_CODE_CONFIG.exists():
            return {}
        try:
            return json.loads(CLAUDE_CODE_CONFIG.read_text())
        except (json.JSONDecodeError, OSError):
            return {}

    def read_provider(self) -> dict | None:
        data = self._load()
        env = data.get("env", {})
        key = env.get("ANTHROPIC_AUTH_TOKEN")
        url = env.get("ANTHROPIC_BASE_URL")
        model = env.get("ANTHROPIC_MODEL")
        if not key and not url:
            return None
        return {"base_url": url, "api_key": key, "model": model, "protocol": "anthropic"}

    def _resolve_url(self, provider: dict) -> str:
        anthro_url = provider.get("anthropic_base_url", "")
        if anthro_url:
            return anthro_url.rstrip("/")
        base_url = provider["base_url"].rstrip("/")
        if provider.get("protocol") == "openai-compatible":
            if not base_url.endswith("/anthropic"):
                import re
                base_url = re.sub(r"/v\d+$", "/anthropic", base_url)
                if not base_url.endswith("/anthropic"):
                    base_url += "/anthropic"
        return base_url

    def write_provider(self, provider: dict) -> None:
        if CLAUDE_CODE_CONFIG.exists():
            self.backup(CLAUDE_CODE_CONFIG)
        data = self._load()

        env = data.setdefault("env", {})
        base_url = self._resolve_url(provider)

        env["ANTHROPIC_AUTH_TOKEN"] = provider["api_key"]
        env["ANTHROPIC_BASE_URL"] = base_url

        models = provider.get("models", [])
        if models:
            env["ANTHROPIC_MODEL"] = models[0]
            env["ANTHROPIC_DEFAULT_SONNET_MODEL"] = models[0]
            env["ANTHROPIC_DEFAULT_OPUS_MODEL"] = models[0]
            env["ANTHROPIC_DEFAULT_HAIKU_MODEL"] = models[-1] if len(models) > 1 else models[0]

        atomic_write(CLAUDE_CODE_CONFIG, json.dumps(data, indent=2, ensure_ascii=False) + "\n")

    def activate_provider(self, provider: dict, model: str | None = None) -> None:
        """For Claude Code, activate = write (single-provider agent)."""
        self.write_provider(provider)
        if model:
            data = self._load()
            env = data.setdefault("env", {})
            env["ANTHROPIC_MODEL"] = model
            env["ANTHROPIC_DEFAULT_SONNET_MODEL"] = model
            atomic_write(CLAUDE_CODE_CONFIG, json.dumps(data, indent=2, ensure_ascii=False) + "\n")

    def has_provider(self, provider: dict) -> bool:
        current = self.read_provider()
        if not current:
            return False
        target_url = self._resolve_url(provider)
        return (
            current.get("base_url", "").rstrip("/") == target_url
            and current.get("api_key") == provider.get("api_key")
        )
