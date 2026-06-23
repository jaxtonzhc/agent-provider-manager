"""Hermes agent adapter (deep integration).

Config: ~/.hermes/config.yaml
Structure:
  model:
    default: <model-id>          # active model
    provider: <provider-slug>    # active provider
  custom_providers:              # list of provider configs
    - name: <slug>
      base_url: <url>
      api_key: <key>
      api_mode: chat_completions
      models:
        <model-id>:
          context_length: N
          name: <display-name>
      model: <default-model-for-this-provider>

Activation: set model.default + model.provider to target.
"""

from __future__ import annotations

from pathlib import Path

from apm.agents.base import AgentAdapter

HOME = Path.home()
HERMES_CONFIG = HOME / ".hermes" / "config.yaml"


def _load_yaml() -> str:
    if not HERMES_CONFIG.exists():
        return ""
    return HERMES_CONFIG.read_text()


def _parse_env(path: Path) -> dict[str, str]:
    """Parse .env file into dict."""
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def _parse_custom_providers(text: str) -> list[dict]:
    """Parse custom_providers list from YAML text (simplified parser)."""
    import re
    providers: list[dict] = []
    in_section = False
    current: dict | None = None
    in_models = False

    for line in text.splitlines():
        stripped = line.strip()

        if stripped == "custom_providers:" or stripped.startswith("custom_providers:"):
            in_section = True
            continue

        if in_section:
            # Detect end of custom_providers section (new top-level key)
            is_toplevel = (
                not line.startswith((" ", "\t")) and stripped
                and not stripped.startswith("#")
            )
            if is_toplevel:
                break

            # New provider entry
            if re.match(r"^- name:", stripped):
                if current:
                    providers.append(current)
                current = {"name": stripped.split(":", 1)[1].strip(), "models": {}}
                in_models = False
                continue

            if current is None:
                continue

            if stripped.startswith("base_url:"):
                current["base_url"] = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("api_key:"):
                current["api_key"] = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("api_mode:"):
                current["api_mode"] = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("model:") and not in_models:
                current["default_model"] = stripped.split(":", 1)[1].strip()
            elif stripped == "models:":
                in_models = True
            elif in_models:
                # model entry like "deepseek-v4-flash:"
                m = re.match(r"^(\S+):$", stripped)
                if m:
                    current["models"][m.group(1)] = {}
                elif ":" in stripped and current["models"]:
                    last_model = list(current["models"].keys())[-1]
                    k, v = stripped.split(":", 1)
                    current["models"][last_model][k.strip()] = v.strip()

    if current:
        providers.append(current)
    return providers


class HermesAdapter(AgentAdapter):
    name = "hermes"

    def is_installed(self) -> bool:
        return HERMES_CONFIG.exists()

    def read_provider(self) -> dict | None:
        text = _load_yaml()
        if not text:
            return None

        from apm.agents.base import yaml_get
        provider_slug = yaml_get(text, "model", "provider")
        model = yaml_get(text, "model", "default")

        if not provider_slug:
            return None

        # 1. Check custom_providers
        providers = _parse_custom_providers(text)
        for p in providers:
            if p["name"] == provider_slug:
                return {
                    "base_url": p.get("base_url", ""),
                    "api_key": p.get("api_key", ""),
                    "model": model,
                    "protocol": "openai-compatible",
                }

        # 2. Check .env vars (pattern: PROVIDER_BASE_URL / PROVIDER_API_KEY)
        env_path = HERMES_CONFIG.parent / ".env"
        if env_path.exists():
            env_vars = _parse_env(env_path)
            prefix = provider_slug.upper().replace("-", "_")
            base_url = env_vars.get(f"{prefix}_BASE_URL", "")
            api_key = env_vars.get(f"{prefix}_API_KEY", "")
            if base_url or api_key:
                return {
                    "base_url": base_url,
                    "api_key": api_key,
                    "model": model,
                    "protocol": "openai-compatible",
                }

        return {"base_url": "", "api_key": "", "model": model, "protocol": "openai-compatible"}

    def write_provider(self, provider: dict) -> None:
        """Add provider to custom_providers list if not already present."""
        from apm.config import atomic_write

        self.backup(HERMES_CONFIG)
        text = _load_yaml()

        slug = provider["name"].lower().replace(" ", "")
        base_url = provider["base_url"].rstrip("/")
        api_key = provider["api_key"]
        models = provider.get("models", [])
        model_meta = provider.get("_model_meta") or provider.get("model_meta", {})

        # Build YAML for the new custom provider entry
        model_yaml_lines = []
        for m in models:
            meta = model_meta.get(m, {})
            ctx = meta.get("context", 128000)
            display = meta.get("name", m)
            model_yaml_lines.append(f"      {m}:")
            model_yaml_lines.append(f"        context_length: {ctx}")
            model_yaml_lines.append(f"        name: {display}")

        new_entry = [
            f"- name: {slug}",
            f"  base_url: {base_url}",
            f"  api_key: {api_key}",
            "  api_mode: chat_completions",
        ]
        if models:
            new_entry.append(f"  model: {models[0]}")
            new_entry.append("  models:")
            for ml in model_yaml_lines:
                new_entry.append(f"  {ml}")

        # ponytail: naive YAML append — works for hermes' flat custom_providers format
        # Upgrade path: use ruamel.yaml for full round-trip editing

        if "custom_providers:" in text:
            # Append to existing list
            lines = text.splitlines()
            insert_idx = None
            for i, line in enumerate(lines):
                if line.strip().startswith("custom_providers:"):
                    # Find end of the list
                    j = i + 1
                    while j < len(lines):
                        ln = lines[j]
                        is_top = (
                            not ln.startswith((" ", "\t"))
                            and ln.strip()
                            and not ln.strip().startswith("#")
                        )
                        if is_top:
                            break
                        j += 1
                    insert_idx = j
                    break
            if insert_idx is not None:
                entry_lines = [f"- name: {slug}",
                               f"  base_url: {base_url}",
                               f"  api_key: {api_key}",
                               "  api_mode: chat_completions"]
                if models:
                    entry_lines.append(f"  model: {models[0]}")
                    entry_lines.append("  models:")
                    entry_lines.extend(f"    {ml.strip()}" for ml in model_yaml_lines)
                lines[insert_idx:insert_idx] = entry_lines
                text = "\n".join(lines) + "\n"
        else:
            # Create section
            entry_lines = ["\ncustom_providers:",
                           f"- name: {slug}",
                           f"  base_url: {base_url}",
                           f"  api_key: {api_key}",
                           "  api_mode: chat_completions"]
            if models:
                entry_lines.append(f"  model: {models[0]}")
                entry_lines.append("  models:")
                entry_lines.extend(f"    {ml.strip()}" for ml in model_yaml_lines)
            text += "\n".join(entry_lines) + "\n"

        atomic_write(HERMES_CONFIG, text)

    def activate_provider(self, provider: dict, model: str | None = None) -> None:
        """Set model.default and model.provider in config.yaml."""
        from apm.agents.base import yaml_set
        from apm.config import atomic_write

        text = _load_yaml()
        slug = provider["name"].lower().replace(" ", "")

        if not model:
            models = provider.get("models", [])
            model = models[0] if models else None

        if model:
            text = yaml_set(text, "model", "default", model)
        text = yaml_set(text, "model", "provider", slug)

        atomic_write(HERMES_CONFIG, text)

    def has_provider(self, provider: dict) -> bool:
        text = _load_yaml()
        target_url = provider.get("base_url", "").rstrip("/")
        target_key = provider.get("api_key", "")

        # Check custom_providers
        providers = _parse_custom_providers(text)
        for p in providers:
            if p.get("base_url", "").rstrip("/") == target_url and p.get("api_key") == target_key:
                return True

        # Check .env vars
        env_path = HERMES_CONFIG.parent / ".env"
        if env_path.exists():
            env_vars = _parse_env(env_path)
            for k, v in env_vars.items():
                if k.endswith("_BASE_URL") and v.rstrip("/") == target_url:
                    prefix = k[:-9]  # strip _BASE_URL
                    env_key = env_vars.get(f"{prefix}_API_KEY", "")
                    if env_key == target_key:
                        return True
        return False
