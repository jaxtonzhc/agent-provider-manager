"""Agent installation detection."""

from __future__ import annotations

from apm.agents.registry import ADAPTERS


def detect_agent(name: str) -> dict:
    """Detect if a specific agent is installed.

    Returns:
        dict with keys: name, installed (bool)
    """
    adapter = ADAPTERS.get(name)
    if not adapter:
        return {"name": name, "installed": False}
    return {"name": name, "installed": adapter.is_installed()}


def detect_all() -> list[dict]:
    """Detect all known agents."""
    return [detect_agent(name) for name in ADAPTERS]


def get_installed_agents() -> list[str]:
    """Return list of installed agent names."""
    return [name for name, adapter in ADAPTERS.items() if adapter.is_installed()]


def print_scan_results() -> None:
    """Print formatted scan results."""
    results = detect_all()
    print("\n  Installed AI Agents")
    print("  " + "=" * 45)
    for r in results:
        status = "✓" if r["installed"] else "✗"
        print(f"  {status}  {r['name']:<15}")
    print()
    installed = [r["name"] for r in results if r["installed"]]
    print(f"  {len(installed)}/{len(results)} agents detected\n")
