---
name: apm
description: >
  Agent Provider Manager — centralized API provider management for AI coding agents.
  Manage API subscriptions (base URL + API key) and sync them to any installed agent
  with one command. Use when the user wants to manage, add, remove, switch, or sync
  API providers across Claude Code, Codex, Cursor, Hermes, OpenClaw, ZCode, WorkBuddy,
  Aider, Pi, or Oh-My-Pi. Triggers on keywords: "apm", "provider", "api key", "切换供应商",
  "switch provider", "sync config", "provider manager", "api 配置".
---

# Agent Provider Manager (apm)

Centralized CLI tool for managing API providers across AI coding agents.

## Core Concept

**Provider-centric, not agent-centric.** Your API subscriptions are the source of truth. Agents come and go — your provider config stays.

## Installation Check

```bash
apm -V  # Should print version. If not found, install:
pip install agent-provider-manager
```

## Commands Reference

### Setup & Status

```bash
apm init                    # Interactive setup (recommended for first-time)
apm scan                    # List installed agents
apm status                  # Current provider for each agent
apm doctor [--fix]          # Diagnose and fix issues
```

### Provider Management

```bash
# Add from built-in registry (interactive — shows provider list if name omitted)
apm provider add                              # Interactive selection
apm provider add deepseek                     # By registry name (key entered securely)
apm provider add xiaomimimo --variant token-plan-cn  # Specific variant
apm provider add deepseek --alias deepseek-tom       # Custom alias

# Add custom provider (not in registry)
apm provider add myapi --url https://api.example.com/v1 --key-env MY_API_KEY

# Other operations
apm provider list           # List all configured providers
apm provider show <name>    # Show details (URLs, key mask, models)
apm provider rename <old> <new>  # Rename a provider slug
apm provider remove <name>  # Remove a provider
apm provider test [name]    # Test connectivity (all if omitted)
apm provider import         # Import from installed agents
apm provider known          # List built-in registry providers
```

### Sync to Agents

```bash
apm sync                                # Interactive provider selection
apm sync <provider>                     # Sync to all installed agents
apm sync <provider> --agents claude-code,codex  # Specific agents only
apm sync <provider> --dry-run           # Preview changes without writing
apm switch <provider>                   # Alias for sync
```

### Snapshot & Undo

```bash
apm undo                    # Restore from last auto-snapshot (before sync)
apm snapshot save [--name N]  # Manual snapshot
apm snapshot restore <name>
apm snapshot list
apm snapshot delete <name>
```

### Maintenance

```bash
apm update                  # Refresh remote provider/agent registry
apm self-update             # Upgrade apm itself
apm logs [--tail N]         # View debug log
apm agents                  # List all known agents
apm providers               # List all known providers
```

## Supported Agents (10 with full sync)

| Agent | Config Files | Protocol |
|-------|-------------|----------|
| claude-code | `~/.claude/settings.json` | Anthropic env vars, auto `/anthropic` URL |
| codex | `~/.codex/config.toml` + `auth.json` | Responses API; CC Switch proxy for non-OpenAI |
| cursor | `~/.cursor/settings.json` | `openai.*` keys |
| hermes | `~/.hermes/config.yaml` + `.env` | YAML model section + env vars |
| openclaw | `~/.openclaw/openclaw.json` | Merge providers with model metadata |
| zcode | `~/.zcode/v2/config.json` | MD5-derived UUID provider entries |
| workbuddy | `~/.workbuddy/models.json` | JSON model array replacement |
| aider | `~/.aider.conf.yml` + `~/.aider.env` | YAML + OPENAI_* env vars |
| pi | `~/.pi/agent/models.json` | JSON providers with model entries |
| omp | `~/.omp/agent/models.json` | JSON providers (Pi fork) |

5 additional agents known (detection only): Copilot, Windsurf, Continue, Mimocode, OpenCode.

## Built-in Registry (13 Providers)

OpenAI, Anthropic, DeepSeek, Google Gemini, GLM (Zhipu), SiliconFlow, OpenRouter, Volcengine, Alibaba Qwen, MiniMax, Xiaomi MiMo, Groq, ZAI.

Providers with variants (e.g., `token-plan-cn`, `api`) have separate base URLs and anthropic URLs.

## Key Behaviors

- **API key input**: Uses `--key-env VAR` or interactive `getpass` prompt. Avoid passing keys directly via `--key` (shell history risk).
- **Anthropic URL**: Providers with `anthropic_base_url` in registry are used directly for Claude Code. Fallback: replaces `/v1` → `/anthropic` in OpenAI-compatible URLs.
- **Codex proxy**: Non-OpenAI providers need [CC Switch](https://github.com/farion1231/cc-switch) on `127.0.0.1:15721`. apm auto-detects and warns if not running.
- **Atomic writes**: All config files written via tempfile + rename to prevent corruption.
- **Auto-snapshot**: Every `apm sync` creates an auto-snapshot before writing. Use `apm undo` to restore. Auto-snapshots are capped at 10 (oldest auto-cleaned).
- **Model metadata**: Each model tracks `context` (window size), `reasoning` (deep thinking), and `vision` (image input). Shown in `apm provider show` and passed to adapters during sync.

## Storage

```
~/.apm/
├── providers.json          # Provider configs (mode 0600)
├── sync-state.json         # Sync history
├── registry-cache.json     # Remote registry cache (24h TTL)
├── snapshots/              # Config backups
└── apm.log                 # Debug log
```

## Common Workflows

### Switch all agents to a different provider
```bash
apm sync deepseek
```

### Switch only Claude Code
```bash
apm sync xiaomi-mimo --agents claude-code
```

### Add same provider with different keys
```bash
apm provider add deepseek --alias deepseek-personal
apm provider add deepseek --alias deepseek-work
```

### Preview before sync
```bash
apm sync deepseek --dry-run
```

### Recover from bad sync
```bash
apm undo
```

## Source Code

GitHub: `https://github.com/jaxtonzhc/agent-provider-manager`
