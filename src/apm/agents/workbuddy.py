"""WorkBuddy agent adapter.

Config: ~/.workbuddy/models.json
Fields: models[].apiKey, models[].url
"""

from __future__ import annotations

import json

from apm.agents.base import AgentAdapter
from apm.config import WORKBUDDY_CONFIG


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
        self.backup(WORKBUDDY_CONFIG)
        base_url = provider["base_url"].rstrip("/")

        models_list = []
        for m in provider.get("models", []):
            models_list.append({
                "id": m,
                "name": m,
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

        with open(WORKBUDDY_CONFIG, "w") as f:
            json.dump(models_list, f, indent=2, ensure_ascii=False)
