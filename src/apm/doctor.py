"""Diagnostic tool — check apm health and agent configurations."""

from __future__ import annotations

import json
import os
import platform
import sys
from pathlib import Path

from apm import __version__
from apm.agents.registry import ADAPTERS
from apm.config import AGENT_CONFIG_PATHS, APM_DIR, LOG_FILE, PROVIDERS_FILE


def run_diagnostics(fix: bool = False) -> None:
    """Run full diagnostics."""
    print("\n  Agent Provider Manager Doctor")
    print("  " + "=" * 40)

    # 1. Check apm
    print(f"\n  ✓ apm v{__version__}")

    # 2. Check Python
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print(f"  ✓ Python {py_ver}")

    # 3. Check platform
    print(f"  ✓ {platform.system()} {platform.machine()}")

    # 4. Check ~/.apm/ directory
    if APM_DIR.exists():
        print(f"  ✓ {APM_DIR} exists")
    else:
        if fix:
            APM_DIR.mkdir(parents=True, exist_ok=True)
            print(f"  ✓ {APM_DIR} created")
        else:
            print(f"  ✗ {APM_DIR} not found")
            print(f"    → Fix: mkdir -p {APM_DIR}")

    # 5. Check providers.json
    if PROVIDERS_FILE.exists():
        try:
            with open(PROVIDERS_FILE) as f:
                data = json.load(f)
            count = len(data.get("providers", {}))
            print(f"  ✓ providers.json valid ({count} providers)")
        except json.JSONDecodeError:
            print("  ✗ providers.json is corrupted")
            if fix:
                PROVIDERS_FILE.write_text('{"providers": {}}')
                print("    → Fixed: reset to empty")
    else:
        print("  ✗ providers.json not found")
        if fix:
            PROVIDERS_FILE.write_text('{"providers": {}}')
            print("    → Fixed: created empty")

    # 6. Check agents
    print("\n  Agents:")
    for name, adapter in ADAPTERS.items():
        if adapter.is_installed():
            # Check config writability
            config_path = _get_agent_config_path(name)
            if config_path and config_path.exists():
                writable = os.access(config_path, os.W_OK)
                if writable:
                    print(f"  ✓ {name:<15} installed, config writable")
                else:
                    print(f"  ✗ {name:<15} installed, config NOT writable")
                    if fix:
                        os.chmod(config_path, 0o644)
                        print(f"    → Fixed: chmod 644 {config_path}")
            else:
                print(f"  ✓ {name:<15} installed")
        else:
            print(f"  ⊘ {name:<15} not installed")

    # 7. Check log file
    if LOG_FILE.exists():
        size = LOG_FILE.stat().st_size
        if size > 10 * 1024 * 1024:  # > 10MB
            print(f"\n  ⚠ Log file is large ({size // 1024}KB)")
            if fix:
                LOG_FILE.write_text("")
                print("    → Fixed: cleared log file")
        else:
            print(f"\n  ✓ Log file OK ({size // 1024}KB)")
    else:
        print("\n  ⊘ No log file yet")

    print()


def _get_agent_config_path(name: str) -> Path | None:
    """Get the primary config path for an agent."""
    paths = AGENT_CONFIG_PATHS.get(name, [])
    return paths[0] if paths else None
