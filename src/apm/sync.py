"""Sync engine — push provider config to agents.

Two operations:
  - sync: write provider config (smart: skip if already identical)
  - switch: write + activate (enable provider and optionally set model)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from apm.agents.registry import ADAPTERS
from apm.config import SYNC_STATE_FILE, atomic_write
from apm.detect import detect_agent, get_installed_agents
from apm.providers import get as get_provider

logger = logging.getLogger(__name__)


def _load_state() -> dict:
    if SYNC_STATE_FILE.exists():
        with open(SYNC_STATE_FILE) as f:
            return json.load(f)
    return {"syncs": {}}


def _save_state(state: dict) -> None:
    atomic_write(SYNC_STATE_FILE, json.dumps(state, indent=2, ensure_ascii=False) + "\n")


def sync_provider(
    provider_name: str,
    agents: list[str] | None = None,
    dry_run: bool = False,
) -> list[dict]:
    """Smart sync: write provider config, skip if already present with same URL+key.

    Returns:
        list of results: [{agent, status, message}]
    """
    _provider = get_provider(provider_name)
    if not _provider:
        return [
            {"agent": None, "status": "error", "message": f"Provider '{provider_name}' not found"}
        ]
    provider = dict(_provider)
    if "model_meta" in provider and "_model_meta" not in provider:
        provider["_model_meta"] = provider["model_meta"]

    targets = agents if agents else get_installed_agents()

    if not targets:
        return [{"agent": None, "status": "warning", "message": "No installed agents found"}]

    snapshot_name = None
    if not dry_run:
        try:
            from apm.snapshot import save_snapshot
            ts = datetime.now().strftime("%Y%m%d%H%M%S")
            snapshot_name = f"auto-pre-sync-{provider_name}-{ts}"
            save_snapshot(name=snapshot_name, agents=targets)
            logger.info("Auto-snapshot saved: %s", snapshot_name)
        except Exception as e:
            logger.warning("Auto-snapshot failed (sync will continue): %s", e)
            snapshot_name = None

    results: list[dict] = []
    for agent_name in targets:
        adapter = ADAPTERS.get(agent_name)
        if not adapter:
            results.append(
                {"agent": agent_name, "status": "error", "message": f"Unknown agent: {agent_name}"}
            )
            continue

        det = detect_agent(agent_name)
        if not det["installed"]:
            results.append({"agent": agent_name, "status": "skipped", "message": "Not installed"})
            continue

        try:
            if dry_run:
                if adapter.has_provider(provider):
                    results.append({
                        "agent": agent_name,
                        "status": "dry-run",
                        "message": "SKIP (already configured with same URL+key)",
                    })
                else:
                    current = adapter.read_provider()
                    results.append({
                        "agent": agent_name,
                        "status": "dry-run",
                        "message": _format_change(current, provider),
                    })
            else:
                if adapter.has_provider(provider):
                    results.append({
                        "agent": agent_name,
                        "status": "skipped",
                        "message": "Already configured (same URL+key)",
                    })
                else:
                    adapter.write_provider(provider)
                    results.append({"agent": agent_name, "status": "synced", "message": "OK"})
        except Exception as e:
            results.append({"agent": agent_name, "status": "error", "message": str(e)})

    if not dry_run:
        state = _load_state()
        for r in results:
            if r["status"] == "synced":
                state["syncs"][r["agent"]] = {
                    "provider": provider_name,
                    "synced_at": datetime.now(timezone.utc).isoformat(),
                    "snapshot": snapshot_name,
                }
        _save_state(state)

        try:
            from apm.snapshot import cleanup_auto_snapshots
            cleaned = cleanup_auto_snapshots()
            if cleaned:
                logger.info("Cleaned up %d old auto-snapshots", cleaned)
        except Exception as e:
            logger.debug("Auto-snapshot cleanup failed: %s", e)

    return results


def switch_provider(
    provider_name: str,
    model: str | None = None,
    agents: list[str] | None = None,
    dry_run: bool = False,
) -> list[dict]:
    """Switch = sync + activate. Write config if needed, then enable the provider.

    Args:
        provider_name: slug of the provider to switch to
        model: specific model to activate (None = use first available)
        agents: list of agent names (None = all installed)
        dry_run: if True, only preview changes
    """
    _provider = get_provider(provider_name)
    if not _provider:
        return [
            {"agent": None, "status": "error", "message": f"Provider '{provider_name}' not found"}
        ]
    provider = dict(_provider)
    if "model_meta" in provider and "_model_meta" not in provider:
        provider["_model_meta"] = provider["model_meta"]

    targets = agents if agents else get_installed_agents()
    if not targets:
        return [{"agent": None, "status": "warning", "message": "No installed agents found"}]

    snapshot_name = None
    if not dry_run:
        try:
            from apm.snapshot import save_snapshot
            ts = datetime.now().strftime("%Y%m%d%H%M%S")
            snapshot_name = f"auto-pre-switch-{provider_name}-{ts}"
            save_snapshot(name=snapshot_name, agents=targets)
        except Exception as e:
            logger.warning("Auto-snapshot failed: %s", e)

    results: list[dict] = []
    for agent_name in targets:
        adapter = ADAPTERS.get(agent_name)
        if not adapter:
            results.append({"agent": agent_name, "status": "error", "message": "Unknown agent"})
            continue

        det = detect_agent(agent_name)
        if not det["installed"]:
            results.append({"agent": agent_name, "status": "skipped", "message": "Not installed"})
            continue

        try:
            if dry_run:
                already = adapter.has_provider(provider)
                msg = "ACTIVATE" if already else "WRITE + ACTIVATE"
                if model:
                    msg += f" (model={model})"
                results.append({"agent": agent_name, "status": "dry-run", "message": msg})
            else:
                if not adapter.has_provider(provider):
                    adapter.write_provider(provider)
                adapter.activate_provider(provider, model=model)
                results.append({
                    "agent": agent_name,
                    "status": "switched",
                    "message": f"Active → {provider_name}" + (f"/{model}" if model else ""),
                })
        except Exception as e:
            results.append({"agent": agent_name, "status": "error", "message": str(e)})

    if not dry_run:
        state = _load_state()
        for r in results:
            if r["status"] == "switched":
                state["syncs"][r["agent"]] = {
                    "provider": provider_name,
                    "model": model,
                    "synced_at": datetime.now(timezone.utc).isoformat(),
                    "snapshot": snapshot_name,
                }
        _save_state(state)

    return results


def get_status() -> list[dict]:
    """Get current provider status for all known agents."""
    state = _load_state()
    results: list[dict] = []
    for name, adapter in ADAPTERS.items():
        det = detect_agent(name)
        if not det["installed"]:
            results.append({"agent": name, "installed": False, "current": None})
            continue
        try:
            current = adapter.read_provider()
        except Exception:
            current = None
        sync_info = state.get("syncs", {}).get(name, {})
        results.append({
            "agent": name,
            "installed": True,
            "current": current,
            "last_sync": sync_info,
        })
    return results


def print_status() -> None:
    """Print formatted status."""
    from apm.colors import bold, cyan, dim, green, yellow
    from apm.providers import list_all

    status = get_status()
    providers = list_all()

    print(f"\n  {bold('Agent Provider Status')}")
    print("  " + "=" * 60)

    if providers:
        slugs = [p["slug"] for p in providers]
        print(f"  Providers: {cyan(', '.join(slugs))}")
    else:
        print(f"  {yellow('No providers configured.')} Run 'apm provider add'")

    print()
    for s in status:
        if not s["installed"]:
            print(f"  {dim('✗')}  {dim(s['agent']):<15}  {dim('(not installed)')}")
            continue
        cur = s["current"]
        if cur:
            url = cur.get("base_url", "?")
            model = cur.get("model")
            model_str = f"  model={cyan(str(model))}" if model else ""
            print(f"  {green('✓')}  {bold(s['agent']):<15}  {url}{model_str}")
        else:
            print(f"  {yellow('✓')}  {s['agent']:<15}  {dim('(no provider configured)')}")
    print()


def print_sync_results(results: list[dict], dry_run: bool = False) -> None:
    """Print formatted sync results."""
    from apm.colors import bold, cyan, dim, green, red, yellow

    prefix = f"{yellow('[DRY RUN]')} " if dry_run else ""
    print(f"\n  {prefix}{bold('Sync Results')}")
    print("  " + "=" * 50)
    color_map = {
        "synced": lambda t: f"{green('✓')}  {t}",
        "switched": lambda t: f"{green('⚡')} {t}",
        "error": lambda t: f"{red('✗')}  {t}",
        "skipped": lambda t: f"{dim('⊘')}  {dim(t)}",
        "dry-run": lambda t: f"{cyan('→')}  {t}",
        "warning": lambda t: f"{yellow('⚠')}  {t}",
    }
    for r in results:
        agent = r["agent"] or "(global)"
        msg = r["message"]
        fmt = color_map.get(r["status"], lambda t: f"?  {t}")
        print(f"  {fmt(f'{agent:<15}  {msg}')}")
    print()


def _format_change(current: dict | None, new: dict) -> str:
    """Format a dry-run change description."""
    if not current:
        return f"NEW: {new['base_url']}"
    old_url = current.get("base_url", "?")
    new_url = new["base_url"]
    if old_url == new_url:
        return f"UPDATE key only (url unchanged: {new_url})"
    return f"CHANGE: {old_url} → {new_url}"
