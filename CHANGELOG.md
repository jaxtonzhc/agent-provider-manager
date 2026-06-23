# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.2] - 2026-06-23

### Added

- Electron GUI 桌面应用（独立于 CLI 发布）
- GUI CI 发布流程（macOS .dmg / Linux .AppImage .deb）

### Fixed

- Agent Status 卡片 URL 溢出问题
- ruff lint 错误（E501 行长度、I001 import 排序）
- Release GUI 构建失败

### Changed

- 版本号对齐：pyproject.toml → 0.1.2

## [0.1.1] - 2026-06-22

### Added

- `apm doctor --fix` 自动修复模式
- 更多 providers: Groq, ZAI, Xiaomi MiMo

### Fixed

- provider test 超时处理改进
- sync 时 agent 配置文件备份逻辑优化

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
