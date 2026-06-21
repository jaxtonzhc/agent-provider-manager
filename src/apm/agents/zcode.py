"""ZCode agent adapter.

Config: ~/.zcode/v2/config.json
Fields: provider.*.options.apiKey, provider.*.options.baseURL
"""

from __future__ import annotations

import hashlib
import json

from apm.agents.base import AgentAdapter
from apm.config import ZCODE_CONFIG


class ZCodeAdapter(AgentAdapter):
    name = "zcode"

    def is_installed(self) -> bool:
        return ZCODE_CONFIG.exists()

    def read_provider(self) -> dict | None:
        if not ZCODE_CONFIG.exists():
            return None
        with open(ZCODE_CONFIG) as f:
            data = json.load(f)
        providers = data.get("provider", {})
        for pid, prov in providers.items():
            if pid.startswith("builtin:"):
                continue
            opts = prov.get("options", {})
            key = opts.get("apiKey")
            url = opts.get("baseURL")
            if key and url:
                return {
                    "base_url": url,
                    "api_key": key,
                    "model": None,
                    "protocol": prov.get("kind", "openai-compatible"),
                }
        return None

    def write_provider(self, provider: dict) -> None:
        self.backup(ZCODE_CONFIG)
        with open(ZCODE_CONFIG) as f:
            data = json.load(f)

        base_url = provider["base_url"].rstrip("/")
        slug = provider["name"].lower().replace(" ", "-")
        pid = hashlib.md5(slug.encode()).hexdigest()
        pid = f"{pid[:8]}-{pid[8:12]}-{pid[12:16]}-{pid[16:20]}-{pid[20:32]}"

        providers = data.setdefault("provider", {})

        models_dict = {}
        for m in provider.get("models", []):
            models_dict[m] = {
                "limit": {"context": 1000000, "output": 131072},
                "reasoning": {"enabled": True},
                "modalities": {"input": ["text"], "output": ["text"]},
            }

        kind = (
            "openai-compatible"
            if "openai-compatible" in provider.get("protocol", "")
            else provider.get("protocol", "openai-compatible")
        )

        providers[pid] = {
            "name": provider["name"],
            "kind": kind,
            "options": {
                "apiKey": provider["api_key"],
                "baseURL": base_url,
                "apiKeyRequired": True,
            },
            "enabled": True,
            "models": models_dict,
        }

        with open(ZCODE_CONFIG, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
