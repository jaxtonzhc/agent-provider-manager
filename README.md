# Agent Provider Manager

[![CI](https://github.com/jaxtonzhc/agent-provider-manager/actions/workflows/ci.yml/badge.svg)](https://github.com/jaxtonzhc/agent-provider-manager/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/agent-provider-manager)](https://pypi.org/project/agent-provider-manager/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/pypi/pyversions/agent-provider-manager)](https://pypi.org/project/agent-provider-manager/)

**Centralized API provider management for AI coding agents.**

Your API subscriptions are the source of truth. Agents come and go — your provider config stays.

```
┌─────────────┐
│   Provider   │  ← Your API subscription (base URL + key)
│  (GLM 5.2)  │
└──────┬──────┘
       │  apm sync glm
       ├──────────────→ Claude Code
       ├──────────────→ Codex
       ├──────────────→ Cursor
       ├──────────────→ Hermes
       ├──────────────→ ZCode
       └──────────────→ ... (15 agents supported)
```

## Install

**One-line install** (macOS/Linux):

```bash
curl -sSL https://raw.githubusercontent.com/jaxtonzhc/agent-provider-manager/main/install.sh | bash
```

Or with pip/pipx:

```bash
pip install agent-provider-manager
# or
pipx install agent-provider-manager
```

## Quick Start

```bash
# Interactive setup (recommended for first-time users)
apm init

# Or step by step:
apm scan                                # 1. Scan installed agents
apm provider add deepseek               # 2. Add a provider (key entered interactively)
apm sync deepseek                       # 3. Sync to all agents
apm status                              # 4. Check status
```

## Commands

### Core

| Command | Description |
|---------|-------------|
| `apm init` | Interactive setup guide |
| `apm scan` | Scan installed agents |
| `apm status` | Show current provider for each agent |
| `apm doctor [--fix]` | Diagnose and fix issues |

### Provider Management

| Command | Description |
|---------|-------------|
| `apm provider add` | Interactive provider selection from registry |
| `apm provider add <name>` | Add provider by name (key entered interactively) |
| `apm provider add <name> --key-env VAR` | Add provider with key from env var |
| `apm provider add <name> --url <url>` | Add custom provider (not in registry) |
| `apm provider add <name> --alias myname` | Add with custom alias |
| `apm provider add <name> --variant V` | Select specific variant (e.g., token-plan-cn) |
| `apm provider test [name]` | Test provider connectivity |
| `apm provider rename <old> <new>` | Rename a provider slug |
| `apm provider remove <name>` | Remove a provider |
| `apm provider list` | List configured providers |
| `apm provider show <name>` | Show provider details (models with context/reasoning/vision) |
| `apm provider import` | Import from installed agents |
| `apm provider known` | List known providers from registry |

### Sync

| Command | Description |
|---------|-------------|
| `apm sync` | Interactive provider selection, sync to all agents |
| `apm sync <provider>` | Sync to all installed agents |
| `apm sync <provider> --agents a1,a2` | Sync to specific agents |
| `apm sync <provider> --dry-run` | Preview changes |
| `apm switch <provider>` | Alias for sync |
| `apm undo` | Undo last sync (restore auto-snapshot) |

### Snapshot

| Command | Description |
|---------|-------------|
| `apm snapshot save [--name N]` | Save current agent configs |
| `apm snapshot restore <name>` | Restore from a snapshot |
| `apm snapshot list` | List saved snapshots |
| `apm snapshot delete <name>` | Delete a snapshot |

### Maintenance

| Command | Description |
|---------|-------------|
| `apm update` | Update provider/agent registry |
| `apm self-update` | Update apm itself |
| `apm logs [--tail N]` | Show log file |
| `apm agents` | List known agents |
| `apm providers` | List known providers |

### Debug

```bash
apm --debug status          # Verbose logging
APM_DEBUG=1 apm status     # Via environment variable
```

## Built-in Registry

**10 AI Agents** with full sync support (read + write config):

Claude Code, Codex, Cursor, Hermes, OpenClaw, ZCode, WorkBuddy, Aider, Pi, Oh-My-Pi

**5 additional agents** known (detection only, no sync yet):

GitHub Copilot, Windsurf, Continue, Mimocode, OpenCode

**13 Providers** with pre-configured base URLs, models, and capabilities:

OpenAI, Anthropic, DeepSeek, Google Gemini, GLM (Zhipu), SiliconFlow, OpenRouter, Volcengine, Alibaba Qwen, MiniMax, Xiaomi MiMo, Groq, ZAI

Each model includes metadata: context window (e.g., 1M), reasoning support, and vision capability.

The registry is updated remotely — run `apm update` to get the latest providers and models.

## Storage

```
~/.apm/
├── providers.json          # Your provider configs (mode 0600)
├── sync-state.json         # Sync history
├── registry-cache.json     # Remote registry cache
├── snapshots/              # Agent config backups (apm snapshot / apm undo)
└── apm.log                 # Debug log
```

## Development

```bash
git clone https://github.com/jaxtonzhc/agent-provider-manager.git
cd agent-provider-manager
pip install -e ".[dev]"
make test
```

## License

[MIT](LICENSE)
