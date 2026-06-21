# apm — Agent Provider Manager

[![CI](https://github.com/jaxtonzhc/apm/actions/workflows/ci.yml/badge.svg)](https://github.com/jaxtonzhc/apm/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/agent-provider-manager)](https://pypi.org/project/agent-provider-manager/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/pypi/pyversions/agent-provider-manager)](https://pypi.org/project/agent-provider-manager/)

**Provider-centric API key management for AI coding agents.**

Your API subscriptions are the source of truth. Agents come and go — your provider config stays.

## Why?

You have multiple AI coding agents (Claude Code, Codex, Hermes, OpenClaw, ZCode, WorkBuddy) and multiple API subscriptions (OpenAI, DeepSeek, Xiaomi MiMo, GLM...). When you get a new subscription or want to switch, you have to manually update each agent's config.

**apm flips the model**: manage providers centrally, sync to any agent with one command.

```
┌─────────────┐
│   Provider   │  ← Your API subscription (base URL + key)
│  (GLM 5.2)  │
└──────┬──────┘
       │  apm sync glm
       ├──────────────→ Claude Code
       ├──────────────→ Codex
       ├──────────────→ Hermes
       ├──────────────→ OpenClaw
       ├──────────────→ ZCode
       └──────────────→ WorkBuddy
```

## Install

```bash
pip install agent-provider-manager
```

Or with [pipx](https://pypa.github.io/pipx/) (recommended for CLI tools):

```bash
pipx install agent-provider-manager
```

## Quick Start

```bash
# 1. Scan installed agents
apm scan

# 2. Add your API provider
apm provider add glm \
  --url "https://open.bigmodel.cn/api/paas/v1" \
  --key "your-api-key" \
  --models "GLM-5.2,GLM-5-Turbo"

# 3. Sync to all agents
apm sync glm

# 4. Check status
apm status
```

## Commands

### Agent Management

```bash
apm scan              # Scan installed agents
apm status            # Show current provider for each agent
```

### Provider Management

```bash
apm provider add <name> --url <url> --key <key> [--models m1,m2]
apm provider remove <name>
apm provider list
apm provider show <name>
apm provider use <name>     # Set active provider
```

### Sync

```bash
apm sync <provider>                        # Sync to all installed agents
apm sync <provider> --agents claude-code,codex  # Sync to specific agents
apm sync <provider> --dry-run              # Preview changes without writing

apm switch <provider>                      # Alias for sync
```

## Supported Agents

| Agent | Config Location | Format |
|-------|----------------|--------|
| Claude Code | `~/.claude/settings.json` | JSON (env vars) |
| Codex | `~/.codex/config.toml` + `auth.json` | TOML + JSON |
| Hermes | `~/.hermes/config.yaml` + `.env` | YAML + dotenv |
| OpenClaw | `~/.openclaw/openclaw.json` | JSON |
| ZCode | `~/.zcode/v2/config.json` | JSON |
| WorkBuddy | `~/.workbuddy/models.json` | JSON |

## Codex Proxy

Codex uses OpenAI's Responses API. For non-OpenAI providers, apm automatically detects if [CC Switch](https://github.com/nicepkg/cc-switch) is running on `127.0.0.1:15721` and configures Codex to route through it (handles Response API → Chat Completions translation).

## Storage

```
~/.apm/
├── providers.json     # Provider registry
└── sync-state.json    # Sync history
```

Config files are created automatically on first use.

## Development

```bash
git clone https://github.com/jaxtonzhc/apm.git
cd apm
pip install -e ".[dev]"
make test
```

## License

[MIT](LICENSE)
