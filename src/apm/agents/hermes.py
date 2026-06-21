"""Hermes agent adapter.

Config: ~/.hermes/config.yaml + ~/.hermes/.env
Fields: model.api_key, model.base_url in config.yaml; env vars in .env
"""

from __future__ import annotations

from apm.agents.base import AgentAdapter, yaml_get, yaml_set
from apm.config import HERMES_CONFIG, HERMES_ENV


class HermesAdapter(AgentAdapter):
    name = "hermes"

    def is_installed(self) -> bool:
        return HERMES_CONFIG.exists()

    def read_provider(self) -> dict | None:
        if not HERMES_CONFIG.exists():
            return None
        text = HERMES_CONFIG.read_text()
        key = yaml_get(text, "model", "api_key")
        url = yaml_get(text, "model", "base_url")
        model = yaml_get(text, "model", "default")
        if not key and not url:
            return None
        return {
            "base_url": url,
            "api_key": key,
            "model": model,
            "protocol": "openai-compatible",
        }

    def write_provider(self, provider: dict) -> None:
        self.backup(HERMES_CONFIG)
        text = HERMES_CONFIG.read_text()

        base_url = provider["base_url"].rstrip("/")
        api_key = provider["api_key"]
        models = provider.get("models", [])
        model = models[0] if models else "mimo-v2.5-pro"

        text = yaml_set(text, "model", "base_url", base_url)
        text = yaml_set(text, "model", "api_key", api_key)
        text = yaml_set(text, "model", "default", model)
        text = yaml_set(
            text, "model", "provider", provider["name"].lower().replace(" ", "")
        )

        HERMES_CONFIG.write_text(text)

        # Update .env
        self.backup(HERMES_ENV)
        env_lines = HERMES_ENV.read_text().splitlines() if HERMES_ENV.exists() else []
        env_map: dict[str, str] = {}
        for line in env_lines:
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env_map[k.strip()] = v.strip()

        env_key = (
            provider["name"].upper().replace(" ", "_").replace("-", "_") + "_API_KEY"
        )
        env_map[env_key] = api_key
        env_map["XIAOMI_BASE_URL"] = base_url

        with open(HERMES_ENV, "w") as f:
            for k, v in env_map.items():
                f.write(f"{k}={v}\n")
