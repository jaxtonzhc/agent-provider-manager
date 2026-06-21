"""Provider registry management."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone

from apm.config import APM_DIR, PROVIDERS_FILE

logger = logging.getLogger(__name__)


def _ensure_dir() -> None:
    """Ensure the apm data directory exists."""
    APM_DIR.mkdir(parents=True, exist_ok=True)


def _load() -> dict:
    """Load providers.json."""
    if not PROVIDERS_FILE.exists():
        return {"providers": {}, "active_provider": None}
    with open(PROVIDERS_FILE) as f:
        return json.load(f)


def _save(data: dict) -> None:
    """Save providers.json."""
    _ensure_dir()
    with open(PROVIDERS_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.chmod(PROVIDERS_FILE, 0o600)


def add(
    name: str,
    base_url: str,
    api_key: str,
    protocol: str = "openai-compatible",
    models: list[str] | None = None,
) -> str:
    """Add a new provider. Returns the provider slug."""
    data = _load()
    slug = name.lower().replace(" ", "-").replace("_", "-")
    data["providers"][slug] = {
        "name": name,
        "base_url": base_url.rstrip("/"),
        "api_key": api_key,
        "protocol": protocol,
        "models": models or [],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if data["active_provider"] is None:
        data["active_provider"] = slug
    _save(data)
    return slug


def remove(name: str) -> None:
    """Remove a provider by name or slug."""
    data = _load()
    slug = _resolve_slug(data, name)
    if slug is None:
        raise ValueError(f"Provider '{name}' not found")
    del data["providers"][slug]
    if data["active_provider"] == slug:
        data["active_provider"] = next(iter(data["providers"]), None)
    _save(data)


def get(name: str) -> dict | None:
    """Get a provider by name or slug."""
    data = _load()
    slug = _resolve_slug(data, name)
    if slug is None:
        return None
    p = data["providers"][slug]
    p["slug"] = slug
    return p


def list_all() -> list[dict]:
    """List all providers."""
    data = _load()
    result = []
    for slug, p in data["providers"].items():
        p["slug"] = slug
        p["is_active"] = slug == data["active_provider"]
        result.append(p)
    return result


def set_active(name: str) -> None:
    """Set the active provider."""
    data = _load()
    slug = _resolve_slug(data, name)
    if slug is None:
        raise ValueError(f"Provider '{name}' not found")
    data["active_provider"] = slug
    _save(data)


def get_active() -> dict | None:
    """Get the active provider."""
    data = _load()
    if not data["active_provider"]:
        return None
    p = data["providers"].get(data["active_provider"])
    if p:
        p["slug"] = data["active_provider"]
    return p


def _resolve_slug(data: dict, name: str) -> str | None:
    """Resolve a name to a slug (match slug or display name)."""
    name_lower = name.lower()
    for slug, p in data["providers"].items():
        if slug == name_lower or p["name"].lower() == name_lower:
            return slug
    return None


def print_list() -> None:
    """Print formatted provider list."""
    providers = list_all()
    if not providers:
        print("\n  No providers configured. Use 'apm provider add' to add one.\n")
        return
    print("\n  Providers")
    print("  " + "=" * 55)
    for p in providers:
        active = " *" if p["is_active"] else "  "
        masked = p["api_key"][:8] + "..." if len(p["api_key"]) > 8 else "***"
        print(f"  {active} {p['slug']:<20} {p['base_url']}")
        print(f"      key={masked}  protocol={p['protocol']}")
        if p["models"]:
            print(f"      models={', '.join(p['models'])}")
    active = next((p["slug"] for p in providers if p["is_active"]), "none")
    print(f"\n  Active: {active}\n")


def print_detail(name: str) -> None:
    """Print detailed provider info."""
    p = get(name)
    if not p:
        print(f"  Provider '{name}' not found.")
        return
    print(f"\n  Provider: {p['name']} ({p['slug']})")
    print(f"  Base URL: {p['base_url']}")
    print(f"  API Key:  {p['api_key'][:8]}...{p['api_key'][-4:]}")
    print(f"  Protocol: {p['protocol']}")
    models = ", ".join(p["models"]) if p["models"] else "(none)"
    print(f"  Models:   {models}")
    print(f"  Created:  {p['created_at']}")
    print()


def import_from_agents(agents: list[str] | None = None) -> list[dict]:
    """Import provider configs from installed agents.

    Reads each agent's current provider config and adds it to the registry.
    Returns list of imported providers.
    """
    from apm.agents.registry import ADAPTERS
    from apm.detect import get_installed_agents

    if agents is None:
        agents = get_installed_agents()

    imported: list[dict] = []
    for agent_name in agents:
        adapter = ADAPTERS.get(agent_name)
        if not adapter or not adapter.is_installed():
            continue
        try:
            current = adapter.read_provider()
            if not current:
                continue
            # Generate a slug from the base URL
            url = current.get("base_url", "")
            if not url:
                continue
            # Try to match a known provider
            slug = _guess_provider_slug(url)
            if not slug:
                slug = agent_name

            # Check if already exists
            existing = get(slug)
            if existing:
                logger.debug("Provider %s already exists, skipping", slug)
                imported.append({"agent": agent_name, "provider": slug, "status": "exists"})
                continue

            # Add
            add(
                name=slug.replace("-", " ").title(),
                base_url=url,
                api_key=current.get("api_key", ""),
                protocol=current.get("protocol", "openai-compatible"),
                models=[current["model"]] if current.get("model") else [],
            )
            imported.append({"agent": agent_name, "provider": slug, "status": "imported"})
            logger.debug("Imported provider %s from %s", slug, agent_name)
        except Exception as e:
            logger.debug("Failed to import from %s: %s", agent_name, e)
            imported.append({"agent": agent_name, "provider": None, "status": "error"})

    return imported


def _guess_provider_slug(url: str) -> str | None:
    """Guess provider slug from base URL."""
    url_lower = url.lower()
    mappings = {
        "openai.com": "openai",
        "anthropic.com": "anthropic",
        "deepseek.com": "deepseek",
        "googleapis.com": "google-gemini",
        "bigmodel.cn": "zhipu-glm",
        "x.ai": "xai",
        "moonshot.cn": "moonshot",
        "siliconflow.cn": "siliconflow",
        "openrouter.ai": "openrouter",
        "together.xyz": "together",
        "fireworks.ai": "fireworks",
        "volces.com": "volcengine",
        "baidu.com": "baidu-qianfan",
        "aliyun.com": "alibaba-qwen",
        "dashscope": "alibaba-qwen",
        "minimax.chat": "minimax",
        "mistral.ai": "mistral",
        "perplexity.ai": "perplexity",
        "xiaomimimo.com": "xiamimimo",
        "groq.com": "groq",
        "cerebras.ai": "cerebras",
        "sambanova.ai": "sambanova",
    }
    for pattern, slug in mappings.items():
        if pattern in url_lower:
            return slug
    return None
