"""Base class for agent configuration adapters."""

from __future__ import annotations

import shutil
import socket
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path


class AgentAdapter(ABC):
    """Base class for agent config adapters.

    Each adapter knows how to read and write provider configuration
    for a specific AI coding agent.  Subclasses must implement:
      - is_installed / read_provider / write_provider (CRUD)
      - activate_provider (set as active/enabled)
      - has_provider (duplicate detection)
    """

    name: str  # agent identifier, e.g. "claude-code"

    @abstractmethod
    def is_installed(self) -> bool:
        """Check if the agent is installed on this machine."""

    @abstractmethod
    def read_provider(self) -> dict | None:
        """Read current provider config from the agent's config files.

        Returns:
            dict with keys: base_url, api_key, model, protocol
            or None if no provider is configured.
        """

    @abstractmethod
    def write_provider(self, provider: dict) -> None:
        """Write provider config to the agent's config files.

        Args:
            provider: dict with keys: name, base_url, api_key, protocol, models
        """

    @abstractmethod
    def activate_provider(self, provider: dict, model: str | None = None) -> None:
        """Activate/enable the provider (and optionally select a model).

        After this call the agent should use this provider for requests.
        """

    def has_provider(self, provider: dict) -> bool:
        """Check if this provider is already configured with the same URL+key.

        Default implementation compares base_url and api_key with read_provider().
        Subclasses with multi-provider support should override to check all entries.
        """
        current = self.read_provider()
        if not current:
            return False
        return (
            current.get("base_url", "").rstrip("/") == provider.get("base_url", "").rstrip("/")
            and current.get("api_key") == provider.get("api_key")
        )

    @staticmethod
    def backup(path: Path) -> None:
        """Create a timestamped backup of a file."""
        if path.exists():
            ts = datetime.now().strftime("%Y%m%d%H%M%S")
            bak = path.with_suffix(f".bak.{ts}")
            shutil.copy2(path, bak)


def is_port_open(port: int, host: str = "127.0.0.1", timeout: float = 1.0) -> bool:
    """Check if a TCP port is open."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (ConnectionRefusedError, TimeoutError, OSError):
        return False


def yaml_get(text: str, section: str, key: str) -> str | None:
    """Simple YAML value getter for flat two-level structures.

    Only handles the common case of a top-level key with indented children.
    """
    in_section = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(f"{section}:"):
            in_section = True
            continue
        if in_section:
            if not line.startswith(" ") and not line.startswith("\t") and stripped:
                break
            if stripped.startswith(f"{key}:"):
                return stripped.split(":", 1)[1].strip().strip('"').strip("'")
    return None


def yaml_set(text: str, section: str, key: str, value: str) -> str:
    """Simple YAML value setter for flat two-level structures."""
    lines = text.splitlines()
    result: list[str] = []
    in_section = False
    found = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith(f"{section}:"):
            in_section = True
            result.append(line)
            continue
        if in_section:
            if not line.startswith(" ") and not line.startswith("\t") and stripped:
                in_section = False
                result.append(line)
                continue
            if stripped.startswith(f"{key}:"):
                indent = len(line) - len(line.lstrip())
                result.append(f"{' ' * indent}{key}: {value}")
                found = True
                continue
        result.append(line)

    if not found:
        for i, line in enumerate(result):
            if line.strip().startswith(f"{section}:"):
                result.insert(i + 1, f"  {key}: {value}")
                break

    return "\n".join(result) + "\n"
