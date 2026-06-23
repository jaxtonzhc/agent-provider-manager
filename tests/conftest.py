"""Shared test fixtures."""

from __future__ import annotations

import json
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
    with (
        patch("apm.config.APM_DIR", tmp_apm_dir),
        patch("apm.config.PROVIDERS_FILE", providers_file),
        patch("apm.config.SYNC_STATE_FILE", sync_state_file),
        patch("apm.providers.APM_DIR", tmp_apm_dir),
        patch("apm.providers.PROVIDERS_FILE", providers_file),
        patch("apm.sync.SYNC_STATE_FILE", sync_state_file),
    ):
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
    claude_settings.write_text(
        json.dumps(
            {
                "env": {
                    "ANTHROPIC_AUTH_TOKEN": "sk-claude-test",
                    "ANTHROPIC_BASE_URL": "https://api.anthropic.com",
                    "ANTHROPIC_MODEL": "claude-sonnet-4",
                }
            }
        )
    )
    configs["claude_code"] = claude_settings


    # Hermes (custom_providers format + .env)
    hermes_dir = tmp_path / ".hermes"
    hermes_dir.mkdir()
    hermes_config = hermes_dir / "config.yaml"
    hermes_yaml = (
        "model:\n"
        "  default: test-model\n"
        "  provider: testprov\n"
        "custom_providers:\n"
        "- name: testprov\n"
        "  base_url: https://api.test.com/v1\n"
        "  api_key: sk-hermes-test\n"
        "  api_mode: chat_completions\n"
        "  model: test-model\n"
        "  models:\n"
        "    test-model:\n"
        "      context_length: 128000\n"
        "      name: Test Model\n"
    )
    hermes_config.write_text(hermes_yaml)
    hermes_env = hermes_dir / ".env"
    hermes_env.write_text("TESTPROV_API_KEY=sk-hermes-test\nTESTPROV_BASE_URL=https://api.test.com/v1\n")
    configs["hermes_config"] = hermes_config
    configs["hermes_env"] = hermes_env

    # OpenCode
    opencode_dir = tmp_path / ".config" / "opencode"
    opencode_dir.mkdir(parents=True)
    opencode_config = opencode_dir / "opencode.json"
    opencode_config.write_text(json.dumps({
        "$schema": "https://opencode.ai/config.json",
        "model": "testprov/test-model",
        "provider": {
            "testprov": {
                "npm": "@ai-sdk/openai-compatible",
                "name": "Test Provider",
                "options": {
                    "baseURL": "https://api.test.com/v1",
                    "apiKey": "sk-opencode-test",
                },
                "models": {"test-model": {"name": "Test Model"}},
            }
        },
    }))
    configs["opencode_config"] = opencode_config


    # ZCode
    zcode_dir = tmp_path / ".zcode" / "v2"
    zcode_dir.mkdir(parents=True)
    zcode_config = zcode_dir / "config.json"
    zcode_config.write_text(
        json.dumps(
            {
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
            }
        )
    )
    configs["zcode_config"] = zcode_config


    # Pi
    pi_dir = tmp_path / ".pi" / "agent"
    pi_dir.mkdir(parents=True)
    pi_config = pi_dir / "models.json"
    pi_config.write_text(json.dumps({
        "providers": {
            "test-prov": {
                "baseUrl": "https://api.test.com/v1",
                "api": "openai-completions",
                "apiKey": "sk-pi-test",
                "models": [],
            }
        }
    }))
    configs["pi_config"] = pi_config
    pi_settings = pi_dir / "settings.json"
    pi_settings.write_text(json.dumps({
        "defaultProvider": "test-prov", "defaultModel": "test-model"
    }))
    configs["pi_settings"] = pi_settings

    # OMP
    omp_dir = tmp_path / ".omp" / "agent"
    omp_dir.mkdir(parents=True)
    omp_config = omp_dir / "models.json"
    omp_config.write_text(json.dumps({
        "providers": {
            "test-prov": {
                "baseUrl": "https://api.test.com/v1",
                "api": "openai-completions",
                "apiKey": "sk-omp-test",
                "models": [],
            }
        }
    }))
    configs["omp_config"] = omp_config
    omp_settings = omp_dir / "settings.json"
    omp_settings.write_text(json.dumps({
        "defaultProvider": "test-prov", "defaultModel": "test-model"
    }))
    configs["omp_settings"] = omp_settings

    return configs
