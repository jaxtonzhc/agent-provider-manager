"""OpenCode agent adapter.

Config: ~/.config/opencode/opencode.json
Format:
  {
    "$schema": "https://opencode.ai/config.json",
    "model": "provider_id/model_id",
    "small_model": "provider_id/model_id",
    "provider": {
      "slug": {
        "npm": "@ai-sdk/openai-compatible",
        "name": "Display Name",
        "options": { "baseURL": "...", "apiKey": "..." },
        "models": { "model-id": { "name": "..." } }
      }
    }
  }

Active model is determined by the top-level "model" field (format: provider_id/model_id).
"""

from __future__ import annotations

import json

from apm.agents.base import AgentAdapter
from apm.config import OPENCODE_CONFIG, atomic_write


class OpenCodeAdapter(AgentAdapter):
    name = "opencode"

    def is_installed(self) -> bool:
        return OPENCODE_CONFIG.parent.exists()

    def _load(self) -> dict:
        if not OPENCODE_CONFIG.exists():
            return {"$schema": "https://opencode.ai/config.json"}
        try:
            return json.loads(OPENCODE_CONFIG.read_text())
        except (json.JSONDecodeError, OSError):
            return {"$schema": "https://opencode.ai/config.json"}

    def read_provider(self) -> dict | None:
        data = self._load()
        model_ref = data.get("model", "")
        if "/" not in model_ref:
            return None
        prov_id = model_ref.split("/", 1)[0]
        providers = data.get("provider", {})
        prov = providers.get(prov_id)
        if not prov:
            return None
        opts = prov.get("options", {})
        return {
            "base_url": opts.get("baseURL", ""),
            "api_key": opts.get("apiKey", ""),
            "model": model_ref.split("/", 1)[1] if "/" in model_ref else None,
            "protocol": "openai-compatible",
        }

    def write_provider(self, provider: dict) -> None:
        if OPENCODE_CONFIG.exists():
            self.backup(OPENCODE_CONFIG)
        data = self._load()

        slug = provider["name"].lower().replace(" ", "-")
        base_url = provider["base_url"].rstrip("/")

        model_meta = provider.get("_model_meta") or provider.get("model_meta", {})
        models_dict = {}
        for m in provider.get("models", []):
            meta = model_meta.get(m, {})
            ctx = meta.get("context", 131072)
            models_dict[m] = {
                "name": meta.get("name", m),
                "limit": {"context": ctx, "output": min(ctx // 4, 65536)},
            }

        providers = data.setdefault("provider", {})
        providers[slug] = {
            "npm": "@ai-sdk/openai-compatible",
            "name": provider["name"],
            "options": {
                "baseURL": base_url,
                "apiKey": provider["api_key"],
            },
            "models": models_dict,
        }

        atomic_write(OPENCODE_CONFIG, json.dumps(data, indent=2, ensure_ascii=False) + "\n")

    def activate_provider(self, provider: dict, model: str | None = None) -> None:
        """Set active model to provider_slug/model_id."""
        data = self._load()
        slug = provider["name"].lower().replace(" ", "-")

        if not model:
            models = provider.get("models", [])
            model = models[0] if models else None
        if not model:
            return

        data["model"] = f"{slug}/{model}"
        atomic_write(OPENCODE_CONFIG, json.dumps(data, indent=2, ensure_ascii=False) + "\n")

    def has_provider(self, provider: dict) -> bool:
        data = self._load()
        providers = data.get("provider", {})
        target_url = provider.get("base_url", "").rstrip("/")
        target_key = provider.get("api_key", "")
        for prov in providers.values():
            opts = prov.get("options", {})
            url_match = opts.get("baseURL", "").rstrip("/") == target_url
            if url_match and opts.get("apiKey") == target_key:
                return True
        return False
