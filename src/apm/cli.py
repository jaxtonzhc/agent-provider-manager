"""Agent Provider Manager — CLI.

Centralized API provider management for AI coding agents.
Manage your API subscriptions and sync them to any agent with one command.

Usage:
    apm scan                                  Scan installed agents
    apm status                                Show current provider status
    apm doctor [--fix]                        Diagnose and fix issues

    apm provider add <name> [--key <key>] [--url <url>] [--models m1,m2]
    apm provider remove <name>
    apm provider list
    apm provider show <name>
    apm provider use <name>
    apm provider import                       Import from installed agents

    apm sync <provider>                       Sync to all installed agents
    apm sync <provider> --agents a1,a2        Sync to specific agents
    apm sync <provider> --dry-run             Preview changes

    apm switch <provider>                     Alias for sync (all agents)

    apm update                                Update provider/agent registry
    apm self-update                           Update apm itself
    apm logs [--tail N]                       Show log file
    apm agents                                List known agents
    apm providers                             List known providers (from registry)
"""

from __future__ import annotations

import argparse
import sys

from apm import __version__
from apm.logging import setup_logging


def cmd_scan(_args: argparse.Namespace) -> None:
    """Scan installed agents."""
    from apm.detect import print_scan_results
    print_scan_results()


def cmd_status(_args: argparse.Namespace) -> None:
    """Show current provider status."""
    from apm.sync import print_status
    print_status()


def cmd_provider(args: argparse.Namespace) -> None:
    """Provider management subcommands."""
    sub = args.subcommand
    if not sub:
        print("  Usage: apm provider <subcommand>")
        print("  Subcommands: add, remove, list, show, use, import")
        return

    if sub == "add":
        _cmd_provider_add(args)
    elif sub == "remove":
        _cmd_provider_remove(args)
    elif sub == "list":
        from apm.providers import print_list
        print_list()
    elif sub == "show":
        from apm.providers import print_detail
        print_detail(args.name)
    elif sub == "use":
        from apm.providers import set_active
        set_active(args.name)
        print(f"  Active provider set to: {args.name}")
    elif sub == "import":
        _cmd_provider_import(args)
    elif sub == "known":
        from apm.registry import print_providers
        print_providers()


def _cmd_provider_add(args: argparse.Namespace) -> None:
    """Add a new provider."""
    from apm.providers import add
    from apm.registry import resolve_provider

    name = args.name
    key = args.key
    if not key:
        print("  Error: --key is required")
        print("  Usage: apm provider add <name> --key <api-key> [--url <url>] [--variant v]")
        return

    variant = getattr(args, "variant", None)

    # Try to resolve from registry
    resolved = resolve_provider(name, key, variant=variant)
    if resolved:
        # Use registry info, allow overrides
        base_url = args.url or resolved["base_url"]
        protocol = args.protocol or resolved["protocol"]
        models = args.models or resolved.get("models", [])
        if isinstance(models, str):
            models = [m.strip() for m in models.split(",") if m.strip()]
        slug = add(resolved["name"], base_url, key, protocol, models)
        print(f"  Added provider: {slug}")
        print(f"    URL: {base_url}")
        print(f"    Protocol: {protocol}")
        if models:
            print(f"    Models: {', '.join(models[:5])}")

        # Show available variants if any
        variants = resolved.get("variants", {})
        if variants and not variant and len(variants) > 1:
            print(f"\n  Available variants (use --variant to select):")
            for vname, vinfo in variants.items():
                print(f"    {vname:<20} {vinfo['base_url']}")
    else:
        # Custom provider
        if not args.url:
            print(f"  Error: '{name}' not found in registry. Use --url for custom providers.")
            print("  Run 'apm providers' to see available providers.")
            return
        models = []
        if args.models:
            models = [m.strip() for m in args.models.split(",") if m.strip()]
        slug = add(name, args.url, key, args.protocol or "openai-compatible", models)
        print(f"  Added provider: {slug}")


def _cmd_provider_remove(args: argparse.Namespace) -> None:
    """Remove a provider."""
    from apm.providers import remove
    try:
        remove(args.name)
        print(f"  Removed provider: {args.name}")
    except ValueError as e:
        print(f"  Error: {e}")


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
        icon = {"imported": "✓", "exists": "⊘", "error": "✗"}.get(r["status"], "?")
        print(f"  {icon}  {r['agent']:<15} → {r['provider'] or '(failed)'}")
    print()


def cmd_sync(args: argparse.Namespace) -> None:
    """Sync a provider to agents."""
    from apm.sync import print_sync_results, sync_provider

    agents = None
    if args.agents:
        agents = [a.strip() for a in args.agents.split(",")]
    results = sync_provider(args.provider, agents, args.dry_run)
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
        print_snapshots()
    elif sub == "delete":
        if not hasattr(args, "name") or not args.name:
            print("  Usage: apm snapshot delete <name>")
            return
        if delete_snapshot(args.name):
            print(f"  Deleted snapshot: {args.name}")
        else:
            print(f"  Snapshot not found: {args.name}")


def cmd_version(_args: argparse.Namespace) -> None:
    """Print version."""
    print(f"apm {__version__}")


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="apm",
        description="Agent Provider Manager — centralized API provider management for AI coding agents",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
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
    p_add.add_argument("name", help="Provider name (or registry slug)")
    p_add.add_argument("--key", required=True, help="API key")
    p_add.add_argument("--url", help="Base URL (auto-filled from registry if known)")
    p_add.add_argument("--variant", help="Provider variant (e.g. token-plan-cn, api)")
    p_add.add_argument("--protocol", default="openai-compatible")
    p_add.add_argument("--models", help="Comma-separated model names")

    # provider remove
    p_rm = prov_sub.add_parser("remove", help="Remove a provider")
    p_rm.add_argument("name")

    # provider list
    prov_sub.add_parser("list", help="List configured providers")

    # provider show
    p_show = prov_sub.add_parser("show", help="Show provider details")
    p_show.add_argument("name")

    # provider use
    p_use = prov_sub.add_parser("use", help="Set active provider")
    p_use.add_argument("name")

    # provider import
    p_import = prov_sub.add_parser("import", help="Import from installed agents")
    p_import.add_argument("--agents", help="Comma-separated agent names")

    # provider known
    prov_sub.add_parser("known", help="List known providers from registry")

    # sync
    p_sync = sub.add_parser("sync", help="Sync provider to agents")
    p_sync.add_argument("provider", help="Provider name")
    p_sync.add_argument("--agents", help="Comma-separated agent names")
    p_sync.add_argument("--dry-run", action="store_true", help="Preview changes")

    # switch (alias)
    p_switch = sub.add_parser("switch", help="Switch all agents to provider")
    p_switch.add_argument("provider", help="Provider name")
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
