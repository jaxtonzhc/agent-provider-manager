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
    from apm.colors import bold, cyan, dim, green

    results = detect_all()
    print(f"\n  {bold('Installed AI Agents')} (sync-ready)")
    print("  " + "=" * 45)
    for r in results:
        if r["installed"]:
            print(f"  {green('✓')}  {r['name']:<15}")
        else:
            print(f"  {dim('✗')}  {dim(r['name'])}")
    installed = [r["name"] for r in results if r["installed"]]
    print(f"\n  {bold(str(len(installed)))}/{len(results)} agents detected")

    detect_only = _get_detect_only_agents()
    if detect_only:
        print(f"\n  {cyan('Detect-only')} (no sync adapter yet):")
        for name in detect_only:
            print(f"  {dim('·')}  {dim(name)}")
    print()


def _get_detect_only_agents() -> list[str]:
    """Return agent names known in registry but without a sync adapter."""
    try:
        from apm.registry import list_agents
        registry_agents = set(list_agents().keys())
        adapter_agents = set(ADAPTERS.keys())
        return sorted(registry_agents - adapter_agents)
    except Exception:
        return []
