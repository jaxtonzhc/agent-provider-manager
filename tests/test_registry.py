"""Tests for registry module."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from apm.registry import (
    _load_builtin,
    _load_cache,
    _save_cache,
    get_agent,
    get_provider,
    list_agents,
    list_providers,
    load_registry,
    resolve_provider,
    CACHE_FILE,
)


@pytest.fixture
def mock_cache_dir(tmp_path):
    """Mock cache directory."""
    cache_file = tmp_path / "registry-cache.json"
    with patch("apm.registry.CACHE_FILE", cache_file):
        yield cache_file


class TestLoadBuiltin:
    def test_load_builtin_has_agents(self):
        registry = _load_builtin()
        assert "agents" in registry
        assert len(registry["agents"]) > 0

    def test_load_builtin_has_providers(self):
        registry = _load_builtin()
        assert "providers" in registry
        assert len(registry["providers"]) > 0

    def test_load_builtin_has_version(self):
        registry = _load_builtin()
        assert "version" in registry
        assert isinstance(registry["version"], int)

    def test_builtin_agents_have_required_fields(self):
        registry = _load_builtin()
        for slug, agent in registry["agents"].items():
            assert "name" in agent, f"{slug} missing 'name'"
            assert "config_paths" in agent, f"{slug} missing 'config_paths'"

    def test_builtin_providers_have_variants(self):
        registry = _load_builtin()
        for slug, provider in registry["providers"].items():
            assert "name" in provider, f"{slug} missing 'name'"
            assert "variants" in provider, f"{slug} missing 'variants'"
            assert len(provider["variants"]) > 0, f"{slug} has no variants"
            for vname, variant in provider["variants"].items():
                assert "base_url" in variant, f"{slug}.{vname} missing 'base_url'"


class TestCache:
    def test_save_and_load_cache(self, mock_cache_dir):
        data = {"version": 1, "agents": {"test": {"name": "Test"}}, "providers": {}}
        _save_cache(data)

        loaded = _load_cache()
        assert loaded is not None
        assert loaded["version"] == 1
        assert loaded["agents"]["test"]["name"] == "Test"
        assert "_cached_at" in loaded

    def test_load_cache_expired(self, mock_cache_dir):
        import time
        data = {"version": 1, "_cached_at": time.time() - 100000}
        mock_cache_dir.write_text(json.dumps(data))

        loaded = _load_cache()
        assert loaded is None  # expired

    def test_load_cache_missing(self, mock_cache_dir):
        loaded = _load_cache()
        assert loaded is None

    def test_load_cache_corrupted(self, mock_cache_dir):
        mock_cache_dir.write_text("not valid json{{{")
        loaded = _load_cache()
        assert loaded is None


class TestGetAgent:
    def test_get_known_agent(self):
        agent = get_agent("claude-code")
        assert agent is not None
        assert agent["name"] == "Claude Code"

    def test_get_unknown_agent(self):
        agent = get_agent("nonexistent-agent")
        assert agent is None


class TestGetProvider:
    def test_get_known_provider(self):
        provider = get_provider("deepseek")
        assert provider is not None
        assert provider["name"] == "DeepSeek"

    def test_get_unknown_provider(self):
        provider = get_provider("nonexistent-provider")
        assert provider is None


class TestResolveProvider:
    def test_resolve_with_default_variant(self):
        result = resolve_provider("deepseek", "sk-test")
        assert result is not None
        assert result["api_key"] == "sk-test"
        assert result["base_url"] == "https://api.deepseek.com/v1"
        assert "deepseek-chat" in result["models"]

    def test_resolve_with_specific_variant(self):
        result = resolve_provider("glm", "sk-test", variant="token-plan-cn")
        assert result is not None
        assert "token-plan-cn" in result["base_url"]

    def test_resolve_unknown_returns_none(self):
        result = resolve_provider("nonexistent", "sk-test")
        assert result is None

    def test_resolve_extracts_model_ids(self):
        result = resolve_provider("openai", "sk-test")
        assert result is not None
        for model in result["models"]:
            assert isinstance(model, str)

    def test_resolve_includes_variants(self):
        result = resolve_provider("xiaomimimo", "sk-test")
        assert result is not None
        assert "variants" in result
        assert len(result["variants"]) > 1


class TestListAgents:
    def test_returns_dict(self):
        agents = list_agents()
        assert isinstance(agents, dict)
        assert len(agents) > 0

    def test_agents_have_name(self):
        agents = list_agents()
        for slug, info in agents.items():
            assert "name" in info


class TestListProviders:
    def test_returns_dict(self):
        providers = list_providers()
        assert isinstance(providers, dict)
        assert len(providers) > 0

    def test_providers_have_variants(self):
        providers = list_providers()
        for slug, info in providers.items():
            assert "variants" in info
