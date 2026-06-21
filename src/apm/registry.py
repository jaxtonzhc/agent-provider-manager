"""Registry management — built-in + remote agent/provider catalog."""

from __future__ import annotations

import json
import logging
import os
import time
from importlib import resources
from pathlib import Path
from urllib.request import Request, urlopen

from apm.config import APM_DIR

logger = logging.getLogger(__name__)

REMOTE_REGISTRY_URL = (
    "https://raw.githubusercontent.com/jaxtonzhc/agent-provider-manager/main/"
    "src/apm/registry.json"
)
CACHE_FILE = APM_DIR / "registry-cache.json"
CACHE_TTL = 86400  # 24 hours


def _load_builtin() -> dict:
    """Load the built-in registry.json shipped with the package."""
    try:
        ref = resources.files("apm").joinpath("registry.json")
        return json.loads(ref.read_text(encoding="utf-8"))
    except Exception:
        # Fallback: read from source tree
        builtin = Path(__file__).parent / "registry.json"
        if builtin.exists():
            return json.loads(builtin.read_text(encoding="utf-8"))
        return {"version": 0, "agents": {}, "providers": {}}


def _load_cache() -> dict | None:
    """Load cached registry if it exists and is fresh."""
    if not CACHE_FILE.exists():
        return None
    try:
        data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        cached_at = data.get("_cached_at", 0)
        if time.time() - cached_at > CACHE_TTL:
            logger.debug("Registry cache expired")
            return None
        return data
    except Exception:
        return None


def _save_cache(data: dict) -> None:
    """Save registry to cache."""
    APM_DIR.mkdir(parents=True, exist_ok=True)
    data["_cached_at"] = time.time()
    CACHE_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    os.chmod(CACHE_FILE, 0o600)


def fetch_remote() -> dict | None:
    """Fetch registry from remote GitHub URL."""
    try:
        logger.debug("Fetching registry from %s", REMOTE_REGISTRY_URL)
        req = Request(REMOTE_REGISTRY_URL, headers={"User-Agent": "apm-cli"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            _save_cache(data)
            logger.debug("Registry fetched and cached")
            return data
    except Exception as e:
        logger.debug("Failed to fetch remote registry: %s", e)
        return None


def load_registry(force_remote: bool = False) -> dict:
    """Load registry with hybrid strategy:
    1. Check cache (if fresh and not force_remote)
    2. Try remote (if force_remote or cache miss)
    3. Fall back to built-in

    Returns registry dict with 'agents' and 'providers' keys.
    """
    if not force_remote:
        cached = _load_cache()
        if cached:
            logger.debug("Using cached registry")
            return cached

    remote = fetch_remote()
    if remote:
        return remote

    logger.debug("Using built-in registry")
    return _load_builtin()


def get_agent(name: str) -> dict | None:
    """Get agent info from registry."""
    registry = load_registry()
    return registry.get("agents", {}).get(name)


def get_provider(name: str) -> dict | None:
    """Get provider info from registry."""
    registry = load_registry()
    return registry.get("providers", {}).get(name)


def list_agents() -> dict[str, dict]:
    """List all known agents."""
    registry = load_registry()
    return registry.get("agents", {})


def list_providers() -> dict[str, dict]:
    """List all known providers."""
    registry = load_registry()
    return registry.get("providers", {})


def resolve_provider(name: str, api_key: str) -> dict | None:
    """Resolve a provider name to a full provider config.

    If the name matches a built-in provider, fill in base_url, protocol, models.
    Returns None if not found.
    """
    reg_provider = get_provider(name)
    if not reg_provider:
        return None
    return {
        "name": reg_provider["name"],
        "base_url": reg_provider["base_url"],
        "api_key": api_key,
        "protocol": reg_provider.get("protocol", "openai-compatible"),
        "models": reg_provider.get("models", []),
    }


def update_registry() -> bool:
    """Force-update the registry cache from remote.

    Returns True if successful.
    """
    remote = fetch_remote()
    if remote:
        print(f"  Registry updated (v{remote.get('version', '?')})")
        print(f"    Agents: {len(remote.get('agents', {}))}")
        print(f"    Providers: {len(remote.get('providers', {}))}")
        return True
    print("  Failed to fetch remote registry")
    return False


def print_agents() -> None:
    """Print all known agents."""
    agents = list_agents()
    print(f"\n  Known Agents ({len(agents)})")
    print("  " + "=" * 50)
    for slug, info in sorted(agents.items()):
        print(f"  {slug:<20} {info['name']}")
        if info.get("description"):
            print(f"    {info['description']}")
    print()


def print_providers() -> None:
    """Print all known providers."""
    providers = list_providers()
    print(f"\n  Known Providers ({len(providers)})")
    print("  " + "=" * 50)
    for slug, info in sorted(providers.items()):
        models = ", ".join(info.get("models", [])[:3])
        if len(info.get("models", [])) > 3:
            models += ", ..."
        print(f"  {slug:<20} {info['name']:<20} {info['base_url']}")
        if models:
            print(f"    models: {models}")
    print()
