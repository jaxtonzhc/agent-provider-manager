"""Agent adapter registry.

Supported agents (deep integration only):
  - claude-code: Claude Code CLI
  - opencode: OpenCode CLI
  - zcode: ZCode IDE
  - hermes: Hermes Agent
  - pi: Pi CLI
  - omp: Oh-My-Pi (Pi fork)
"""

from __future__ import annotations

from apm.agents.base import AgentAdapter
from apm.agents.claude_code import ClaudeCodeAdapter
from apm.agents.hermes import HermesAdapter
from apm.agents.opencode import OpenCodeAdapter
from apm.agents.pi import OmpAdapter, PiAdapter
from apm.agents.zcode import ZCodeAdapter

ADAPTERS: dict[str, AgentAdapter] = {
    "claude-code": ClaudeCodeAdapter(),
    "opencode": OpenCodeAdapter(),
    "zcode": ZCodeAdapter(),
    "hermes": HermesAdapter(),
    "pi": PiAdapter(),
    "omp": OmpAdapter(),
}


def get_adapter(name: str) -> AgentAdapter | None:
    """Get an adapter by agent name."""
    return ADAPTERS.get(name)


def get_all_adapters() -> dict[str, AgentAdapter]:
    """Get all registered adapters."""
    return ADAPTERS
