"""Snapshot management — save and restore agent configurations.

Each agent has different config files. A snapshot captures all config files
for a set of agents, allowing one-click restore to a known-good state.

Snapshots are stored in ~/.apm/snapshots/<name>/
"""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime
from pathlib import Path

from apm.config import (
    APM_DIR,
    CLAUDE_CODE_CONFIG,
    CODEX_AUTH,
    CODEX_CONFIG,
    HERMES_CONFIG,
    HERMES_ENV,
    OPENCLAW_CONFIG,
    WORKBUDDY_CONFIG,
    ZCODE_CONFIG,
)
from apm.detect import get_installed_agents

SNAPSHOTS_DIR = APM_DIR / "snapshots"

# Map agent name → list of config files to snapshot
AGENT_CONFIG_FILES: dict[str, list[Path]] = {
    "claude-code": [CLAUDE_CODE_CONFIG],
    "codex": [CODEX_CONFIG, CODEX_AUTH],
    "hermes": [HERMES_CONFIG, HERMES_ENV],
    "openclaw": [OPENCLAW_CONFIG],
    "zcode": [ZCODE_CONFIG],
    "workbuddy": [WORKBUDDY_CONFIG],
}


def save_snapshot(
    name: str | None = None,
    agents: list[str] | None = None,
) -> dict:
    """Save current agent configs as a snapshot.

    Args:
        name: Snapshot name (default: timestamp)
        agents: Agent names to snapshot (default: all installed)

    Returns:
        dict with snapshot info
    """
    if name is None:
        name = datetime.now().strftime("%Y%m%d-%H%M%S")

    target_agents = agents if agents else get_installed_agents()
    if not target_agents:
        return {"name": name, "agents": {}, "error": "No installed agents found"}

    snapshot_dir = SNAPSHOTS_DIR / name
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    result = {"name": name, "agents": {}, "path": str(snapshot_dir)}

    for agent_name in target_agents:
        config_files = AGENT_CONFIG_FILES.get(agent_name, [])
        if not config_files:
            result["agents"][agent_name] = {"status": "skipped", "reason": "unknown agent"}
            continue

        agent_dir = snapshot_dir / agent_name
        agent_dir.mkdir(parents=True, exist_ok=True)

        saved_files = []
        for config_path in config_files:
            if config_path.exists():
                dest = agent_dir / config_path.name
                shutil.copy2(config_path, dest)
                saved_files.append(config_path.name)

        if saved_files:
            result["agents"][agent_name] = {"status": "saved", "files": saved_files}
        else:
            result["agents"][agent_name] = {"status": "skipped", "reason": "no config files"}

    # Save snapshot metadata
    meta = {
        "name": name,
        "created_at": datetime.now().isoformat(),
        "agents": list(result["agents"].keys()),
    }
    (snapshot_dir / "meta.json").write_text(json.dumps(meta, indent=2))

    return result


def restore_snapshot(
    name: str,
    agents: list[str] | None = None,
) -> dict:
    """Restore agent configs from a snapshot.

    Args:
        name: Snapshot name
        agents: Agent names to restore (default: all in snapshot)

    Returns:
        dict with restore results
    """
    snapshot_dir = SNAPSHOTS_DIR / name
    if not snapshot_dir.exists():
        return {"name": name, "error": f"Snapshot '{name}' not found"}

    # Read metadata
    meta_path = snapshot_dir / "meta.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
        available_agents = meta.get("agents", [])
    else:
        # Discover from directory structure
        available_agents = [d.name for d in snapshot_dir.iterdir() if d.is_dir()]

    target_agents = agents if agents else available_agents

    result = {"name": name, "agents": {}}

    for agent_name in target_agents:
        agent_dir = snapshot_dir / agent_name
        if not agent_dir.exists():
            result["agents"][agent_name] = {"status": "skipped", "reason": "not in snapshot"}
            continue

        config_files = AGENT_CONFIG_FILES.get(agent_name, [])
        if not config_files:
            result["agents"][agent_name] = {"status": "skipped", "reason": "unknown agent"}
            continue

        restored_files = []
        for config_path in config_files:
            src = agent_dir / config_path.name
            if src.exists():
                # Backup current config before restore
                if config_path.exists():
                    ts = datetime.now().strftime("%Y%m%d%H%M%S")
                    bak = config_path.with_suffix(f".bak.{ts}")
                    shutil.copy2(config_path, bak)

                config_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, config_path)
                restored_files.append(config_path.name)

        if restored_files:
            result["agents"][agent_name] = {"status": "restored", "files": restored_files}
        else:
            result["agents"][agent_name] = {"status": "skipped", "reason": "no files in snapshot"}

    return result


def list_snapshots() -> list[dict]:
    """List all saved snapshots."""
    if not SNAPSHOTS_DIR.exists():
        return []

    snapshots = []
    for d in sorted(SNAPSHOTS_DIR.iterdir(), reverse=True):
        if not d.is_dir():
            continue
        meta_path = d / "meta.json"
        if meta_path.exists():
            meta = json.loads(meta_path.read_text())
            snapshots.append({
                "name": d.name,
                "created_at": meta.get("created_at", "?"),
                "agents": meta.get("agents", []),
            })
        else:
            agents = [sub.name for sub in d.iterdir() if sub.is_dir()]
            snapshots.append({
                "name": d.name,
                "created_at": "?",
                "agents": agents,
            })

    return snapshots


def delete_snapshot(name: str) -> bool:
    """Delete a snapshot."""
    snapshot_dir = SNAPSHOTS_DIR / name
    if not snapshot_dir.exists():
        return False
    shutil.rmtree(snapshot_dir)
    return True


def print_save_result(result: dict) -> None:
    """Print formatted save result."""
    print(f"\n  Snapshot saved: {result['name']}")
    print(f"  Path: {result.get('path', '?')}")
    print("  " + "-" * 40)
    for agent, info in result.get("agents", {}).items():
        if info["status"] == "saved":
            files = ", ".join(info["files"])
            print(f"  ✓  {agent:<15} {files}")
        else:
            print(f"  ⊘  {agent:<15} {info.get('reason', 'skipped')}")
    print()


def print_restore_result(result: dict) -> None:
    """Print formatted restore result."""
    print(f"\n  Snapshot restored: {result['name']}")
    print("  " + "-" * 40)
    for agent, info in result.get("agents", {}).items():
        if info["status"] == "restored":
            files = ", ".join(info["files"])
            print(f"  ✓  {agent:<15} {files}")
        else:
            print(f"  ⊘  {agent:<15} {info.get('reason', 'skipped')}")
    print()


def print_snapshots() -> None:
    """Print all saved snapshots."""
    snapshots = list_snapshots()
    if not snapshots:
        print("\n  No snapshots saved.")
        print("  Use 'apm snapshot save' to create one.\n")
        return

    print(f"\n  Snapshots ({len(snapshots)})")
    print("  " + "=" * 50)
    for s in snapshots:
        agents = ", ".join(s["agents"])
        print(f"  {s['name']:<25} {s['created_at'][:19]}")
        print(f"    agents: {agents}")
    print()
