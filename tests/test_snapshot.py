"""Tests for snapshot module."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from apm.snapshot import (
    delete_snapshot,
    list_snapshots,
    restore_snapshot,
    save_snapshot,
    SNAPSHOTS_DIR,
    AGENT_CONFIG_FILES,
)


@pytest.fixture
def mock_snapshot_dir(tmp_path):
    """Mock snapshot directory."""
    snap_dir = tmp_path / "snapshots"
    snap_dir.mkdir()
    with patch("apm.snapshot.SNAPSHOTS_DIR", snap_dir):
        yield snap_dir


@pytest.fixture
def mock_agent_files(tmp_path):
    """Create mock agent config files."""
    files = {}
    # Create claude config
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir(parents=True)
    claude_file = claude_dir / "settings.json"
    claude_file.write_text(json.dumps({"env": {"ANTHROPIC_AUTH_TOKEN": "sk-test"}}))
    files["claude-code"] = [claude_file]

    # Create workbuddy config
    wb_dir = tmp_path / ".workbuddy"
    wb_dir.mkdir(parents=True)
    wb_file = wb_dir / "models.json"
    wb_file.write_text(json.dumps([{"id": "test", "apiKey": "sk-test"}]))
    files["workbuddy"] = [wb_file]

    return files


class TestSaveSnapshot:
    def test_save_creates_directory(self, mock_snapshot_dir, mock_agent_files):
        with patch("apm.snapshot.AGENT_CONFIG_FILES", mock_agent_files), \
             patch("apm.snapshot.get_installed_agents", return_value=["claude-code"]):
            result = save_snapshot(name="test-snap")

        assert result["name"] == "test-snap"
        assert (mock_snapshot_dir / "test-snap").exists()
        assert (mock_snapshot_dir / "test-snap" / "meta.json").exists()

    def test_save_copies_config_files(self, mock_snapshot_dir, mock_agent_files):
        with patch("apm.snapshot.AGENT_CONFIG_FILES", mock_agent_files), \
             patch("apm.snapshot.get_installed_agents", return_value=["claude-code"]):
            result = save_snapshot(name="test-snap")

        assert result["agents"]["claude-code"]["status"] == "saved"
        assert "settings.json" in result["agents"]["claude-code"]["files"]
        assert (mock_snapshot_dir / "test-snap" / "claude-code" / "settings.json").exists()

    def test_save_multiple_agents(self, mock_snapshot_dir, mock_agent_files):
        with patch("apm.snapshot.AGENT_CONFIG_FILES", mock_agent_files), \
             patch("apm.snapshot.get_installed_agents", return_value=["claude-code", "workbuddy"]):
            result = save_snapshot(name="multi")

        assert "claude-code" in result["agents"]
        assert "workbuddy" in result["agents"]
        assert result["agents"]["claude-code"]["status"] == "saved"
        assert result["agents"]["workbuddy"]["status"] == "saved"

    def test_save_skips_missing_files(self, mock_snapshot_dir, mock_agent_files):
        with patch("apm.snapshot.AGENT_CONFIG_FILES", mock_agent_files), \
             patch("apm.snapshot.get_installed_agents", return_value=["nonexistent"]):
            result = save_snapshot(name="skip-test")

        assert result["agents"]["nonexistent"]["status"] == "skipped"

    def test_save_default_name_is_timestamp(self, mock_snapshot_dir, mock_agent_files):
        with patch("apm.snapshot.AGENT_CONFIG_FILES", mock_agent_files), \
             patch("apm.snapshot.get_installed_agents", return_value=["claude-code"]):
            result = save_snapshot()

        # Name should be a timestamp-like string
        assert len(result["name"]) == 15  # YYYYMMDD-HHMMSS
        assert "-" in result["name"]


class TestRestoreSnapshot:
    def test_restore_copies_files_back(self, mock_snapshot_dir, mock_agent_files):
        # Save first
        with patch("apm.snapshot.AGENT_CONFIG_FILES", mock_agent_files), \
             patch("apm.snapshot.get_installed_agents", return_value=["claude-code"]):
            save_snapshot(name="test-snap")

        # Modify the original file
        original_file = mock_agent_files["claude-code"][0]
        original_file.write_text(json.dumps({"env": {"ANTHROPIC_AUTH_TOKEN": "sk-modified"}}))

        # Restore
        with patch("apm.snapshot.AGENT_CONFIG_FILES", mock_agent_files):
            result = restore_snapshot("test-snap")

        assert result["agents"]["claude-code"]["status"] == "restored"
        content = json.loads(original_file.read_text())
        assert content["env"]["ANTHROPIC_AUTH_TOKEN"] == "sk-test"

    def test_restore_nonexistent_snapshot(self, mock_snapshot_dir):
        result = restore_snapshot("does-not-exist")
        assert "error" in result

    def test_restore_selective_agents(self, mock_snapshot_dir, mock_agent_files):
        # Save both agents
        with patch("apm.snapshot.AGENT_CONFIG_FILES", mock_agent_files), \
             patch("apm.snapshot.get_installed_agents", return_value=["claude-code", "workbuddy"]):
            save_snapshot(name="test-snap")

        # Restore only claude-code
        with patch("apm.snapshot.AGENT_CONFIG_FILES", mock_agent_files):
            result = restore_snapshot("test-snap", agents=["claude-code"])

        assert "claude-code" in result["agents"]
        assert "workbuddy" not in result["agents"]


class TestListSnapshots:
    def test_list_empty(self, mock_snapshot_dir):
        snapshots = list_snapshots()
        assert snapshots == []

    def test_list_returns_snapshots(self, mock_snapshot_dir, mock_agent_files):
        with patch("apm.snapshot.AGENT_CONFIG_FILES", mock_agent_files), \
             patch("apm.snapshot.get_installed_agents", return_value=["claude-code"]):
            save_snapshot(name="snap-1")
            save_snapshot(name="snap-2")

        snapshots = list_snapshots()
        names = [s["name"] for s in snapshots]
        assert "snap-1" in names
        assert "snap-2" in names


class TestDeleteSnapshot:
    def test_delete_existing(self, mock_snapshot_dir, mock_agent_files):
        with patch("apm.snapshot.AGENT_CONFIG_FILES", mock_agent_files), \
             patch("apm.snapshot.get_installed_agents", return_value=["claude-code"]):
            save_snapshot(name="to-delete")

        assert delete_snapshot("to-delete") is True
        assert not (mock_snapshot_dir / "to-delete").exists()

    def test_delete_nonexistent(self, mock_snapshot_dir):
        assert delete_snapshot("does-not-exist") is False
