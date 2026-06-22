"""Agent Provider Manager — CLI.

Centralized API provider management for AI coding agents.
Manage your API subscriptions and sync them to any agent with one command.
"""

from __future__ import annotations

import argparse
import getpass
import os
import sys

from apm import __version__
from apm.logging import setup_logging


def cmd_scan(args: argparse.Namespace) -> None:
    """Scan installed agents."""
    if getattr(args, "json", False):
        import json

        from apm.detect import detect_all
        print(json.dumps(detect_all(), ensure_ascii=False))
    else:
        from apm.detect import print_scan_results
        print_scan_results()


def cmd_status(args: argparse.Namespace) -> None:
    """Show current provider status."""
    if getattr(args, "json", False):
        import json

        from apm.providers import list_all
        from apm.sync import get_status
        print(json.dumps({
            "providers": list_all(),
            "agents": get_status(),
        }, ensure_ascii=False))
    else:
        from apm.sync import print_status
        print_status()


def cmd_provider(args: argparse.Namespace) -> None:
    """Provider management subcommands."""
    sub = args.subcommand
    if not sub:
        print("  Usage: apm provider <subcommand>")
        print("  Subcommands: add, update, remove, rename, list, show, test, models, import, known")
        return

    if sub == "add":
        _cmd_provider_add(args)
    elif sub == "remove":
        _cmd_provider_remove(args)
    elif sub == "update":
        _cmd_provider_update(args)
    elif sub == "list":
        if getattr(args, "json", False):
            import json

            from apm.providers import list_all
            print(json.dumps(list_all(), ensure_ascii=False))
        else:
            from apm.providers import print_list
            print_list()
    elif sub == "show":
        if getattr(args, "json", False):
            import json

            from apm.providers import get
            data = get(args.name)
            print(json.dumps(data, ensure_ascii=False) if data else '{}')
        else:
            from apm.providers import print_detail
            print_detail(args.name)
    elif sub == "import":
        _cmd_provider_import(args)
    elif sub == "known":
        from apm.registry import print_providers
        print_providers()
    elif sub == "test":
        _cmd_provider_test(args)
    elif sub == "rename":
        _cmd_provider_rename(args)
    elif sub == "models":
        _cmd_provider_models(args)


def _resolve_api_key(args: argparse.Namespace) -> str | None:
    """Resolve API key from --key-env or interactive prompt.

    --key is kept for backward compat but prints a security warning.
    """
    key_direct = getattr(args, "key", None)
    if key_direct:
        from apm.colors import yellow
        msg = "⚠ --key exposes secrets in shell history."
        msg += " Prefer --key-env or interactive prompt."
        print(f"  {yellow(msg)}")
        return key_direct
    env_name = getattr(args, "key_env", None)
    if env_name:
        val = os.environ.get(env_name)
        if not val:
            print(f"  Error: environment variable ${env_name} is not set")
            return None
        return val
    if not sys.stdin.isatty():
        print("  Error: no API key provided. Use --key-env VAR in non-interactive mode.")
        return None
    try:
        return getpass.getpass("  Enter API key: ")
    except (EOFError, KeyboardInterrupt):
        print()
        return None


def _pick_provider_from_registry() -> tuple[str, str | None] | None:
    """Interactive provider + variant selection. Returns (slug, variant) or None."""
    from apm.menu import pick
    from apm.registry import list_providers as list_registry_providers

    providers = list_registry_providers()
    options = []
    for slug, info in sorted(providers.items()):
        variants = info.get("variants", {})
        v_count = len(variants)
        first_url = next(iter(variants.values()), {}).get("base_url", "") if variants else ""
        models = info.get("models", [])
        model_str = ", ".join(m["id"] if isinstance(m, dict) else m for m in models[:3])
        v_hint = f" [{v_count} variants]" if v_count > 1 else ""
        label = f"{info['name']} ({slug}){v_hint}"
        detail = f"{first_url}  models: {model_str}" if model_str else first_url
        options.append({
            "label": label,
            "detail": detail,
            "slug": slug,
            "info": info,
        })

    chosen = pick("Select a provider", options)
    if not chosen:
        return None

    slug = chosen["slug"]
    info = chosen["info"]
    variants = info.get("variants", {})

    variant = None
    if len(variants) == 1:
        variant = next(iter(variants))
    elif len(variants) > 1:
        v_options = []
        for vname, vinfo in variants.items():
            desc = vinfo.get("description", "")
            url = vinfo.get("base_url", "")
            detail = f"{desc}  {url}" if desc else url
            v_options.append({"label": vname, "detail": detail})
        v_chosen = pick("Select a variant", v_options, allow_filter=False)
        if v_chosen:
            variant = v_chosen["label"]

    return slug, variant


def _cmd_provider_add(args: argparse.Namespace) -> None:
    """Add a new provider."""
    from apm.colors import bold, green, yellow
    from apm.providers import add, fuzzy_match
    from apm.registry import list_providers as list_registry_providers
    from apm.registry import resolve_provider

    name = getattr(args, "name", None)
    variant = getattr(args, "variant", None)

    if not name:
        result = _pick_provider_from_registry()
        if not result:
            return
        name, variant = result

    key = _resolve_api_key(args)
    if not key:
        return

    resolved = resolve_provider(name, key, variant=variant)
    if resolved:
        base_url = args.url or resolved["base_url"]
        protocol = args.protocol or resolved["protocol"]
        models = args.models or resolved.get("models", [])
        if isinstance(models, str):
            models = [m.strip() for m in models.split(",") if m.strip()]
        anthro_url = getattr(args, "anthropic_url", None) or resolved.get("anthropic_base_url")
        meta = resolved.get("_model_meta")
        user_alias = getattr(args, "alias", None)
        slug = add(
            resolved["name"], base_url, key, protocol, models,
            anthropic_base_url=anthro_url, model_meta=meta,
            alias=user_alias,
        )
        print(f"  {green('✓')} Added provider: {bold(slug)}")
        print(f"    URL: {base_url}")
        if anthro_url:
            print(f"    Anthropic URL: {anthro_url}")
        print(f"    Protocol: {protocol}")
        if models:
            print(f"    Models: {', '.join(models[:5])}")

    else:
        registry_names = list(list_registry_providers().keys())
        suggestions = fuzzy_match(name, registry_names)
        if suggestions:
            hint = ", ".join(yellow(s) for s in suggestions[:3])
            print(f"  '{name}' not found in registry. Did you mean: {hint}?")
            if not args.url:
                return

        url = args.url
        interactive = sys.stdin.isatty()
        if not url:
            if not interactive:
                print("  Error: --url required for custom providers in non-interactive mode.")
                return
            from apm.colors import dim
            print(f"\n  {bold('Custom Provider Setup')}")
            print("  " + "─" * 40)
            url = input("  Base URL (e.g. https://api.example.com/v1): ").strip()
            if not url:
                print("  Cancelled.")
                return

        anthro_url = getattr(args, "anthropic_url", None)
        if not anthro_url and interactive and not args.url:
            from apm.colors import dim
            raw_anthro = input(
                f"  Anthropic Base URL {dim('(Enter to skip)')}: "
            ).strip()
            if raw_anthro:
                anthro_url = raw_anthro

        models: list[str] = []
        if args.models:
            models = [m.strip() for m in args.models.split(",") if m.strip()]

        if not models and interactive:
            print(f"\n  Fetching models from {url}...")
            from apm.providers import fetch_models
            fetched = fetch_models(url, key)
            if fetched:
                print(f"  Found {green(str(len(fetched)))} models:")
                for i, m in enumerate(fetched, 1):
                    print(f"    {i:3d}. {m}")
                sel = input(
                    "\n  Enter model numbers (e.g. 1,3,5) or 'all' [all]: "
                ).strip()
                if not sel or sel.lower() == "all":
                    models = fetched
                else:
                    for part in sel.split(","):
                        part = part.strip()
                        if part.isdigit():
                            idx = int(part) - 1
                            if 0 <= idx < len(fetched):
                                models.append(fetched[idx])
            else:
                raw = input("  Models (comma-separated, or Enter to skip): ").strip()
                if raw:
                    models = [m.strip() for m in raw.split(",") if m.strip()]

        alias = getattr(args, "alias", None)
        protocol = args.protocol or "openai-compatible"
        slug = add(
            name, url, key, protocol, models,
            anthropic_base_url=anthro_url, alias=alias,
        )
        print(f"\n  {green('✓')} Added provider: {bold(slug)}")
        print(f"    URL: {url}")
        if anthro_url:
            print(f"    Anthropic URL: {anthro_url}")
        if models:
            shown = ", ".join(models[:5])
            extra = f" (+{len(models) - 5} more)" if len(models) > 5 else ""
            print(f"    Models: {shown}{extra}")


def _cmd_provider_update(args: argparse.Namespace) -> None:
    """Update an existing provider's fields."""
    from apm.colors import bold, green, red
    from apm.providers import get, rename, update

    provider = get(args.name)
    if not provider:
        print(f"  {red('✗')} Provider '{args.name}' not found.")
        return

    kwargs = {}
    if args.url:
        kwargs["base_url"] = args.url
    anthro = getattr(args, "anthropic_url", None)
    if anthro is not None:
        kwargs["anthropic_base_url"] = anthro
    if getattr(args, "key_env", None):
        val = os.environ.get(args.key_env)
        if not val:
            print(f"  {red('✗')} Env var '{args.key_env}' is empty or not set.")
            return
        kwargs["api_key"] = val
    elif getattr(args, "key", None):
        kwargs["api_key"] = args.key
    if getattr(args, "models", None):
        kwargs["models"] = args.models

    new_name = getattr(args, "rename", None)
    if not kwargs and not new_name:
        print("  Nothing to update. Use --url, --anthropic-url, --key-env, --models, or --rename.")
        return

    if kwargs:
        update(args.name, **kwargs)
    if new_name:
        rename(args.name, new_name)

    display_name = new_name or args.name
    print(f"  {green('✓')} Updated provider: {bold(display_name)}")
    if new_name:
        print(f"    renamed: {args.name} → {new_name}")
    for k, v in kwargs.items():
        if k == "api_key":
            v = v[:4] + "..." + v[-4:] if len(v) > 8 else "***"
        print(f"    {k}: {v}")


def _cmd_provider_remove(args: argparse.Namespace) -> None:
    """Remove a provider."""
    from apm.colors import green, red
    from apm.providers import fuzzy_match, list_all, remove
    try:
        remove(args.name)
        print(f"  {green('✓')} Removed provider: {args.name}")
    except ValueError:
        slugs = [p["slug"] for p in list_all()]
        suggestions = fuzzy_match(args.name, slugs)
        if suggestions:
            hint = ", ".join(suggestions[:3])
            print(f"  {red('✗')} Provider '{args.name}' not found. Did you mean: {hint}?")
        else:
            print(f"  {red('✗')} Provider '{args.name}' not found.")
            print("  → Run 'apm provider list' to see configured providers.")


def _cmd_provider_test(args: argparse.Namespace) -> None:
    """Test provider connectivity."""
    from apm.colors import bold, green, red
    from apm.providers import list_all, test_provider

    if hasattr(args, "name") and args.name:
        names = [args.name]
    else:
        providers = list_all()
        if not providers:
            print("  No providers configured. Use 'apm provider add' first.")
            return
        names = [p["slug"] for p in providers]

    print("\n  Testing Provider Connectivity")
    print("  " + "=" * 45)
    for name in names:
        result = test_provider(name)
        if result["status"] == "ok":
            latency = result.get("latency_ms", "?")
            print(f"  {green('✓')}  {bold(name):<20} {result['message']} ({latency}ms)")
        else:
            print(f"  {red('✗')}  {bold(name):<20} {result['message']}")
    print()


def _cmd_provider_import(args: argparse.Namespace) -> None:
    """Import providers from installed agents."""
    from apm.providers import import_from_agents

    agents = None
    if hasattr(args, "agents") and args.agents:
        agents = [a.strip() for a in args.agents.split(",")]

    results = import_from_agents(agents)
    if not results:
        print("  No providers found to import.")
        return

    print("\n  Import Results")
    print("  " + "=" * 45)
    for r in results:
        icon = {"imported": "✓", "exists": "⊘", "merged": "≡", "error": "✗"}.get(r["status"], "?")
        detail = r.get("message", r["provider"] or "(failed)")
        if r["status"] == "merged":
            detail = f"skipped — {r.get('message', 'same key')}"
        elif r["status"] == "exists":
            detail = f"skipped — '{r['provider']}' already exists"
        elif r["status"] == "imported":
            detail = f"added as '{r['provider']}'"
        print(f"  {icon}  {r['agent']:<15} {detail}")
    print()


def _cmd_provider_models(args: argparse.Namespace) -> None:
    """Fetch and display available models from a provider."""
    from apm.colors import bold, dim, green, red
    from apm.providers import fetch_models, get

    name = args.name
    p = get(name)
    if not p:
        print(f"  {red('✗')} Provider '{name}' not found.")
        return

    print(f"\n  Fetching models from {bold(name)}...")
    models = fetch_models(p["base_url"], p["api_key"])
    if not models:
        print(f"  {red('✗')} No models returned (endpoint may not support /models)")
        return

    print(f"  {green('✓')} Found {len(models)} models {dim('(sorted by version)')}\n")
    for i, m in enumerate(models, 1):
        print(f"  {i:3d}. {m}")
    print()


def _cmd_provider_rename(args: argparse.Namespace) -> None:
    """Rename a provider's slug."""
    from apm.colors import green, red
    from apm.providers import rename
    try:
        rename(args.old_name, args.new_name)
        print(f"  {green('✓')} Renamed: {args.old_name} → {args.new_name}")
    except ValueError as e:
        print(f"  {red('✗')} {e}")


def _pick_configured_provider() -> str | None:
    """Interactive selection from user's configured providers."""
    from apm.menu import pick
    from apm.providers import list_all

    providers = list_all()
    if not providers:
        print("  No providers configured. Run 'apm provider add' first.")
        return None

    options = [
        {
            "label": f"{p['name']} ({p['slug']})",
            "detail": p["base_url"],
            "slug": p["slug"],
        }
        for p in providers
    ]
    chosen = pick("Select a provider to sync", options, allow_filter=False)
    return chosen["slug"] if chosen else None


def cmd_sync(args: argparse.Namespace) -> None:
    """Sync a provider to agents."""
    from apm.sync import print_sync_results, sync_provider

    provider_name = getattr(args, "provider", None)
    if not provider_name:
        provider_name = _pick_configured_provider()
        if not provider_name:
            return

    agents = None
    if args.agents:
        agents = [a.strip() for a in args.agents.split(",")]
    results = sync_provider(provider_name, agents, args.dry_run)
    print_sync_results(results, args.dry_run)


def cmd_switch(args: argparse.Namespace) -> None:
    """Switch all agents to a provider (alias for sync)."""
    cmd_sync(args)


def cmd_update(_args: argparse.Namespace) -> None:
    """Update registry from remote."""
    from apm.registry import update_registry
    update_registry()


def cmd_self_update(_args: argparse.Namespace) -> None:
    """Update apm itself."""
    from apm.updater import self_update
    self_update()


def cmd_doctor(args: argparse.Namespace) -> None:
    """Run diagnostics."""
    from apm.doctor import run_diagnostics
    run_diagnostics(fix=args.fix)


def cmd_logs(args: argparse.Namespace) -> None:
    """Show log file."""
    from apm.logging import get_log_file, tail_logs

    n = getattr(args, "tail", 20)
    lines = tail_logs(n)
    if not lines:
        print(f"  No logs yet. Log file: {get_log_file()}")
        return
    print(f"\n  Last {len(lines)} lines from {get_log_file()}:\n")
    for line in lines:
        print(f"  {line}")
    print()


def cmd_agents(_args: argparse.Namespace) -> None:
    """List known agents from registry."""
    from apm.registry import print_agents
    print_agents()


def cmd_providers(_args: argparse.Namespace) -> None:
    """List known providers from registry."""
    from apm.registry import print_providers
    print_providers()


def cmd_snapshot(args: argparse.Namespace) -> None:
    """Snapshot management subcommands."""
    from apm.snapshot import (
        delete_snapshot,
        print_restore_result,
        print_save_result,
        print_snapshots,
        restore_snapshot,
        save_snapshot,
    )

    sub = args.subcommand
    if not sub:
        print("  Usage: apm snapshot <subcommand>")
        print("  Subcommands: save, restore, list, delete")
        return

    if sub == "save":
        agents = None
        if hasattr(args, "agents") and args.agents:
            agents = [a.strip() for a in args.agents.split(",")]
        name = getattr(args, "name", None)
        result = save_snapshot(name=name, agents=agents)
        print_save_result(result)
    elif sub == "restore":
        if not hasattr(args, "name") or not args.name:
            print("  Usage: apm snapshot restore <name> [--agents a1,a2]")
            return
        agents = None
        if hasattr(args, "agents") and args.agents:
            agents = [a.strip() for a in args.agents.split(",")]
        result = restore_snapshot(args.name, agents=agents)
        print_restore_result(result)
    elif sub == "list":
        if getattr(args, "json", False):
            import json

            from apm.snapshot import list_snapshots
            print(json.dumps(list_snapshots(), ensure_ascii=False))
        else:
            print_snapshots()
    elif sub == "delete":
        if not hasattr(args, "name") or not args.name:
            print("  Usage: apm snapshot delete <name>")
            return
        if delete_snapshot(args.name):
            print(f"  Deleted snapshot: {args.name}")
        else:
            print(f"  Snapshot not found: {args.name}")


def cmd_init(_args: argparse.Namespace) -> None:
    """Interactive setup guide."""
    from apm.colors import bold, cyan, green, yellow
    from apm.detect import detect_all
    from apm.registry import list_providers as list_registry_providers

    print(f"\n  {bold('Agent Provider Manager — Setup')}")
    print("  " + "=" * 40)

    # Step 1: Scan agents
    print(f"\n  {cyan('Step 1:')} Scanning installed agents...")
    results = detect_all()
    installed = [r for r in results if r["installed"]]
    print(f"  Found {green(str(len(installed)))} installed agents:")
    for r in installed:
        print(f"    ✓ {r['name']}")
    if not installed:
        print(f"  {yellow('No agents found.')} Install an AI coding agent first.")
        return

    # Step 2: Choose provider (interactive menu)
    print(f"\n  {cyan('Step 2:')} Choose a provider")
    result = _pick_provider_from_registry()
    if not result:
        print("  Setup cancelled.")
        return
    provider_slug, variant = result
    providers = list_registry_providers()

    # Step 3: API key
    print(f"\n  {cyan('Step 3:')} Enter your API key for {bold(providers[provider_slug]['name'])}")
    try:
        key = getpass.getpass("  API key (hidden): ")
    except (EOFError, KeyboardInterrupt):
        print("\n  Setup cancelled.")
        return
    if not key.strip():
        print("  No key provided. Setup cancelled.")
        return

    # Step 4: Add & sync
    from apm.providers import add
    from apm.registry import resolve_provider
    resolved = resolve_provider(provider_slug, key, variant=variant)
    if resolved:
        slug = add(
            resolved["name"], resolved["base_url"], key,
            resolved["protocol"], resolved.get("models", []),
            anthropic_base_url=resolved.get("anthropic_base_url"),
            model_meta=resolved.get("_model_meta"),
        )
        print(f"\n  {green('✓')} Provider added: {bold(slug)}")

        print(f"\n  {cyan('Step 4:')} Syncing to all agents...")
        from apm.sync import print_sync_results, sync_provider
        results = sync_provider(slug)
        print_sync_results(results)
    else:
        print(f"  Failed to resolve provider. Try {cyan('apm provider add')} manually.")

    print(f"  {bold('Setup complete!')} Run {cyan('apm status')} to check.")
    print()


def cmd_undo(_args: argparse.Namespace) -> None:
    """Undo the last sync by restoring the most recent auto-snapshot."""
    from apm.colors import bold, green, red
    from apm.snapshot import list_snapshots, print_restore_result, restore_snapshot

    snapshots = list_snapshots()
    auto_snaps = [s for s in snapshots if s["name"].startswith("auto-pre-sync-")]
    if not auto_snaps:
        print(f"  {red('✗')} No auto-snapshots found. Nothing to undo.")
        return

    latest = auto_snaps[0]  # Already sorted by reverse time
    print(f"  Restoring from: {bold(latest['name'])}")
    print(f"  Created at: {latest['created_at'][:19]}")
    print(f"  Agents: {', '.join(latest['agents'])}")

    try:
        answer = input("\n  Restore? [y/N] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\n  Cancelled.")
        return

    if answer not in ("y", "yes"):
        print("  Cancelled.")
        return

    result = restore_snapshot(latest["name"])
    print_restore_result(result)
    print(f"  {green('✓')} Undo complete.")


def cmd_version(_args: argparse.Namespace) -> None:
    """Print version."""
    print(f"apm {__version__}")


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="apm",
        description="Agent Provider Manager — centralized API provider management",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument(
        "--json", action="store_true", help="JSON output (for GUI/scripts)"
    )
    parser.add_argument("-V", "--version", action="version", version=f"apm {__version__}")

    sub = parser.add_subparsers(dest="command")

    # scan
    sub.add_parser("scan", help="Scan installed agents")

    # status
    sub.add_parser("status", help="Show current provider status")

    # doctor
    p_doctor = sub.add_parser("doctor", help="Diagnose and fix issues")
    p_doctor.add_argument("--fix", action="store_true", help="Auto-fix issues")

    # provider
    p_prov = sub.add_parser("provider", help="Manage providers")
    prov_sub = p_prov.add_subparsers(dest="subcommand")

    # provider add
    p_add = prov_sub.add_parser("add", help="Add a provider")
    p_add.add_argument("name", nargs="?", help="Provider name (interactive if omitted)")
    p_add.add_argument("--key", help="API key (DEPRECATED: use --key-env or interactive prompt)")
    p_add.add_argument("--key-env", help="Read API key from this env var")
    p_add.add_argument("--url", help="Base URL (OpenAI-compatible endpoint)")
    p_add.add_argument("--anthropic-url", help="Anthropic-compatible endpoint URL")
    p_add.add_argument("--variant", help="Provider variant (e.g. token-plan-cn, api)")
    p_add.add_argument("--protocol", default="openai-compatible")
    p_add.add_argument("--models", help="Comma-separated model names")
    p_add.add_argument("--alias", help="Custom slug/alias for the provider")

    # provider update
    p_upd = prov_sub.add_parser("update", help="Update a provider's config")
    p_upd.add_argument("name", help="Provider slug to update")
    p_upd.add_argument("--url", help="New OpenAI-compatible base URL")
    p_upd.add_argument(
        "--anthropic-url", help="New Anthropic URL (empty to remove)"
    )
    p_upd.add_argument("--key", help="New API key")
    p_upd.add_argument("--key-env", help="Read new API key from env var")
    p_upd.add_argument("--models", help="Comma-separated model names")
    p_upd.add_argument("--rename", help="Rename provider slug")

    # provider remove
    p_rm = prov_sub.add_parser("remove", help="Remove a provider")
    p_rm.add_argument("name")

    # provider list
    prov_sub.add_parser("list", help="List configured providers")

    # provider show
    p_show = prov_sub.add_parser("show", help="Show provider details")
    p_show.add_argument("name")

    # provider import
    p_import = prov_sub.add_parser("import", help="Import from installed agents")
    p_import.add_argument("--agents", help="Comma-separated agent names")

    # provider known
    prov_sub.add_parser("known", help="List known providers from registry")

    # provider rename
    p_rename = prov_sub.add_parser("rename", help="Rename a provider slug")
    p_rename.add_argument("old_name", help="Current provider slug")
    p_rename.add_argument("new_name", help="New slug")

    # provider test
    p_test = prov_sub.add_parser("test", help="Test provider connectivity")
    p_test.add_argument("name", nargs="?", help="Provider name (tests all if omitted)")

    # provider models
    p_models = prov_sub.add_parser("models", help="Fetch available models from provider")
    p_models.add_argument("name", help="Provider name")

    # sync
    p_sync = sub.add_parser("sync", help="Sync provider to agents")
    p_sync.add_argument("provider", nargs="?", help="Provider name (interactive if omitted)")
    p_sync.add_argument("--agents", help="Comma-separated agent names")
    p_sync.add_argument("--dry-run", action="store_true", help="Preview changes")

    # switch (alias)
    p_switch = sub.add_parser("switch", help="Switch all agents to provider")
    p_switch.add_argument("provider", nargs="?", help="Provider name (interactive if omitted)")
    p_switch.add_argument("--agents", help="Comma-separated agent names")
    p_switch.add_argument("--dry-run", action="store_true", help="Preview changes")

    # update
    sub.add_parser("update", help="Update provider/agent registry")

    # self-update
    sub.add_parser("self-update", help="Update apm itself")

    # logs
    p_logs = sub.add_parser("logs", help="Show log file")
    p_logs.add_argument("--tail", type=int, default=20, help="Number of lines")

    # agents
    sub.add_parser("agents", help="List known agents from registry")

    # providers (registry)
    sub.add_parser("providers", help="List known providers from registry")

    # init
    sub.add_parser("init", help="Interactive setup guide")

    # undo
    sub.add_parser("undo", help="Undo last sync (restore auto-snapshot)")

    # snapshot
    p_snap = sub.add_parser("snapshot", help="Save/restore agent configs")
    snap_sub = p_snap.add_subparsers(dest="subcommand")

    # snapshot save
    p_snap_save = snap_sub.add_parser("save", help="Save current configs as snapshot")
    p_snap_save.add_argument("--name", help="Snapshot name (default: timestamp)")
    p_snap_save.add_argument("--agents", help="Comma-separated agent names")

    # snapshot restore
    p_snap_restore = snap_sub.add_parser("restore", help="Restore configs from snapshot")
    p_snap_restore.add_argument("name", help="Snapshot name")
    p_snap_restore.add_argument("--agents", help="Comma-separated agent names")

    # snapshot list
    snap_sub.add_parser("list", help="List saved snapshots")

    # snapshot delete
    p_snap_del = snap_sub.add_parser("delete", help="Delete a snapshot")
    p_snap_del.add_argument("name", help="Snapshot name")

    return parser


def main(argv: list[str] | None = None) -> None:
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    # Setup logging
    setup_logging(debug=args.debug)

    if not args.command:
        parser.print_help()
        return

    commands = {
        "scan": cmd_scan,
        "status": cmd_status,
        "doctor": cmd_doctor,
        "provider": cmd_provider,
        "sync": cmd_sync,
        "switch": cmd_switch,
        "update": cmd_update,
        "self-update": cmd_self_update,
        "logs": cmd_logs,
        "agents": cmd_agents,
        "providers": cmd_providers,
        "snapshot": cmd_snapshot,
        "init": cmd_init,
        "undo": cmd_undo,
        "version": cmd_version,
    }

    handler = commands.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
