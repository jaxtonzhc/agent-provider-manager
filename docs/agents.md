# Agent Configuration Reference

This document describes how each supported agent stores its API configuration.

## Claude Code

**Config file**: `~/.claude/settings.json`

**Format**: JSON with environment variables in `env` block

```json
{
  "env": {
    "ANTHROPIC_AUTH_TOKEN": "your-api-key",
    "ANTHROPIC_BASE_URL": "https://your-provider.com/anthropic",
    "ANTHROPIC_MODEL": "your-model",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "your-model",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "your-model",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "your-model"
  }
}
```

**Notes**:
- Uses Anthropic protocol
- Base URL should end with `/anthropic` for non-Anthropic providers
- Model overrides affect which model is used for each tier

---

## Codex

**Config files**: `~/.codex/config.toml` + `~/.codex/auth.json`

**auth.json format**:
```json
{
  "OPENAI_API_KEY": "your-api-key"
}
```

**config.toml format**:
```toml
model_provider = "custom"

[model_providers.custom]
name = "OpenAI"
requires_openai_auth = true
supports_websockets = true
wire_api = "responses"
```

**Notes**:
- Uses Responses API by default (OpenAI only)
- Non-OpenAI providers need CC Switch proxy for API translation
- `wire_api` should be `"chat_completions"` for non-OpenAI providers

---

## Hermes

**Config files**: `~/.hermes/config.yaml` + `~/.hermes/.env`

**config.yaml relevant section**:
```yaml
model:
  default: mimo-v2.5-pro
  provider: xiaomi
  base_url: https://your-provider.com/v1
  api_key: your-api-key
```

**.env format**:
```
XIAOMI_API_KEY=your-api-key
XIAOMI_BASE_URL=https://your-provider.com/v1
```

**Notes**:
- Uses OpenAI-compatible protocol
- Both config.yaml and .env need to be updated
- Has additional `custom_providers` and `auxiliary` sections

---

## OpenClaw

**Config file**: `~/.openclaw/openclaw.json`

**Format**: JSON with nested providers

```json
{
  "models": {
    "mode": "merge",
    "providers": {
      "your-provider": {
        "baseUrl": "https://your-provider.com/v1",
        "api": "openai-completions",
        "apiKey": "your-api-key",
        "models": [
          {
            "id": "model-name",
            "name": "Model Display Name",
            "reasoning": true,
            "contextWindow": 1048576,
            "maxTokens": 32000
          }
        ]
      }
    }
  }
}
```

**Notes**:
- Multiple providers can coexist
- `mode: "merge"` allows combining providers
- Each provider has its own model list

---

## ZCode

**Config file**: `~/.zcode/v2/config.json`

**Format**: JSON with provider dictionary

```json
{
  "provider": {
    "provider-uuid": {
      "name": "Provider Name",
      "kind": "openai-compatible",
      "options": {
        "apiKey": "your-api-key",
        "baseURL": "https://your-provider.com/v1",
        "apiKeyRequired": true
      },
      "enabled": true,
      "models": {
        "model-name": {
          "limit": { "context": 1000000, "output": 131072 },
          "reasoning": { "enabled": true }
        }
      }
    }
  }
}
```

**Notes**:
- Provider ID is a UUID (generated from provider name hash)
- `kind` can be `"openai-compatible"` or `"anthropic"`
- Supports encrypted credentials in `credentials.json`

---

## WorkBuddy

**Config file**: `~/.workbuddy/models.json`

**Format**: JSON array of model definitions

```json
[
  {
    "id": "model-name",
    "name": "Model Display Name",
    "vendor": "Custom",
    "url": "https://your-provider.com/v1",
    "apiKey": "your-api-key",
    "supportsToolCall": true,
    "supportsImages": false,
    "supportsReasoning": true,
    "reasoning": {
      "supportedEfforts": ["medium", "high", "max", "xhigh"]
    }
  }
]
```

**Notes**:
- Simple array format
- Each entry is a complete model definition
- `vendor` is typically `"Custom"` for non-official providers
