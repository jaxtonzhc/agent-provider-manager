"""Tests for provider management."""

from __future__ import annotations

import os
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
    with (
        patch("apm.config.APM_DIR", tmp_apm_dir),
        patch("apm.config.PROVIDERS_FILE", tmp_apm_dir / "providers.json"),
        patch("apm.providers.APM_DIR", tmp_apm_dir),
        patch("apm.providers.PROVIDERS_FILE", tmp_apm_dir / "providers.json"),
    ):
        yield tmp_apm_dir


def test_add_provider(mock_config):
    from apm.providers import add, get

    slug = add(
        "Test Provider", "https://api.test.com/v1", "sk-test123", models=["model-a", "model-b"]
    )
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


class TestSortModelsByVersion:
    def test_basic_version_sorting(self):
        from apm.providers import sort_models_by_version
        models = ["deepseek-v2", "deepseek-v4-flash", "deepseek-v3"]
        result = sort_models_by_version(models)
        assert result[0] == "deepseek-v4-flash"
        assert result[-1] == "deepseek-v2"

    def test_float_versions(self):
        from apm.providers import sort_models_by_version
        models = ["mimo-v2.5", "mimo-v1.0", "mimo-v2.5-pro"]
        result = sort_models_by_version(models)
        assert result[0] in ("mimo-v2.5", "mimo-v2.5-pro")
        assert result[-1] == "mimo-v1.0"

    def test_no_version_goes_last(self):
        from apm.providers import sort_models_by_version
        models = ["deepseek-chat", "deepseek-v4-flash", "deepseek-reasoner"]
        result = sort_models_by_version(models)
        assert result[0] == "deepseek-v4-flash"

    def test_empty_list(self):
        from apm.providers import sort_models_by_version
        assert sort_models_by_version([]) == []

    def test_mixed_versions(self):
        from apm.providers import sort_models_by_version
        models = ["gpt-4o", "gpt-3.5-turbo", "gpt-5", "claude-sonnet-4.5"]
        result = sort_models_by_version(models)
        assert result[0] == "gpt-5"


class TestFetchModels:
    def test_fetch_success(self):
        import json
        from unittest.mock import MagicMock
        from unittest.mock import patch as _patch

        from apm.providers import fetch_models

        body = json.dumps({
            "data": [
                {"id": "deepseek-v2"},
                {"id": "deepseek-v4-flash"},
                {"id": "deepseek-v3"},
            ]
        }).encode()
        mock_resp = MagicMock()
        mock_resp.read.return_value = body
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with _patch("urllib.request.urlopen", return_value=mock_resp):
            result = fetch_models("https://api.example.com/v1", "sk-test")

        assert len(result) == 3
        assert result[0] == "deepseek-v4-flash"

    def test_fetch_failure_returns_empty(self):
        from unittest.mock import patch as _patch
        from urllib.error import URLError

        from apm.providers import fetch_models

        with _patch("urllib.request.urlopen", side_effect=URLError("fail")):
            result = fetch_models("https://bad.url/v1", "sk-test")

        assert result == []

    def test_fetch_alt_format(self):
        """Some providers return {models: [...]} instead of {data: [...]}."""
        import json
        from unittest.mock import MagicMock
        from unittest.mock import patch as _patch

        from apm.providers import fetch_models

        body = json.dumps({
            "models": [{"id": "model-a"}, {"id": "model-b"}]
        }).encode()
        mock_resp = MagicMock()
        mock_resp.read.return_value = body
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with _patch("urllib.request.urlopen", return_value=mock_resp):
            result = fetch_models("https://api.example.com/v1", "sk-test")

        assert "model-a" in result
        assert "model-b" in result
