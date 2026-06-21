"""WorkBuddy agent adapter.

Config: ~/.workbuddy/models.json
Fields: models[].apiKey, models[].url
"""

from __future__ import annotations

import json

from apm.agents.base import AgentAdapter
from apm.config import WORKBUDDY_CONFIG, atomic_write


class WorkBuddyAdapter(AgentAdapter):
    name = "workbuddy"

    def is_installed(self) -> bool:
        return WORKBUDDY_CONFIG.exists()

    def read_provider(self) -> dict | None:
        if not WORKBUDDY_CONFIG.exists():
            return None
        with open(WORKBUDDY_CONFIG) as f:
            models = json.load(f)
        if not models:
            return None
        m = models[0]
        return {
            "base_url": m.get("url", ""),
            "api_key": m.get("apiKey", ""),
            "model": m.get("id"),
            "protocol": "openai-compatible",
        }

    def write_provider(self, provider: dict) -> None:
        if WORKBUDDY_CONFIG.exists():
            self.backup(WORKBUDDY_CONFIG)
        base_url = provider["base_url"].rstrip("/")

        model_meta = provider.get("_model_meta", {})
        models_list = []
        for m in provider.get("models", []):
            meta = model_meta.get(m, {})
            has_reasoning = meta.get("reasoning", True)
            has_vision = meta.get("vision", False)
            models_list.append({
                "id": m,
                "name": meta.get("name", m),
                "vendor": "Custom",
                "url": base_url,
                "apiKey": provider["api_key"],
                "supportsToolCall": True,
                "supportsImages": has_vision,
                "supportsReasoning": has_reasoning,
                "useCustomProtocol": False,
                "reasoning": {
                    "supportedEfforts": ["medium", "high", "max", "xhigh"],
                } if has_reasoning else {},
            })

        if not models_list:
            models_list.append({
                "id": "unknown",
                "name": "Custom Model",
                "vendor": "Custom",
                "url": base_url,
                "apiKey": provider["api_key"],
                "supportsToolCall": True,
                "supportsImages": False,
                "supportsReasoning": True,
                "useCustomProtocol": False,
                "reasoning": {
                    "supportedEfforts": ["medium", "high", "max", "xhigh"],
                },
            })

        atomic_write(WORKBUDDY_CONFIG, json.dumps(models_list, indent=2, ensure_ascii=False) + "\n")
