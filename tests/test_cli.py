"""Tests for CLI module."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from apm.cli import build_parser, main


class TestBuildParser:
    def test_parser_has_all_commands(self):
        parser = build_parser()
        # Parse help to ensure no errors
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--help"])
        assert exc_info.value.code == 0

    def test_parse_scan(self):
        parser = build_parser()
        args = parser.parse_args(["scan"])
        assert args.command == "scan"

    def test_parse_status(self):
        parser = build_parser()
        args = parser.parse_args(["status"])
        assert args.command == "status"

    def test_parse_sync_with_agents(self):
        parser = build_parser()
        args = parser.parse_args(["sync", "deepseek", "--agents", "claude-code,codex"])
        assert args.command == "sync"
        assert args.provider == "deepseek"
        assert args.agents == "claude-code,codex"

    def test_parse_sync_dry_run(self):
        parser = build_parser()
        args = parser.parse_args(["sync", "deepseek", "--dry-run"])
        assert args.dry_run is True

    def test_parse_provider_add(self):
        parser = build_parser()
        args = parser.parse_args(["provider", "add", "deepseek", "--key", "sk-test"])
        assert args.subcommand == "add"
        assert args.name == "deepseek"
        assert args.key == "sk-test"

    def test_parse_provider_add_with_variant(self):
        parser = build_parser()
        args = parser.parse_args(
            ["provider", "add", "glm", "--key", "sk-test", "--variant", "token-plan-cn"]
        )
        assert args.variant == "token-plan-cn"

    def test_parse_snapshot_save(self):
        parser = build_parser()
        args = parser.parse_args(["snapshot", "save", "--name", "official"])
        assert args.subcommand == "save"
        assert args.name == "official"

    def test_parse_snapshot_restore(self):
        parser = build_parser()
        args = parser.parse_args(["snapshot", "restore", "official", "--agents", "claude-code"])
        assert args.subcommand == "restore"
        assert args.name == "official"
        assert args.agents == "claude-code"

    def test_parse_doctor_with_fix(self):
        parser = build_parser()
        args = parser.parse_args(["doctor", "--fix"])
        assert args.fix is True

    def test_parse_debug_flag(self):
        parser = build_parser()
        args = parser.parse_args(["--debug", "status"])
        assert args.debug is True
        assert args.command == "status"


class TestMain:
    def test_no_args_shows_help(self, capsys):
        main([])
        output = capsys.readouterr().out
        assert "Agent Provider Manager" in output

    def test_unknown_command(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            main(["nonexistent"])
        assert exc_info.value.code in (1, 2)  # argparse uses 2 for invalid choice

    def test_version(self, capsys):
        with pytest.raises(SystemExit):
            main(["--version"])
        output = capsys.readouterr().out
        assert "apm" in output

    @patch("apm.cli.cmd_scan")
    def test_scan_dispatch(self, mock_scan):
        main(["scan"])
        mock_scan.assert_called_once()

    @patch("apm.cli.cmd_status")
    def test_status_dispatch(self, mock_status):
        main(["status"])
        mock_status.assert_called_once()
