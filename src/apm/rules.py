"""Global rules management — inject a reference to shared rules into each agent's config.

Strategy: each agent keeps its own rules file, but we ensure it contains a
reference block pointing to the user's shared global rules file. The AI agent
reads and follows the referenced file at runtime.

The source path is stored in ~/.apm/rules-config.json. If absent, first run
prompts the user to configure it (or creates a default at ~/.apm/global-rules.md).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from apm.config import APM_DIR, HOME, atomic_write

RULES_CONFIG = APM_DIR / "rules-config.json"
DEFAULT_RULES_PATH = APM_DIR / "global-rules.md"

# Unique sentinel for fast detection — NEVER match against the full path.
REFERENCE_SENTINEL = "⚙️[APM:GLOBAL_RULES]⚙️"

# Agent → global rules file path
AGENT_RULES_MAP: dict[str, Path] = {
    "claude-code": HOME / ".claude" / "AGENTS.md",
    "zcode": HOME / ".zcode" / "AGENTS.md",
    "hermes": HOME / ".hermes" / "SOUL.md",
}

DEFAULT_GLOBAL_RULES = """\
# Global Rules (managed by APM)

## Code Standards
- Security first: zero tolerance for vulnerabilities
- Maintainability over cleverness
- Performance under safety and readability constraints

## Preferences
- Respond in Chinese (中文回复)
- Use existing utilities before writing new code
- Minimal abstractions; delete over add

## Conventions
- Follow existing project patterns
- Use standard library when possible
- Error handling: never swallow exceptions silently
"""


def _build_reference_block(source_path: Path) -> str:
    """Build the reference block with the actual source path."""
    return f"""

╔══════════════════════════════════════════════════════════════════════════╗
║  {REFERENCE_SENTINEL}  <<<  DO NOT REMOVE THIS BLOCK  >>>              ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║  ### HIGHEST PRIORITY DIRECTIVE ###                                      ║
║                                                                          ║
║  Before processing ANY request, you MUST read the global rules file:     ║
║                                                                          ║
║      {str(source_path):<60s}   ║
║                                                                          ║
║  This file contains shared rules across ALL AI agents (code standards,   ║
║  security requirements, project preferences). Its priority is HIGHER     ║
║  than everything else in this file. Violating these rules is equivalent  ║
║  to violating a direct user instruction.                                 ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
"""


def _get_source_path() -> Path | None:
    """Read configured source path from rules-config.json."""
    if not RULES_CONFIG.exists():
        return None
    try:
        data = json.loads(RULES_CONFIG.read_text())
        p = Path(data["source"]).expanduser()
        return p
    except (json.JSONDecodeError, KeyError, OSError):
        return None


def _save_source_path(path: Path) -> None:
    """Save source path to rules-config.json."""
    APM_DIR.mkdir(parents=True, exist_ok=True)
    atomic_write(RULES_CONFIG, json.dumps({"source": str(path)}, indent=2) + "\n")


def setup_rules_source(path: str | None = None) -> Path:
    """Configure the global rules source. Interactive if no path given."""
    if path:
        p = Path(path).expanduser().resolve()
        if not p.exists():
            print(f"  Warning: '{p}' does not exist yet.")
        _save_source_path(p)
        return p

    existing = _get_source_path()
    if existing and existing.exists():
        return existing

    if not sys.stdin.isatty():
        # Non-interactive: use default
        _create_default_rules()
        _save_source_path(DEFAULT_RULES_PATH)
        return DEFAULT_RULES_PATH

    from apm.colors import bold, cyan, green

    print(f"\n  {bold('Global Rules Setup')}")
    print(f"  {'=' * 50}")
    print("  APM can inject a reference to your global rules file")
    print("  into each agent's configuration.\n")

    answer = input(
        f"  {cyan('Do you have an existing global rules file? [y/N]')} "
    ).strip().lower()

    if answer in ("y", "yes"):
        raw = input("  Path to your global rules file: ").strip()
        if raw:
            p = Path(raw).expanduser().resolve()
            if not p.exists():
                print(f"  Warning: '{p}' does not exist. Creating it with defaults...")
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(DEFAULT_GLOBAL_RULES)
            _save_source_path(p)
            print(f"  {green('✓')} Configured: {p}")
            return p

    # Create default
    _create_default_rules()
    _save_source_path(DEFAULT_RULES_PATH)
    print(f"  {green('✓')} Created default at: {DEFAULT_RULES_PATH}")
    print("  Edit this file to add your global rules.")
    return DEFAULT_RULES_PATH


def _create_default_rules() -> None:
    """Create default global rules file."""
    if not DEFAULT_RULES_PATH.exists():
        APM_DIR.mkdir(parents=True, exist_ok=True)
        DEFAULT_RULES_PATH.write_text(DEFAULT_GLOBAL_RULES)


def _has_reference(path: Path) -> bool:
    """Check if the file already contains the reference sentinel."""
    if not path.exists():
        return False
    return REFERENCE_SENTINEL in path.read_text()


def inject_reference(agents: list[str] | None = None, source: Path | None = None) -> list[dict]:
    """Inject the global rules reference into each agent's rules file."""
    results: list[dict] = []

    src = source or _get_source_path()
    if not src:
        src = setup_rules_source()

    if not src.exists():
        return [{"agent": "*", "status": "error", "message": f"Global rules not found: {src}"}]

    block = _build_reference_block(src)
    targets = AGENT_RULES_MAP if agents is None else {
        k: v for k, v in AGENT_RULES_MAP.items() if k in agents
    }

    for agent, path in targets.items():
        try:
            if _has_reference(path):
                results.append({"agent": agent, "status": "ok", "message": "reference exists"})
                continue

            path.parent.mkdir(parents=True, exist_ok=True)
            existing = path.read_text() if path.exists() else ""
            path.write_text(existing + block)
            results.append({"agent": agent, "status": "injected", "message": "reference added"})
        except Exception as e:
            results.append({"agent": agent, "status": "error", "message": str(e)})

    return results


def rules_status() -> list[dict]:
    """Check if each agent's rules file contains the global reference."""
    results: list[dict] = []
    for agent, path in AGENT_RULES_MAP.items():
        if not path.exists():
            results.append({"agent": agent, "status": "missing", "path": str(path)})
        elif _has_reference(path):
            results.append({"agent": agent, "status": "linked", "path": str(path)})
        else:
            results.append({"agent": agent, "status": "no-ref", "path": str(path)})
    return results


def print_rules_status() -> None:
    """Pretty-print rules status."""
    from apm.colors import bold, green, red, yellow

    src = _get_source_path()
    print("\n  Global Rules Status")
    print(f"  {'=' * 50}")
    if src:
        exists = src.exists()
        print(f"  Source: {bold(str(src))} {'✓' if exists else red('✗ NOT FOUND')}")
    else:
        print(f"  Source: {yellow('not configured')} (run 'apm rules sync' to setup)")
    print()

    for r in rules_status():
        agent = f"{r['agent']:<12}"
        if r["status"] == "linked":
            print(f"  {green('✓')} {agent} has global reference")
        elif r["status"] == "no-ref":
            print(f"  {yellow('!')} {agent} missing reference")
        elif r["status"] == "missing":
            print(f"  {red('✗')} {agent} rules file not found")
    print()


def print_inject_results(results: list[dict]) -> None:
    """Pretty-print injection results."""
    from apm.colors import green, red, yellow

    print("\n  Rules Injection Results")
    print(f"  {'=' * 50}")
    for r in results:
        agent = f"{r['agent']:<12}"
        if r["status"] == "injected":
            print(f"  {green('✓')} {agent} {r['message']}")
        elif r["status"] == "ok":
            print(f"  {yellow('⊘')} {agent} {r['message']}")
        elif r["status"] == "error":
            print(f"  {red('✗')} {agent} {r['message']}")
    print()
