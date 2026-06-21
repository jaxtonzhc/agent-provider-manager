"""Tests for agent adapters."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest


class TestClaudeCodeAdapter:
    def _get_adapter(self):
        from apm.agents.claude_code import ClaudeCodeAdapter
        return ClaudeCodeAdapter()

    def test_read_provider(self, mock_agent_config, tmp_path):
        adapter = self._get_adapter()
        with patch("apm.agents.claude_code.CLAUDE_CODE_CONFIG", mock_agent_config["claude_code"]):
            result = adapter.read_provider()

        assert result is not None
        assert result["api_key"] == "sk-claude-test"
        assert result["base_url"] == "https://api.anthropic.com"
        assert result["protocol"] == "anthropic"

    def test_write_provider(self, mock_agent_config, tmp_path):
        adapter = self._get_adapter()
        provider = {
            "name": "DeepSeek",
            "base_url": "https://api.deepseek.com/v1",
            "api_key": "sk-new-key",
            "protocol": "openai-compatible",
            "models": ["deepseek-chat"],
        }

        with patch("apm.agents.claude_code.CLAUDE_CODE_CONFIG", mock_agent_config["claude_code"]):
            adapter.write_provider(provider)

        with open(mock_agent_config["claude_code"]) as f:
            data = json.load(f)

        assert data["env"]["ANTHROPIC_AUTH_TOKEN"] == "sk-new-key"
        assert "/anthropic" in data["env"]["ANTHROPIC_BASE_URL"]

    def test_write_provider_anthropic_no_suffix(self, mock_agent_config, tmp_path):
        adapter = self._get_adapter()
        provider = {
            "name": "Anthropic",
            "base_url": "https://api.anthropic.com",
            "api_key": "sk-anthropic",
            "protocol": "anthropic",
            "models": ["claude-sonnet-4"],
        }

        with patch("apm.agents.claude_code.CLAUDE_CODE_CONFIG", mock_agent_config["claude_code"]):
            adapter.write_provider(provider)

        with open(mock_agent_config["claude_code"]) as f:
            data = json.load(f)

        assert "/anthropic" not in data["env"]["ANTHROPIC_BASE_URL"]


class TestCodexAdapter:
    def _get_adapter(self):
        from apm.agents.codex import CodexAdapter
        return CodexAdapter()

    def test_read_provider(self, mock_agent_config, tmp_path):
        adapter = self._get_adapter()
        with patch("apm.agents.codex.CODEX_AUTH", mock_agent_config["codex_auth"]), \
             patch("apm.agents.codex.CODEX_CONFIG", mock_agent_config["codex_config"]):
            result = adapter.read_provider()

        assert result is not None
        assert result["api_key"] == "sk-codex-test"
        assert result["protocol"] == "responses"

    def test_write_provider(self, mock_agent_config, tmp_path):
        adapter = self._get_adapter()
        provider = {
            "name": "DeepSeek",
            "base_url": "https://api.deepseek.com/v1",
            "api_key": "sk-new",
            "protocol": "openai-compatible",
            "models": ["deepseek-chat"],
        }

        with patch("apm.agents.codex.CODEX_AUTH", mock_agent_config["codex_auth"]), \
             patch("apm.agents.codex.CODEX_CONFIG", mock_agent_config["codex_config"]), \
             patch("apm.agents.codex.is_port_open", return_value=False):
            adapter.write_provider(provider)

        auth = json.loads(mock_agent_config["codex_auth"].read_text())
        assert auth["OPENAI_API_KEY"] == "sk-new"

        config = mock_agent_config["codex_config"].read_text()
        assert "chat_completions" in config


class TestWorkBuddyAdapter:
    def _get_adapter(self):
        from apm.agents.workbuddy import WorkBuddyAdapter
        return WorkBuddyAdapter()

    def test_read_provider(self, mock_agent_config, tmp_path):
        adapter = self._get_adapter()
        with patch("apm.agents.workbuddy.WORKBUDDY_CONFIG", mock_agent_config["workbuddy_config"]):
            result = adapter.read_provider()

        assert result is not None
        assert result["api_key"] == "sk-workbuddy-test"
        assert result["base_url"] == "https://api.test.com/v1"

    def test_write_provider(self, mock_agent_config, tmp_path):
        adapter = self._get_adapter()
        provider = {
            "name": "DeepSeek",
            "base_url": "https://api.deepseek.com/v1",
            "api_key": "sk-new",
            "protocol": "openai-compatible",
            "models": ["deepseek-chat", "deepseek-reasoner"],
        }

        with patch("apm.agents.workbuddy.WORKBUDDY_CONFIG", mock_agent_config["workbuddy_config"]):
            adapter.write_provider(provider)

        models = json.loads(mock_agent_config["workbuddy_config"].read_text())
        assert len(models) == 2
        assert models[0]["id"] == "deepseek-chat"
        assert models[0]["apiKey"] == "sk-new"


class TestHermesAdapter:
    def _get_adapter(self):
        from apm.agents.hermes import HermesAdapter
        return HermesAdapter()

    def test_read_provider(self, mock_agent_config, tmp_path):
        adapter = self._get_adapter()
        with patch("apm.agents.hermes.HERMES_CONFIG", mock_agent_config["hermes_config"]):
            result = adapter.read_provider()

        assert result is not None
        assert result["api_key"] == "sk-hermes-test"
        assert result["base_url"] == "https://api.test.com/v1"


class TestOpenClawAdapter:
    def _get_adapter(self):
        from apm.agents.openclaw import OpenClawAdapter
        return OpenClawAdapter()

    def test_read_provider(self, mock_agent_config, tmp_path):
        adapter = self._get_adapter()
        with patch("apm.agents.openclaw.OPENCLAW_CONFIG", mock_agent_config["openclaw_config"]):
            result = adapter.read_provider()

        assert result is not None
        assert result["api_key"] == "sk-openclaw-test"
        assert result["base_url"] == "https://api.test.com/v1"


class TestZCodeAdapter:
    def _get_adapter(self):
        from apm.agents.zcode import ZCodeAdapter
        return ZCodeAdapter()

    def test_read_provider(self, mock_agent_config, tmp_path):
        adapter = self._get_adapter()
        with patch("apm.agents.zcode.ZCODE_CONFIG", mock_agent_config["zcode_config"]):
            result = adapter.read_provider()

        assert result is not None
        assert result["api_key"] == "sk-zcode-test"
        assert result["base_url"] == "https://api.test.com/v1"
