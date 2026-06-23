"""Tests for agent registry."""

from __future__ import annotations

from apm.agents.registry import ADAPTERS, get_adapter, get_all_adapters


def test_all_adapters_registered():
    adapters = get_all_adapters()
    assert len(adapters) == 6
    assert "claude-code" in adapters
    assert "opencode" in adapters
    assert "zcode" in adapters
    assert "hermes" in adapters
    assert "pi" in adapters
    assert "omp" in adapters


def test_get_adapter_by_name():
    adapter = get_adapter("claude-code")
    assert adapter is not None
    assert adapter.name == "claude-code"


def test_get_adapter_unknown():
    adapter = get_adapter("unknown")
    assert adapter is None


def test_all_adapters_have_required_methods():
    for name, adapter in ADAPTERS.items():
        assert hasattr(adapter, "name"), f"{name} missing name"
        assert hasattr(adapter, "is_installed"), f"{name} missing is_installed"
        assert hasattr(adapter, "read_provider"), f"{name} missing read_provider"
        assert hasattr(adapter, "write_provider"), f"{name} missing write_provider"
        assert callable(adapter.is_installed), f"{name}.is_installed not callable"
        assert callable(adapter.read_provider), f"{name}.read_provider not callable"
        assert callable(adapter.write_provider), f"{name}.write_provider not callable"
