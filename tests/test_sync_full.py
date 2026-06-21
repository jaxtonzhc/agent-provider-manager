"""Tests for sync module — full coverage."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from apm.sync import (
    _format_change,
    _load_state,
    _save_state,
    get_status,
    sync_provider,
)


@pytest.fixture
def mock_sync_deps(mock_config):
    """Mock sync dependencies."""
    provider = {
        "name": "Test",
        "base_url": "https://api.test.com/v1",
        "api_key": "sk-test",
        "protocol": "openai-compatible",
        "models": ["model-a"],
    }
    with patch("apm.sync.get_provider", return_value=provider), \
         patch("apm.sync.get_installed_agents", return_value=["test-agent"]):
        yield provider


class TestSyncProvider:
    def test_provider_not_found(self, mock_config):
        with patch("apm.sync.get_provider", return_value=None):
            results = sync_provider("nonexistent")
        assert len(results) == 1
        assert results[0]["status"] == "error"
        assert "not found" in results[0]["message"]

    def test_no_installed_agents(self, mock_config):
        with patch("apm.sync.get_provider", return_value={"name": "test"}), \
             patch("apm.sync.get_installed_agents", return_value=[]):
            results = sync_provider("test")
        assert results[0]["status"] == "warning"

    def test_unknown_agent(self, mock_config):
        with patch("apm.sync.get_provider", return_value={"name": "test"}), \
             patch("apm.sync.get_installed_agents", return_value=["unknown"]):
            results = sync_provider("test", agents=["unknown"])
        assert results[0]["status"] == "error"

    def test_skips_uninstalled_agent(self, mock_config):
        mock_adapter = MagicMock()
        mock_adapter.is_installed.return_value = False

        with patch("apm.sync.get_provider", return_value={"name": "test"}), \
             patch("apm.sync.ADAPTERS", {"test-agent": mock_adapter}), \
             patch("apm.sync.detect_agent", return_value={"name": "test-agent", "installed": False}):
            results = sync_provider("test", agents=["test-agent"])
        assert results[0]["status"] == "skipped"

    def test_successful_sync(self, mock_config):
        mock_adapter = MagicMock()
        mock_adapter.is_installed.return_value = True
        mock_adapter.read_provider.return_value = {"base_url": "https://old.com"}

        with patch("apm.sync.get_provider", return_value={"name": "test", "base_url": "https://new.com", "api_key": "sk-new"}), \
             patch("apm.sync.ADAPTERS", {"test-agent": mock_adapter}), \
             patch("apm.sync.detect_agent", return_value={"name": "test-agent", "installed": True}), \
             patch("apm.snapshot.save_snapshot"):
            results = sync_provider("test", agents=["test-agent"])

        assert results[0]["status"] == "synced"
        mock_adapter.write_provider.assert_called_once()

    def test_sync_error_handling(self, mock_config):
        mock_adapter = MagicMock()
        mock_adapter.is_installed.return_value = True
        mock_adapter.write_provider.side_effect = PermissionError("denied")

        with patch("apm.sync.get_provider", return_value={"name": "test"}), \
             patch("apm.sync.ADAPTERS", {"test-agent": mock_adapter}), \
             patch("apm.sync.detect_agent", return_value={"name": "test-agent", "installed": True}), \
             patch("apm.snapshot.save_snapshot"):
            results = sync_provider("test", agents=["test-agent"])

        assert results[0]["status"] == "error"
        assert "denied" in results[0]["message"]

    def test_dry_run_no_write(self, mock_config):
        mock_adapter = MagicMock()
        mock_adapter.is_installed.return_value = True
        mock_adapter.read_provider.return_value = {"base_url": "https://old.com"}

        with patch("apm.sync.get_provider", return_value={"name": "test", "base_url": "https://new.com"}), \
             patch("apm.sync.ADAPTERS", {"test-agent": mock_adapter}), \
             patch("apm.sync.detect_agent", return_value={"name": "test-agent", "installed": True}):
            results = sync_provider("test", agents=["test-agent"], dry_run=True)

        assert results[0]["status"] == "dry-run"
        mock_adapter.write_provider.assert_not_called()

    def test_auto_snapshot_failure_doesnt_crash(self, mock_config):
        mock_adapter = MagicMock()
        mock_adapter.is_installed.return_value = True

        with patch("apm.sync.get_provider", return_value={"name": "test"}), \
             patch("apm.sync.ADAPTERS", {"test-agent": mock_adapter}), \
             patch("apm.sync.detect_agent", return_value={"name": "test-agent", "installed": True}), \
             patch("apm.snapshot.save_snapshot", side_effect=Exception("disk full")):
            results = sync_provider("test", agents=["test-agent"])

        # Should still succeed despite snapshot failure
        assert results[0]["status"] == "synced"

    def test_dry_run_no_snapshot(self, mock_config):
        with patch("apm.sync.get_provider", return_value={"name": "test"}), \
             patch("apm.sync.ADAPTERS", {}), \
             patch("apm.snapshot.save_snapshot") as mock_snap:
            sync_provider("test", agents=["test-agent"], dry_run=True)
        mock_snap.assert_not_called()


class TestFormatChange:
    def test_new_provider(self):
        result = _format_change(None, {"base_url": "https://new.com"})
        assert "NEW" in result

    def test_same_url(self):
        result = _format_change({"base_url": "https://same.com"}, {"base_url": "https://same.com"})
        assert "UPDATE" in result

    def test_different_url(self):
        result = _format_change({"base_url": "https://old.com"}, {"base_url": "https://new.com"})
        assert "CHANGE" in result
        assert "old.com" in result
        assert "new.com" in result


class TestStateManagement:
    def test_load_state_empty(self, mock_config):
        state = _load_state()
        assert state == {"syncs": {}}

    def test_save_and_load_state(self, mock_config):
        _save_state({"syncs": {"agent1": {"provider": "test"}}})
        state = _load_state()
        assert state["syncs"]["agent1"]["provider"] == "test"
