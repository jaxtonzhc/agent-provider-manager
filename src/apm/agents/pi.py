"""Pi / Oh-My-Pi agent adapter.

Pi: ~/.pi/agent/models.json + auth.json
OMP: ~/.omp/agent/models.json + auth.json

Both use the same format (omp is a Pi fork).
Multi-provider: providers.{slug} dict. Active provider determined by PI's internal state.
"""

from __future__ import annotations

import json
from pathlib import Path

from apm.agents.base import AgentAdapter
from apm.config import (
    OMP_AUTH,
    OMP_CONFIG,
    OMP_SETTINGS,
    PI_AUTH,
    PI_CONFIG,
    PI_SETTINGS,
    atomic_write,
)


def _load(config_path: Path) -> dict:
    if not config_path.exists():
        return {}
    try:
        return json.loads(config_path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _read(config_path: Path, auth_path: Path) -> dict | None:
    data = _load(config_path)
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


def _write(adapter: AgentAdapter, config_path: Path, provider: dict) -> None:
    if config_path.exists():
        adapter.backup(config_path)
    data = _load(config_path)

    slug = provider["name"].lower().replace(" ", "-")
    base_url = provider["base_url"].rstrip("/")

    model_meta = provider.get("_model_meta") or provider.get("model_meta", {})
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


def _has_provider(config_path: Path, provider: dict) -> bool:
    data = _load(config_path)
    providers = data.get("providers", {})
    target_url = provider.get("base_url", "").rstrip("/")
    target_key = provider.get("api_key", "")
    for prov in providers.values():
        if prov.get("baseUrl", "").rstrip("/") == target_url and prov.get("apiKey") == target_key:
            return True
    return False


def _activate(
    adapter: AgentAdapter, settings_path: Path, config_path: Path,
    provider: dict, model: str | None,
) -> None:
    """PI activation: set defaultProvider and defaultModel in settings.json."""
    slug = provider["name"].lower().replace(" ", "-")

    # Verify provider exists in models.json
    data = _load(config_path)
    providers = data.get("providers", {})
    if slug not in providers:
        return

    # Pick model: explicit > first in provider's model list
    if not model:
        prov_models = providers[slug].get("models", [])
        if prov_models:
            model = prov_models[0]["id"] if isinstance(prov_models[0], dict) else prov_models[0]

    # Update settings.json
    settings = _load(settings_path)
    settings["defaultProvider"] = slug
    if model:
        settings["defaultModel"] = model
    atomic_write(settings_path, json.dumps(settings, indent=2, ensure_ascii=False) + "\n")


class PiAdapter(AgentAdapter):
    name = "pi"

    def is_installed(self) -> bool:
        return PI_CONFIG.parent.exists()

    def read_provider(self) -> dict | None:
        return _read(PI_CONFIG, PI_AUTH)

    def write_provider(self, provider: dict) -> None:
        _write(self, PI_CONFIG, provider)

    def activate_provider(self, provider: dict, model: str | None = None) -> None:
        _activate(self, PI_SETTINGS, PI_CONFIG, provider, model)

    def has_provider(self, provider: dict) -> bool:
        return _has_provider(PI_CONFIG, provider)


class OmpAdapter(AgentAdapter):
    name = "omp"

    def is_installed(self) -> bool:
        return OMP_CONFIG.parent.exists()

    def read_provider(self) -> dict | None:
        return _read(OMP_CONFIG, OMP_AUTH)

    def write_provider(self, provider: dict) -> None:
        _write(self, OMP_CONFIG, provider)

    def activate_provider(self, provider: dict, model: str | None = None) -> None:
        _activate(self, OMP_SETTINGS, OMP_CONFIG, provider, model)

    def has_provider(self, provider: dict) -> bool:
        return _has_provider(OMP_CONFIG, provider)
