"""Tests for agent detection."""

from __future__ import annotations

from apm.detect import detect_agent, detect_all, get_installed_agents


def test_detect_all_returns_all_agents():
    results = detect_all()
    names = [r["name"] for r in results]
    assert "claude-code" in names
    assert "codex" in names
    assert "cursor" in names
    assert "hermes" in names
    assert "openclaw" in names
    assert "zcode" in names
    assert "workbuddy" in names
    assert "aider" in names
    assert "pi" in names
    assert "omp" in names
    assert len(results) == 10


def test_detect_agent_returns_dict():
    result = detect_agent("claude-code")
    assert "name" in result
    assert "installed" in result
    assert result["name"] == "claude-code"


def test_detect_unknown_agent():
    result = detect_agent("unknown-agent")
    assert result["name"] == "unknown-agent"
    assert result["installed"] is False


def test_get_installed_agents_returns_list():
    result = get_installed_agents()
    assert isinstance(result, list)
