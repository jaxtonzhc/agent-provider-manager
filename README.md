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
       └──────────────→ ... (19 agents supported)
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
# 1. Scan installed agents
apm scan

# 2. Add a provider (uses built-in registry — just provide the key!)
apm provider add deepseek --key sk-xxx

# 3. Sync to all agents
apm sync deepseek

# 4. Check status
apm status
```

## Commands

### Core

| Command | Description |
|---------|-------------|
| `apm scan` | Scan installed agents |
| `apm status` | Show current provider for each agent |
| `apm doctor [--fix]` | Diagnose and fix issues |

### Provider Management

| Command | Description |
|---------|-------------|
| `apm provider add <name> --key <key>` | Add provider (auto-fills URL from registry) |
| `apm provider add <name> --url <url> --key <key>` | Add custom provider |
| `apm provider remove <name>` | Remove a provider |
| `apm provider list` | List configured providers |
| `apm provider show <name>` | Show provider details |
| `apm provider use <name>` | Set active provider |
| `apm provider import` | Import from installed agents |
| `apm provider known` | List known providers from registry |

### Sync

| Command | Description |
|---------|-------------|
| `apm sync <provider>` | Sync to all installed agents |
| `apm sync <provider> --agents a1,a2` | Sync to specific agents |
| `apm sync <provider> --dry-run` | Preview changes |
| `apm switch <provider>` | Alias for sync |

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

**19 AI Agents** supported out of the box:

Claude Code, Codex, Cursor, GitHub Copilot, Windsurf, Hermes, OpenClaw, ZCode, WorkBuddy, Aider, Continue, Cody, Tabnine, Amazon Q, Mimocode, OpenCode, Pi, OhMyPi

**21 Providers** with pre-configured base URLs and models:

OpenAI, Anthropic, DeepSeek, Google Gemini, GLM (Zhipu), xAI (Grok), Moonshot, SiliconFlow, OpenRouter, Together AI, Fireworks AI, Volcengine, Baidu Qianfan, Alibaba Qwen, MiniMax, Mistral AI, Perplexity, Xiaomi MiMo, Groq, Cerebras, SambaNova

The registry is updated remotely — run `apm update` to get the latest providers and models.

## Storage

```
~/.apm/
├── providers.json          # Your provider configs
├── sync-state.json         # Sync history
├── registry-cache.json     # Remote registry cache
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
