"""Aider agent adapter.

Config: ~/.aider.conf.yml + ~/.aider.env
Fields: openai-api-key, openai-api-base in conf.yml; env vars in .env

Aider reads configuration from both YAML config and .env files.
"""

from __future__ import annotations

from apm.agents.base import AgentAdapter
from apm.config import AIDER_CONFIG, AIDER_ENV, atomic_write


class AiderAdapter(AgentAdapter):
    name = "aider"

    def is_installed(self) -> bool:
        return AIDER_CONFIG.exists() or AIDER_ENV.exists()

    def read_provider(self) -> dict | None:
        key = None
        url = None
        model = None

        if AIDER_ENV.exists():
            for line in AIDER_ENV.read_text().splitlines():
                if "=" not in line or line.startswith("#"):
                    continue
                k, v = line.split("=", 1)
                k, v = k.strip(), v.strip()
                if k == "OPENAI_API_KEY":
                    key = v
                elif k == "OPENAI_API_BASE":
                    url = v

        if AIDER_CONFIG.exists():
            text = AIDER_CONFIG.read_text()
            # ponytail: aider uses flat YAML (no sections), parse top-level keys
            for line in text.splitlines():
                stripped = line.strip()
                if stripped.startswith("openai-api-key:"):
                    key = stripped.split(":", 1)[1].strip().strip('"').strip("'")
                elif stripped.startswith("openai-api-base:"):
                    url = stripped.split(":", 1)[1].strip().strip('"').strip("'")
                elif stripped.startswith("model:"):
                    model = stripped.split(":", 1)[1].strip().strip('"').strip("'")

        if not key and not url:
            return None
        return {
            "base_url": url,
            "api_key": key,
            "model": model,
            "protocol": "openai-compatible",
        }

    def write_provider(self, provider: dict) -> None:
        base_url = provider["base_url"].rstrip("/")
        api_key = provider["api_key"]
        models = provider.get("models", [])
        model = models[0] if models else None

        # Update .env file (primary config for sensitive keys)
        if AIDER_ENV.exists():
            self.backup(AIDER_ENV)
        env_lines = AIDER_ENV.read_text().splitlines() if AIDER_ENV.exists() else []
        env_map: dict[str, str] = {}
        for line in env_lines:
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env_map[k.strip()] = v.strip()
        env_map["OPENAI_API_KEY"] = api_key
        env_map["OPENAI_API_BASE"] = base_url
        env_content = "".join(f"{k}={v}\n" for k, v in env_map.items())
        atomic_write(AIDER_ENV, env_content)

        # Update conf.yml if it exists
        if AIDER_CONFIG.exists():
            self.backup(AIDER_CONFIG)
            text = AIDER_CONFIG.read_text()
            lines_out = []
            found_base = found_key = found_model = False
            for line in text.splitlines():
                stripped = line.strip()
                if stripped.startswith("openai-api-base:"):
                    lines_out.append(f"openai-api-base: {base_url}")
                    found_base = True
                elif stripped.startswith("openai-api-key:"):
                    lines_out.append(f"openai-api-key: {api_key}")
                    found_key = True
                elif stripped.startswith("model:") and model:
                    lines_out.append(f"model: {model}")
                    found_model = True
                else:
                    lines_out.append(line)
            if not found_base:
                lines_out.append(f"openai-api-base: {base_url}")
            if not found_key:
                lines_out.append(f"openai-api-key: {api_key}")
            if model and not found_model:
                lines_out.append(f"model: {model}")
            atomic_write(AIDER_CONFIG, "\n".join(lines_out) + "\n")
