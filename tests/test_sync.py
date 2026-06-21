"""Tests for sync engine."""

from __future__ import annotations

from unittest.mock import patch

from apm.sync import _format_change, sync_provider


def test_sync_provider_not_found():
    results = sync_provider("nonexistent")
    assert len(results) == 1
    assert results[0]["status"] == "error"
    assert "not found" in results[0]["message"]


def test_sync_no_agents():
    with (
        patch("apm.sync.get_provider", return_value={"name": "test"}),
        patch("apm.sync.get_installed_agents", return_value=[]),
    ):
        results = sync_provider("test")
        assert len(results) == 1
        assert results[0]["status"] == "warning"


def test_sync_unknown_agent():
    with (
        patch("apm.sync.get_provider", return_value={"name": "test"}),
        patch("apm.sync.get_installed_agents", return_value=["unknown"]),
    ):
        results = sync_provider("test", agents=["unknown"])
        assert len(results) == 1
        assert results[0]["status"] == "error"


def test_format_change_new():
    result = _format_change(None, {"base_url": "https://new.com/v1"})
    assert "NEW" in result
    assert "https://new.com/v1" in result


def test_format_change_same_url():
    current = {"base_url": "https://same.com/v1"}
    new = {"base_url": "https://same.com/v1"}
    result = _format_change(current, new)
    assert "UPDATE" in result


def test_format_change_different_url():
    current = {"base_url": "https://old.com/v1"}
    new = {"base_url": "https://new.com/v1"}
    result = _format_change(current, new)
    assert "CHANGE" in result
    assert "https://old.com/v1" in result
    assert "https://new.com/v1" in result
