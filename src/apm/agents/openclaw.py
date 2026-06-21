"""OpenClaw agent adapter.

Config: ~/.openclaw/openclaw.json
Fields: models.providers.*.apiKey, models.providers.*.baseUrl
"""

from __future__ import annotations

import json

from apm.agents.base import AgentAdapter
from apm.config import OPENCLAW_CONFIG, atomic_write


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
        if OPENCLAW_CONFIG.exists():
            self.backup(OPENCLAW_CONFIG)
            with open(OPENCLAW_CONFIG) as f:
                data = json.load(f)
        else:
            data = {}

        base_url = provider["base_url"].rstrip("/")
        slug = provider["name"].lower().replace(" ", "-")

        models_section = data.setdefault("models", {})
        models_section["mode"] = "merge"
        providers_dict = models_section.setdefault("providers", {})

        model_meta = provider.get("_model_meta", {})
        model_entries = []
        for m in provider.get("models", []):
            meta = model_meta.get(m, {})
            inputs = ["text"]
            if meta.get("vision"):
                inputs.append("image")
            model_entries.append({
                "id": m,
                "name": meta.get("name", m),
                "reasoning": meta.get("reasoning", False),
                "input": inputs,
                "contextWindow": meta.get("context", 131072),
                "maxTokens": 32000,
            })

        providers_dict[slug] = {
            "baseUrl": base_url,
            "api": "openai-completions",
            "apiKey": provider["api_key"],
            "models": model_entries,
        }

        atomic_write(OPENCLAW_CONFIG, json.dumps(data, indent=2, ensure_ascii=False) + "\n")
