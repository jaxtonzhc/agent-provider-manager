"""Provider registry management."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from apm.config import APM_DIR, PROVIDERS_FILE, atomic_write

logger = logging.getLogger(__name__)


def _ensure_dir() -> None:
    """Ensure the apm data directory exists."""
    APM_DIR.mkdir(parents=True, exist_ok=True)


def _load() -> dict:
    """Load providers.json."""
    if not PROVIDERS_FILE.exists():
        return {"providers": {}}
    try:
        with open(PROVIDERS_FILE) as f:
            data = json.load(f)
        data.pop("active_provider", None)
        return data
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Failed to load providers.json: %s", e)
        return {"providers": {}}


def _save(data: dict) -> None:
    """Save providers.json atomically with restricted permissions."""
    _ensure_dir()
    atomic_write(PROVIDERS_FILE, json.dumps(data, indent=2, ensure_ascii=False) + "\n", mode=0o600)


def add(
    name: str,
    base_url: str,
    api_key: str,
    protocol: str = "openai-compatible",
    models: list[str] | None = None,
    anthropic_base_url: str | None = None,
    model_meta: dict | None = None,
    alias: str | None = None,
) -> str:
    """Add a new provider. Returns the provider slug."""
    data = _load()
    slug = alias or name.lower().replace(" ", "-").replace("_", "-")
    # Deduplicate: append suffix if slug already exists
    if slug in data["providers"] and not alias:
        i = 2
        while f"{slug}-{i}" in data["providers"]:
            i += 1
        slug = f"{slug}-{i}"
    entry = {
        "name": name,
        "base_url": base_url.rstrip("/"),
        "api_key": api_key,
        "protocol": protocol,
        "models": models or [],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if anthropic_base_url:
        entry["anthropic_base_url"] = anthropic_base_url.rstrip("/")
    if model_meta:
        entry["model_meta"] = model_meta
    data["providers"][slug] = entry
    _save(data)
    return slug


def remove(name: str) -> None:
    """Remove a provider by name or slug."""
    data = _load()
    slug = _resolve_slug(data, name)
    if slug is None:
        raise ValueError(f"Provider '{name}' not found")
    del data["providers"][slug]
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
        result.append(p)
    return result


def rename(old_slug: str, new_slug: str) -> None:
    """Rename a provider's slug."""
    data = _load()
    resolved = _resolve_slug(data, old_slug)
    if resolved is None:
        raise ValueError(f"Provider '{old_slug}' not found")
    new_slug = new_slug.lower().replace(" ", "-").replace("_", "-")
    if new_slug in data["providers"]:
        raise ValueError(f"Provider '{new_slug}' already exists")
    entry = data["providers"].pop(resolved)
    data["providers"][new_slug] = entry
    _save(data)


def update(name: str, **kwargs) -> None:
    """Update provider fields. Only non-None kwargs are applied."""
    data = _load()
    slug = _resolve_slug(data, name)
    if slug is None:
        raise ValueError(f"Provider '{name}' not found")
    entry = data["providers"][slug]
    for k, v in kwargs.items():
        if v is None:
            continue
        if k == "base_url":
            entry["base_url"] = v.rstrip("/")
        elif k == "anthropic_base_url":
            if v == "":
                entry.pop("anthropic_base_url", None)
            else:
                entry["anthropic_base_url"] = v.rstrip("/")
        elif k == "api_key":
            entry["api_key"] = v
        elif k == "models":
            entry["models"] = (
                v if isinstance(v, list)
                else [m.strip() for m in v.split(",") if m.strip()]
            )
        elif k == "protocol":
            entry["protocol"] = v
    _save(data)


def _mask_key(key: str) -> str:
    """Mask API key, showing only prefix and last 2 chars."""
    if len(key) <= 6:
        return "***"
    prefix = key[:4]
    return f"{prefix}{'*' * min(len(key) - 6, 20)}..{key[-2:]}"


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
    print(f"\n  Providers ({len(providers)})")
    print("  " + "=" * 55)
    for p in providers:
        masked = _mask_key(p["api_key"])
        print(f"    {p['slug']:<20} {p['base_url']}")
        print(f"      key={masked}  protocol={p['protocol']}")
        if p.get("anthropic_base_url"):
            print(f"      anthropic={p['anthropic_base_url']}")
        if p["models"]:
            print(f"      models={', '.join(p['models'])}")
    print()


def print_detail(name: str) -> None:
    """Print detailed provider info."""
    p = get(name)
    if not p:
        print(f"  Provider '{name}' not found.")
        return
    print(f"\n  Provider: {p['name']} ({p['slug']})")
    print(f"  Base URL:      {p['base_url']}")
    if p.get("anthropic_base_url"):
        print(f"  Anthropic URL: {p['anthropic_base_url']}")
    print(f"  API Key:       {_mask_key(p['api_key'])}")
    print(f"  Protocol:      {p['protocol']}")
    if p["models"]:
        print("  Models:")
        meta = p.get("model_meta", {})
        for mid in p["models"]:
            m = meta.get(mid, {})
            tags = []
            ctx = m.get("context")
            if ctx:
                if ctx >= 1000000:
                    tags.append(f"{ctx // 1000000}M ctx")
                else:
                    tags.append(f"{ctx // 1000}K ctx")
            if m.get("reasoning"):
                tags.append("reasoning")
            if m.get("vision"):
                tags.append("vision")
            tag_str = f"  ({', '.join(tags)})" if tags else ""
            print(f"    - {mid}{tag_str}")
    else:
        print("  Models:        (none)")
    print(f"  Created:       {p['created_at']}")
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
            url = current.get("base_url", "")
            api_key = current.get("api_key", "")
            if not url:
                continue

            # Try to find existing provider by API key match
            match = _find_by_key(api_key)
            if match:
                model = current.get("model")
                merged_model = False
                if model:
                    merged_model = _merge_model(match, model)
                msg = f"same key as '{match}'"
                if merged_model:
                    msg += f", merged model '{model}'"
                imported.append({
                    "agent": agent_name,
                    "provider": match,
                    "status": "merged",
                    "message": msg,
                })
                continue

            slug = _guess_provider_slug(url)
            if not slug:
                slug = agent_name

            existing = get(slug)
            if existing:
                imported.append({
                    "agent": agent_name,
                    "provider": slug,
                    "status": "exists",
                })
                continue

            add(
                name=slug.replace("-", " ").title(),
                base_url=url,
                api_key=api_key,
                protocol=current.get("protocol", "openai-compatible"),
                models=[current["model"]] if current.get("model") else [],
            )
            imported.append({
                "agent": agent_name,
                "provider": slug,
                "status": "imported",
            })
        except (json.JSONDecodeError, OSError, KeyError, ValueError) as e:
            logger.warning("Failed to import from %s: %s", agent_name, e)
            imported.append({
                "agent": agent_name,
                "provider": None,
                "status": "error",
            })

    return imported


def _merge_model(slug: str, model_id: str) -> bool:
    """Add a model to an existing provider if not already present. Returns True if added."""
    data = _load()
    p = data["providers"].get(slug)
    if not p:
        return False
    models = p.get("models", [])
    if model_id in models:
        return False
    models.append(model_id)
    p["models"] = models
    _save(data)
    return True


def _find_by_key(api_key: str) -> str | None:
    """Find an existing provider with the same API key."""
    if not api_key:
        return None
    data = _load()
    for slug, p in data["providers"].items():
        if p.get("api_key") == api_key:
            return slug
    return None


def _guess_provider_slug(url: str) -> str | None:
    """Guess provider slug from base URL using registry data."""
    from apm.registry import list_providers as list_registry_providers

    url_lower = url.lower()
    for slug, info in list_registry_providers().items():
        for variant in info.get("variants", {}).values():
            if variant.get("base_url", "").lower().rstrip("/") in url_lower:
                return slug
            # Also match by domain
            from urllib.parse import urlparse
            try:
                domain = urlparse(variant.get("base_url", "")).netloc
                if domain and domain in url_lower:
                    return slug
            except Exception:
                pass
    return None


def test_provider(name: str, timeout: float = 10.0) -> dict:
    """Test provider connectivity by sending a simple API request.

    Returns dict with: status (ok|error), message, latency_ms
    """
    import time
    from urllib.error import HTTPError, URLError
    from urllib.request import Request, urlopen

    p = get(name)
    if not p:
        return {"status": "error", "message": f"Provider '{name}' not found"}

    base_url = p["base_url"].rstrip("/")
    api_key = p["api_key"]

    # Try /models endpoint (works for most OpenAI-compatible providers)
    test_url = f"{base_url}/models"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "apm-cli",
    }

    start = time.monotonic()
    try:
        req = Request(test_url, headers=headers)
        with urlopen(req, timeout=timeout) as resp:
            elapsed = (time.monotonic() - start) * 1000
            return {
                "status": "ok",
                "message": f"Connected ({resp.status})",
                "latency_ms": round(elapsed),
            }
    except HTTPError as e:
        elapsed = (time.monotonic() - start) * 1000
        if e.code == 401:
            return {"status": "error", "message": "Authentication failed (401) — check API key",
                    "latency_ms": round(elapsed)}
        if e.code == 403:
            return {"status": "error", "message": "Access forbidden (403) — check permissions",
                    "latency_ms": round(elapsed)}
        # 404 on /models is common for non-OpenAI providers, but connection works
        if e.code == 404:
            msg = "Connected (404 — /models may not be supported)"
            return {"status": "ok", "message": msg,
                    "latency_ms": round(elapsed)}
        return {"status": "error", "message": f"HTTP {e.code}: {e.reason}",
                "latency_ms": round(elapsed)}
    except URLError as e:
        elapsed = (time.monotonic() - start) * 1000
        return {"status": "error", "message": f"Connection failed: {e.reason}",
                "latency_ms": round(elapsed)}
    except Exception as e:
        elapsed = (time.monotonic() - start) * 1000
        return {"status": "error", "message": str(e), "latency_ms": round(elapsed)}


def fetch_models(
    base_url: str, api_key: str, timeout: float = 15.0,
) -> list[str]:
    """Fetch available model list from /v1/models endpoint.

    Returns sorted model IDs (newest version first).
    """
    import json as _json
    from urllib.error import HTTPError, URLError
    from urllib.request import Request, urlopen

    url = base_url.rstrip("/") + "/models"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "apm-cli",
    }

    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=timeout) as resp:
            body = _json.loads(resp.read())
    except (HTTPError, URLError, OSError) as e:
        logger.warning("Failed to fetch models from %s: %s", url, e)
        return []

    raw = body.get("data", body.get("models", []))
    ids: list[str] = []
    for item in raw:
        mid = item.get("id") if isinstance(item, dict) else str(item)
        if mid:
            ids.append(mid)

    return sort_models_by_version(ids)


def sort_models_by_version(model_ids: list[str]) -> list[str]:
    """Sort model IDs by embedded version number, highest first.

    Version extraction: find the first float-like substring (e.g. "4.5", "2.5").
    Models with higher versions come first. Ties broken alphabetically.
    """
    import re

    def _version_key(mid: str) -> tuple:
        nums = re.findall(r"\d+(?:\.\d+)?", mid)
        if not nums:
            return (1, 0.0, mid)  # no version → sort last
        best = max(float(n) for n in nums)
        return (0, -best, mid)  # versioned → sort first, highest version first

    return sorted(model_ids, key=_version_key)


def fuzzy_match(name: str, candidates: list[str], threshold: int = 3) -> list[str]:
    """Find candidates within edit distance threshold of name."""
    name_lower = name.lower()
    results = []
    for c in candidates:
        c_lower = c.lower()
        if name_lower in c_lower or c_lower in name_lower:
            results.append(c)
            continue
        # Simple Levenshtein distance
        dist = _edit_distance(name_lower, c_lower)
        if dist <= threshold:
            results.append(c)
    return results


def _edit_distance(a: str, b: str) -> int:
    """Levenshtein distance."""
    if len(a) < len(b):
        return _edit_distance(b, a)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        curr = [i + 1]
        for j, cb in enumerate(b):
            curr.append(min(prev[j + 1] + 1, curr[j] + 1, prev[j] + (ca != cb)))
        prev = curr
    return prev[-1]
