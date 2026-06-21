"""Agent adapter registry."""

from __future__ import annotations

from apm.agents.base import AgentAdapter
from apm.agents.claude_code import ClaudeCodeAdapter
from apm.agents.codex import CodexAdapter
from apm.agents.hermes import HermesAdapter
from apm.agents.openclaw import OpenClawAdapter
from apm.agents.workbuddy import WorkBuddyAdapter
from apm.agents.zcode import ZCodeAdapter

ADAPTERS: dict[str, AgentAdapter] = {
    "claude-code": ClaudeCodeAdapter(),
    "codex": CodexAdapter(),
    "hermes": HermesAdapter(),
    "openclaw": OpenClawAdapter(),
    "zcode": ZCodeAdapter(),
    "workbuddy": WorkBuddyAdapter(),
}


def get_adapter(name: str) -> AgentAdapter | None:
    """Get an adapter by agent name."""
    return ADAPTERS.get(name)


def get_all_adapters() -> dict[str, AgentAdapter]:
    """Get all registered adapters."""
    return ADAPTERS
