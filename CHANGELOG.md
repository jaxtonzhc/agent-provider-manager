# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-06-21

### Added

- Initial release
- Provider management (add, remove, list, show, use)
- Agent detection (scan installed agents)
- Sync engine (sync provider config to agents)
- Support for 6 agents:
  - Claude Code
  - Codex
  - Hermes
  - OpenClaw
  - ZCode
  - WorkBuddy
- CC Switch proxy integration for Codex
- Automatic backup before config changes
- Dry-run mode for previewing changes
- Status command to see current provider for each agent
