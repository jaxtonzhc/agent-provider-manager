"""Sync engine — push provider config to agents."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from apm.agents.registry import ADAPTERS
from apm.config import APM_DIR, SYNC_STATE_FILE
from apm.detect import detect_agent, get_installed_agents
from apm.providers import get as get_provider

logger = logging.getLogger(__name__)


def _load_state() -> dict:
    """Load sync state from disk."""
    if SYNC_STATE_FILE.exists():
        with open(SYNC_STATE_FILE) as f:
            return json.load(f)
    return {"syncs": {}}


def _save_state(state: dict) -> None:
    """Save sync state to disk."""
    APM_DIR.mkdir(parents=True, exist_ok=True)
    with open(SYNC_STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def sync_provider(
    provider_name: str,
    agents: list[str] | None = None,
    dry_run: bool = False,
) -> list[dict]:
    """Sync a provider to specified agents (or all installed).

    Returns:
        list of results: [{agent, status, message}]
    """
    provider = get_provider(provider_name)
    if not provider:
        return [
            {"agent": None, "status": "error", "message": f"Provider '{provider_name}' not found"}
        ]

    targets = agents if agents else get_installed_agents()

    if not targets:
        return [{"agent": None, "status": "warning", "message": "No installed agents found"}]

    # Auto-snapshot before sync (unless dry-run)
    snapshot_name = None
    if not dry_run:
        try:
            from apm.snapshot import save_snapshot
            snapshot_name = f"auto-pre-sync-{provider_name}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
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
                current = adapter.read_provider()
                results.append({
                    "agent": agent_name,
                    "status": "dry-run",
                    "message": _format_change(current, provider),
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
    status = get_status()
    print("\n  Agent Provider Status")
    print("  " + "=" * 60)
    for s in status:
        if not s["installed"]:
            print(f"  ✗  {s['agent']:<15}  (not installed)")
            continue
        cur = s["current"]
        if cur:
            url = cur.get("base_url", "?")
            model = cur.get("model", "?")
            print(f"  ✓  {s['agent']:<15}  {url}")
            if model:
                print(f"      model={model}")
        else:
            print(f"  ✓  {s['agent']:<15}  (no provider configured)")
        if s.get("last_sync"):
            ts = s["last_sync"].get("synced_at", "?")[:19]
            print(f"      last sync: {s['last_sync'].get('provider', '?')} @ {ts}")
    print()


def print_sync_results(results: list[dict], dry_run: bool = False) -> None:
    """Print formatted sync results."""
    prefix = "[DRY RUN] " if dry_run else ""
    print(f"\n  {prefix}Sync Results")
    print("  " + "=" * 50)
    icons = {"synced": "✓", "error": "✗", "skipped": "⊘", "dry-run": "→", "warning": "⚠"}
    for r in results:
        icon = icons.get(r["status"], "?")
        agent = r["agent"] or "(global)"
        print(f"  {icon}  {agent:<15}  {r['message']}")
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
