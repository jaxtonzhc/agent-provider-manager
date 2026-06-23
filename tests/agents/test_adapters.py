"""Tests for agent adapters (supported agents only)."""

from __future__ import annotations

import json
from unittest.mock import patch


class TestClaudeCodeAdapter:
    def _get_adapter(self):
        from apm.agents.claude_code import ClaudeCodeAdapter
        return ClaudeCodeAdapter()

    def test_read_provider(self, mock_agent_config):
        adapter = self._get_adapter()
        with patch("apm.agents.claude_code.CLAUDE_CODE_CONFIG", mock_agent_config["claude_code"]):
            result = adapter.read_provider()

        assert result is not None
        assert result["api_key"] == "sk-claude-test"
        assert result["base_url"] == "https://api.anthropic.com"
        assert result["protocol"] == "anthropic"

    def test_write_provider(self, mock_agent_config):
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

    def test_has_provider(self, mock_agent_config):
        adapter = self._get_adapter()
        with patch("apm.agents.claude_code.CLAUDE_CODE_CONFIG", mock_agent_config["claude_code"]):
            assert adapter.has_provider({
                "base_url": "https://api.anthropic.com",
                "api_key": "sk-claude-test",
                "protocol": "anthropic",
            })
            assert not adapter.has_provider({
                "base_url": "https://api.other.com",
                "api_key": "sk-other",
            })

    def test_activate_provider(self, mock_agent_config):
        adapter = self._get_adapter()
        provider = {
            "name": "DeepSeek",
            "base_url": "https://api.deepseek.com/v1",
            "api_key": "sk-new",
            "protocol": "openai-compatible",
            "models": ["deepseek-chat"],
        }
        with patch("apm.agents.claude_code.CLAUDE_CODE_CONFIG", mock_agent_config["claude_code"]):
            adapter.activate_provider(provider, model="deepseek-v4-flash")

        data = json.loads(mock_agent_config["claude_code"].read_text())
        assert data["env"]["ANTHROPIC_MODEL"] == "deepseek-v4-flash"


class TestOpenCodeAdapter:
    def _get_adapter(self):
        from apm.agents.opencode import OpenCodeAdapter
        return OpenCodeAdapter()

    def test_read_provider(self, mock_agent_config):
        adapter = self._get_adapter()
        with patch("apm.agents.opencode.OPENCODE_CONFIG", mock_agent_config["opencode_config"]):
            result = adapter.read_provider()

        assert result is not None
        assert result["api_key"] == "sk-opencode-test"
        assert result["base_url"] == "https://api.test.com/v1"
        assert result["model"] == "test-model"

    def test_write_provider(self, mock_agent_config):
        adapter = self._get_adapter()
        provider = {
            "name": "DeepSeek",
            "base_url": "https://api.deepseek.com/v1",
            "api_key": "sk-new",
            "protocol": "openai-compatible",
            "models": ["deepseek-chat", "deepseek-reasoner"],
            "model_meta": {"deepseek-chat": {"name": "DeepSeek Chat", "context": 65536}},
        }
        with patch("apm.agents.opencode.OPENCODE_CONFIG", mock_agent_config["opencode_config"]):
            adapter.write_provider(provider)

        data = json.loads(mock_agent_config["opencode_config"].read_text())
        assert "deepseek" in data["provider"]
        prov = data["provider"]["deepseek"]
        assert prov["options"]["apiKey"] == "sk-new"
        assert prov["options"]["baseURL"] == "https://api.deepseek.com/v1"
        assert "deepseek-chat" in prov["models"]

    def test_activate_provider(self, mock_agent_config):
        adapter = self._get_adapter()
        provider = {"name": "Test Provider", "models": ["test-model"]}
        with patch("apm.agents.opencode.OPENCODE_CONFIG", mock_agent_config["opencode_config"]):
            adapter.activate_provider(provider, model="new-model")

        data = json.loads(mock_agent_config["opencode_config"].read_text())
        assert data["model"] == "test-provider/new-model"

    def test_has_provider(self, mock_agent_config):
        adapter = self._get_adapter()
        with patch("apm.agents.opencode.OPENCODE_CONFIG", mock_agent_config["opencode_config"]):
            assert adapter.has_provider({
                "base_url": "https://api.test.com/v1",
                "api_key": "sk-opencode-test",
            })
            assert not adapter.has_provider({
                "base_url": "https://api.other.com/v1",
                "api_key": "sk-other",
            })


class TestZCodeAdapter:
    def _get_adapter(self):
        from apm.agents.zcode import ZCodeAdapter
        return ZCodeAdapter()

    def test_read_provider(self, mock_agent_config):
        adapter = self._get_adapter()
        with patch("apm.agents.zcode.ZCODE_CONFIG", mock_agent_config["zcode_config"]):
            result = adapter.read_provider()

        assert result is not None
        assert result["api_key"] == "sk-zcode-test"
        assert result["base_url"] == "https://api.test.com/v1"

    def test_write_provider(self, mock_agent_config):
        adapter = self._get_adapter()
        provider = {
            "name": "DeepSeek",
            "base_url": "https://api.deepseek.com/v1",
            "api_key": "sk-new",
            "protocol": "openai-compatible",
            "models": ["deepseek-chat"],
        }
        with patch("apm.agents.zcode.ZCODE_CONFIG", mock_agent_config["zcode_config"]):
            adapter.write_provider(provider)

        data = json.loads(mock_agent_config["zcode_config"].read_text())
        provs = {k: v for k, v in data["provider"].items() if v.get("name") == "DeepSeek"}
        assert len(provs) == 1
        prov = next(iter(provs.values()))
        assert prov["options"]["apiKey"] == "sk-new"
        assert prov["enabled"] is True

    def test_activate_provider(self, mock_agent_config):
        adapter = self._get_adapter()
        provider = {
            "name": "DeepSeek", "base_url": "https://api.deepseek.com/v1",
            "api_key": "sk-new", "models": [],
        }
        # Write first, then activate
        with patch("apm.agents.zcode.ZCODE_CONFIG", mock_agent_config["zcode_config"]):
            adapter.write_provider(provider)
            adapter.activate_provider(provider)

        data = json.loads(mock_agent_config["zcode_config"].read_text())
        for k, v in data["provider"].items():
            if v.get("name") == "DeepSeek":
                assert v["enabled"] is True
            elif k != "test-uuid":
                assert v["enabled"] is False

    def test_has_provider(self, mock_agent_config):
        adapter = self._get_adapter()
        with patch("apm.agents.zcode.ZCODE_CONFIG", mock_agent_config["zcode_config"]):
            assert adapter.has_provider({
                "base_url": "https://api.test.com/v1",
                "api_key": "sk-zcode-test",
            })
            assert not adapter.has_provider({
                "base_url": "https://api.other.com",
                "api_key": "sk-other",
            })


class TestHermesAdapter:
    def _get_adapter(self):
        from apm.agents.hermes import HermesAdapter
        return HermesAdapter()

    def test_read_provider(self, mock_agent_config):
        adapter = self._get_adapter()
        with patch("apm.agents.hermes.HERMES_CONFIG", mock_agent_config["hermes_config"]):
            result = adapter.read_provider()

        assert result is not None
        assert result["api_key"] == "sk-hermes-test"
        assert result["base_url"] == "https://api.test.com/v1"
        assert result["model"] == "test-model"

    def test_has_provider(self, mock_agent_config):
        adapter = self._get_adapter()
        with patch("apm.agents.hermes.HERMES_CONFIG", mock_agent_config["hermes_config"]):
            assert adapter.has_provider({
                "base_url": "https://api.test.com/v1",
                "api_key": "sk-hermes-test",
            })
            assert not adapter.has_provider({
                "base_url": "https://api.other.com",
                "api_key": "sk-other",
            })

    def test_activate_provider(self, mock_agent_config):
        adapter = self._get_adapter()
        provider = {"name": "NewProv", "models": ["new-model"]}
        with patch("apm.agents.hermes.HERMES_CONFIG", mock_agent_config["hermes_config"]):
            adapter.activate_provider(provider, model="new-model")

        text = mock_agent_config["hermes_config"].read_text()
        assert "default: new-model" in text
        assert "provider: newprov" in text


class TestPiAdapter:
    def _get_adapter(self):
        from apm.agents.pi import PiAdapter
        return PiAdapter()

    def test_read_provider(self, mock_agent_config):
        adapter = self._get_adapter()
        with patch("apm.agents.pi.PI_CONFIG", mock_agent_config["pi_config"]):
            result = adapter.read_provider()

        assert result is not None
        assert result["api_key"] == "sk-pi-test"
        assert result["base_url"] == "https://api.test.com/v1"

    def test_write_provider(self, mock_agent_config):
        adapter = self._get_adapter()
        provider = {
            "name": "DeepSeek",
            "base_url": "https://api.deepseek.com/v1",
            "api_key": "sk-new",
            "protocol": "openai-compatible",
            "models": ["deepseek-chat"],
        }
        with patch("apm.agents.pi.PI_CONFIG", mock_agent_config["pi_config"]):
            adapter.write_provider(provider)

        data = json.loads(mock_agent_config["pi_config"].read_text())
        prov = data["providers"]["deepseek"]
        assert prov["apiKey"] == "sk-new"
        assert prov["baseUrl"] == "https://api.deepseek.com/v1"
        assert len(prov["models"]) == 1

    def test_activate_provider(self, mock_agent_config):
        adapter = self._get_adapter()
        provider = {
            "name": "DeepSeek", "base_url": "https://api.deepseek.com/v1",
            "api_key": "sk-new", "models": ["deepseek-chat"],
        }
        with patch("apm.agents.pi.PI_CONFIG", mock_agent_config["pi_config"]), \
             patch("apm.agents.pi.PI_SETTINGS", mock_agent_config["pi_settings"]):
            adapter.write_provider(provider)
            adapter.activate_provider(provider)

        settings = json.loads(mock_agent_config["pi_settings"].read_text())
        assert settings["defaultProvider"] == "deepseek"
        assert settings["defaultModel"] == "deepseek-chat"

    def test_has_provider(self, mock_agent_config):
        adapter = self._get_adapter()
        with patch("apm.agents.pi.PI_CONFIG", mock_agent_config["pi_config"]):
            assert adapter.has_provider({
                "base_url": "https://api.test.com/v1",
                "api_key": "sk-pi-test",
            })


class TestOmpAdapter:
    def _get_adapter(self):
        from apm.agents.pi import OmpAdapter
        return OmpAdapter()

    def test_read_provider(self, mock_agent_config):
        adapter = self._get_adapter()
        with patch("apm.agents.pi.OMP_CONFIG", mock_agent_config["omp_config"]):
            result = adapter.read_provider()

        assert result is not None
        assert result["api_key"] == "sk-omp-test"
        assert result["base_url"] == "https://api.test.com/v1"

    def test_write_provider(self, mock_agent_config):
        adapter = self._get_adapter()
        provider = {
            "name": "DeepSeek",
            "base_url": "https://api.deepseek.com/v1",
            "api_key": "sk-new",
            "protocol": "openai-compatible",
            "models": ["deepseek-chat"],
        }
        with patch("apm.agents.pi.OMP_CONFIG", mock_agent_config["omp_config"]):
            adapter.write_provider(provider)

        data = json.loads(mock_agent_config["omp_config"].read_text())
        prov = data["providers"]["deepseek"]
        assert prov["apiKey"] == "sk-new"
