"""Tests for provider management."""

from __future__ import annotations

import json
import os
import tempfile
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
    with patch("apm.config.APM_DIR", tmp_apm_dir), \
         patch("apm.config.PROVIDERS_FILE", tmp_apm_dir / "providers.json"), \
         patch("apm.providers.APM_DIR", tmp_apm_dir), \
         patch("apm.providers.PROVIDERS_FILE", tmp_apm_dir / "providers.json"):
        yield tmp_apm_dir


def test_add_provider(mock_config):
    from apm.providers import add, get

    slug = add("Test Provider", "https://api.test.com/v1", "sk-test123",
               models=["model-a", "model-b"])
    assert slug == "test-provider"

    p = get("test-provider")
    assert p is not None
    assert p["name"] == "Test Provider"
    assert p["base_url"] == "https://api.test.com/v1"
    assert p["api_key"] == "sk-test123"
    assert p["models"] == ["model-a", "model-b"]


def test_remove_provider(mock_config):
    from apm.providers import add, get, remove

    add("Test", "https://api.test.com/v1", "sk-test")
    remove("test")
    assert get("test") is None


def test_list_providers(mock_config):
    from apm.providers import add, list_all

    add("Alpha", "https://alpha.com/v1", "sk-a")
    add("Beta", "https://beta.com/v1", "sk-b")

    providers = list_all()
    assert len(providers) == 2
    names = [p["name"] for p in providers]
    assert "Alpha" in names
    assert "Beta" in names


def test_set_active(mock_config):
    from apm.providers import add, get_active, set_active

    add("Alpha", "https://alpha.com/v1", "sk-a")
    add("Beta", "https://beta.com/v1", "sk-b")

    set_active("beta")
    active = get_active()
    assert active is not None
    assert active["name"] == "Beta"


def test_get_nonexistent(mock_config):
    from apm.providers import get

    assert get("nonexistent") is None


def test_remove_nonexistent_raises(mock_config):
    from apm.providers import remove

    with pytest.raises(ValueError, match="not found"):
        remove("nonexistent")


def test_file_permissions(mock_config):
    from apm.providers import add

    add("Test", "https://api.test.com/v1", "sk-test")

    providers_file = mock_config / "providers.json"
    assert providers_file.exists()
    mode = oct(os.stat(providers_file).st_mode)[-3:]
    assert mode == "600"
