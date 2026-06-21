"""Self-update mechanism for apm."""

from __future__ import annotations

import logging
import subprocess
import sys

from apm import __version__

logger = logging.getLogger(__name__)


def self_update() -> bool:
    """Update apm to the latest version.

    Tries pipx first, then pip. Returns True if updated.
    """
    print(f"\n  Current version: {__version__}")
    print("  Checking for updates...\n")

    # Try pipx
    if _try_pipx_update():
        return True

    # Try pip
    if _try_pip_update():
        return True

    print("  Failed to update. Try manually:")
    print("    pipx upgrade agent-provider-manager")
    print("    pip install -U agent-provider-manager")
    return False


def _try_pipx_update() -> bool:
    """Try updating via pipx."""
    try:
        result = subprocess.run(
            ["pipx", "upgrade", "agent-provider-manager"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            if "upgraded" in result.stdout.lower() or "already" in result.stdout.lower():
                print(f"  ✓ Updated via pipx")
                _print_new_version()
                return True
            print(f"  Already up to date (pipx)")
            return True
    except FileNotFoundError:
        logger.debug("pipx not found")
    except Exception as e:
        logger.debug("pipx update failed: %s", e)
    return False


def _try_pip_update() -> bool:
    """Try updating via pip."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-U", "agent-provider-manager"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            if "successfully installed" in result.stdout.lower():
                print(f"  ✓ Updated via pip")
                _print_new_version()
                return True
            print(f"  Already up to date (pip)")
            return True
        else:
            logger.debug("pip update stderr: %s", result.stderr)
    except Exception as e:
        logger.debug("pip update failed: %s", e)
    return False


def _print_new_version() -> None:
    """Print the new version after update."""
    try:
        result = subprocess.run(
            ["apm", "version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            print(f"  {result.stdout.strip()}")
    except Exception:
        pass
