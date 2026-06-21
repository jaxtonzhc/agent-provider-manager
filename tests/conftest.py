"""Shared test fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def tmp_apm_dir(tmp_path):
    """Create a temporary apm directory."""
    apm_dir = tmp_path / ".apm"
    apm_dir.mkdir()
    return apm_dir


@pytest.fixture
def mock_config(tmp_apm_dir):
    """Mock config paths to use temp directory."""
    providers_file = tmp_apm_dir / "providers.json"
    sync_state_file = tmp_apm_dir / "sync-state.json"
    with patch("apm.config.APM_DIR", tmp_apm_dir), \
         patch("apm.config.PROVIDERS_FILE", providers_file), \
         patch("apm.config.SYNC_STATE_FILE", sync_state_file), \
         patch("apm.providers.APM_DIR", tmp_apm_dir), \
         patch("apm.providers.PROVIDERS_FILE", providers_file), \
         patch("apm.sync.APM_DIR", tmp_apm_dir), \
         patch("apm.sync.SYNC_STATE_FILE", sync_state_file):
        yield tmp_apm_dir


@pytest.fixture
def sample_provider():
    """Return a sample provider dict."""
    return {
        "name": "Test Provider",
        "base_url": "https://api.test.com/v1",
        "api_key": "sk-test-key-12345678",
        "protocol": "openai-compatible",
        "models": ["model-a", "model-b"],
    }


@pytest.fixture
def mock_agent_config(tmp_path):
    """Create mock agent config files in a temp directory."""
    configs = {}

    # Claude Code
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    claude_settings = claude_dir / "settings.json"
    claude_settings.write_text(json.dumps({
        "env": {
            "ANTHROPIC_AUTH_TOKEN": "sk-claude-test",
            "ANTHROPIC_BASE_URL": "https://api.anthropic.com",
            "ANTHROPIC_MODEL": "claude-sonnet-4",
        }
    }))
    configs["claude_code"] = claude_settings

    # Codex
    codex_dir = tmp_path / ".codex"
    codex_dir.mkdir()
    codex_config = codex_dir / "config.toml"
    codex_config.write_text('model_provider = "custom"\n\n[model_providers.custom]\nwire_api = "responses"\n')
    codex_auth = codex_dir / "auth.json"
    codex_auth.write_text(json.dumps({"OPENAI_API_KEY": "sk-codex-test"}))
    configs["codex_config"] = codex_config
    configs["codex_auth"] = codex_auth

    # Hermes
    hermes_dir = tmp_path / ".hermes"
    hermes_dir.mkdir()
    hermes_config = hermes_dir / "config.yaml"
    hermes_config.write_text("model:\n  default: test-model\n  provider: test\n  base_url: https://api.test.com/v1\n  api_key: sk-hermes-test\n")
    hermes_env = hermes_dir / ".env"
    hermes_env.write_text("TEST_API_KEY=sk-hermes-test\n")
    configs["hermes_config"] = hermes_config
    configs["hermes_env"] = hermes_env

    # OpenClaw
    openclaw_dir = tmp_path / ".openclaw"
    openclaw_dir.mkdir()
    openclaw_config = openclaw_dir / "openclaw.json"
    openclaw_config.write_text(json.dumps({
        "models": {
            "mode": "merge",
            "providers": {
                "test-provider": {
                    "baseUrl": "https://api.test.com/v1",
                    "api": "openai-completions",
                    "apiKey": "sk-openclaw-test",
                    "models": [{"id": "test-model", "name": "Test"}],
                }
            }
        }
    }))
    configs["openclaw_config"] = openclaw_config

    # ZCode
    zcode_dir = tmp_path / ".zcode" / "v2"
    zcode_dir.mkdir(parents=True)
    zcode_config = zcode_dir / "config.json"
    zcode_config.write_text(json.dumps({
        "provider": {
            "test-uuid": {
                "name": "Test",
                "kind": "openai-compatible",
                "options": {
                    "apiKey": "sk-zcode-test",
                    "baseURL": "https://api.test.com/v1",
                    "apiKeyRequired": True,
                },
                "enabled": True,
                "models": {},
            }
        }
    }))
    configs["zcode_config"] = zcode_config

    # WorkBuddy
    workbuddy_dir = tmp_path / ".workbuddy"
    workbuddy_dir.mkdir()
    workbuddy_config = workbuddy_dir / "models.json"
    workbuddy_config.write_text(json.dumps([{
        "id": "test-model",
        "name": "Test Model",
        "vendor": "Custom",
        "url": "https://api.test.com/v1",
        "apiKey": "sk-workbuddy-test",
        "supportsToolCall": True,
        "supportsImages": False,
        "supportsReasoning": True,
        "useCustomProtocol": False,
        "reasoning": {"supportedEfforts": ["medium", "high"]},
    }]))
    configs["workbuddy_config"] = workbuddy_config

    return configs
