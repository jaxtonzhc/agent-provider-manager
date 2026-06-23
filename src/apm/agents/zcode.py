"""ZCode agent adapter.

Config: ~/.zcode/v2/config.json
Format: provider.{uuid} entries with enabled: true/false for activation.
"""

from __future__ import annotations

import hashlib
import json

from apm.agents.base import AgentAdapter
from apm.config import ZCODE_CONFIG, atomic_write


def _slug_to_pid(slug: str) -> str:
    h = hashlib.md5(slug.encode()).hexdigest()
    return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"


class ZCodeAdapter(AgentAdapter):
    name = "zcode"

    def is_installed(self) -> bool:
        return ZCODE_CONFIG.exists()

    def _load(self) -> dict:
        if not ZCODE_CONFIG.exists():
            return {}
        try:
            return json.loads(ZCODE_CONFIG.read_text())
        except (json.JSONDecodeError, OSError):
            return {}

    def read_provider(self) -> dict | None:
        data = self._load()
        providers = data.get("provider", {})
        # Return the first enabled non-builtin provider
        for pid, prov in providers.items():
            if pid.startswith("builtin:"):
                continue
            if not prov.get("enabled", False):
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
        # Fallback: any non-builtin with credentials
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
        if ZCODE_CONFIG.exists():
            self.backup(ZCODE_CONFIG)
        data = self._load()

        base_url = provider["base_url"].rstrip("/")
        slug = provider["name"].lower().replace(" ", "-")
        pid = _slug_to_pid(slug)

        providers = data.setdefault("provider", {})

        model_meta = provider.get("_model_meta") or provider.get("model_meta", {})
        models_dict = {}
        for m in provider.get("models", []):
            meta = model_meta.get(m, {})
            models_dict[m] = {
                "limit": {"context": meta.get("context", 1000000), "output": 131072},
                "reasoning": {"enabled": meta.get("reasoning", True)},
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

        atomic_write(ZCODE_CONFIG, json.dumps(data, indent=2, ensure_ascii=False) + "\n")

    def activate_provider(self, provider: dict, model: str | None = None) -> None:
        """Enable target provider, disable all other non-builtin providers."""
        data = self._load()
        providers = data.get("provider", {})
        slug = provider["name"].lower().replace(" ", "-")
        target_pid = _slug_to_pid(slug)

        for pid, prov in providers.items():
            if pid.startswith("builtin:"):
                continue
            prov["enabled"] = (pid == target_pid)

        atomic_write(ZCODE_CONFIG, json.dumps(data, indent=2, ensure_ascii=False) + "\n")

    def has_provider(self, provider: dict) -> bool:
        data = self._load()
        providers = data.get("provider", {})
        target_url = provider.get("base_url", "").rstrip("/")
        target_key = provider.get("api_key", "")
        for pid, prov in providers.items():
            if pid.startswith("builtin:"):
                continue
            opts = prov.get("options", {})
            url_match = opts.get("baseURL", "").rstrip("/") == target_url
            if url_match and opts.get("apiKey") == target_key:
                return True
        return False
