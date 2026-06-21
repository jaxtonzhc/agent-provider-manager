"""Pi / Oh-My-Pi agent adapter.

Pi: ~/.pi/agent/models.json + auth.json
OMP: ~/.omp/agent/models.json + auth.json

Both use the same format (omp is a Pi fork).
"""

from __future__ import annotations

import json

from apm.agents.base import AgentAdapter
from apm.config import OMP_AUTH, OMP_CONFIG, PI_AUTH, PI_CONFIG, atomic_write


def _read(config_path, auth_path) -> dict | None:
    if not config_path.exists():
        return None
    try:
        data = json.loads(config_path.read_text())
    except (json.JSONDecodeError, OSError):
        return None
    providers = data.get("providers", {})
    if not providers:
        return None
    name, prov = next(iter(providers.items()))
    api_key = prov.get("apiKey", "")
    if not api_key and auth_path.exists():
        try:
            auth = json.loads(auth_path.read_text())
            api_key = auth.get(name, {}).get("apiKey", "")
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "base_url": prov.get("baseUrl", ""),
        "api_key": api_key,
        "model": None,
        "protocol": prov.get("api", "openai-completions"),
    }


def _write(adapter, config_path, provider) -> None:
    if config_path.exists():
        adapter.backup(config_path)
        try:
            data = json.loads(config_path.read_text())
        except (json.JSONDecodeError, OSError):
            data = {}
    else:
        data = {}

    slug = provider["name"].lower().replace(" ", "-")
    base_url = provider["base_url"].rstrip("/")

    model_meta = provider.get("_model_meta", {})
    models = []
    for m in provider.get("models", []):
        meta = model_meta.get(m, {})
        inputs = ["text"]
        if meta.get("vision"):
            inputs.append("image")
        models.append({
            "id": m,
            "name": meta.get("name", m),
            "reasoning": meta.get("reasoning", False),
            "input": inputs,
            "contextWindow": meta.get("context", 128000),
            "maxTokens": 16384,
        })

    providers_dict = data.setdefault("providers", {})
    providers_dict[slug] = {
        "baseUrl": base_url,
        "api": "openai-completions",
        "apiKey": provider["api_key"],
        "models": models,
    }

    atomic_write(config_path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


class PiAdapter(AgentAdapter):
    name = "pi"

    def is_installed(self) -> bool:
        return PI_CONFIG.parent.exists()

    def read_provider(self) -> dict | None:
        return _read(PI_CONFIG, PI_AUTH)

    def write_provider(self, provider: dict) -> None:
        _write(self, PI_CONFIG, provider)


class OmpAdapter(AgentAdapter):
    name = "omp"

    def is_installed(self) -> bool:
        return OMP_CONFIG.parent.exists()

    def read_provider(self) -> dict | None:
        return _read(OMP_CONFIG, OMP_AUTH)

    def write_provider(self, provider: dict) -> None:
        _write(self, OMP_CONFIG, provider)
