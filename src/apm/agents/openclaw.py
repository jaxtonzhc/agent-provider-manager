"""OpenClaw agent adapter.

Config: ~/.openclaw/openclaw.json
Fields: models.providers.*.apiKey, models.providers.*.baseUrl
"""

from __future__ import annotations

import json

from apm.agents.base import AgentAdapter
from apm.config import OPENCLAW_CONFIG


class OpenClawAdapter(AgentAdapter):
    name = "openclaw"

    def is_installed(self) -> bool:
        return OPENCLAW_CONFIG.exists()

    def read_provider(self) -> dict | None:
        if not OPENCLAW_CONFIG.exists():
            return None
        with open(OPENCLAW_CONFIG) as f:
            data = json.load(f)
        providers = data.get("models", {}).get("providers", {})
        if not providers:
            return None
        name, prov = next(iter(providers.items()))
        return {
            "base_url": prov.get("baseUrl", ""),
            "api_key": prov.get("apiKey", ""),
            "model": None,
            "protocol": prov.get("api", "openai-completions"),
        }

    def write_provider(self, provider: dict) -> None:
        self.backup(OPENCLAW_CONFIG)
        with open(OPENCLAW_CONFIG) as f:
            data = json.load(f)

        base_url = provider["base_url"].rstrip("/")
        slug = provider["name"].lower().replace(" ", "-")

        models_section = data.setdefault("models", {})
        models_section["mode"] = "merge"
        providers = models_section.setdefault("providers", {})

        model_entries = []
        for m in provider.get("models", []):
            model_entries.append({
                "id": m,
                "name": m,
                "reasoning": True,
                "input": ["text"],
                "contextWindow": 1048576,
                "maxTokens": 32000,
            })

        providers[slug] = {
            "baseUrl": base_url,
            "api": "openai-completions",
            "apiKey": provider["api_key"],
            "models": model_entries,
        }

        with open(OPENCLAW_CONFIG, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
