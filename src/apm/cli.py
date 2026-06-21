"""apm — Agent Provider Manager CLI.

Centralized API provider management for AI coding agents.
Manage your API subscriptions and sync them to any agent with one command.

Usage:
    apm scan                                  Scan installed agents
    apm status                                Show current provider status

    apm provider add <name> --url <url> --key <key> [--models m1,m2]
    apm provider remove <name>
    apm provider list
    apm provider show <name>
    apm provider use <name>                   Set active provider

    apm sync <provider>                       Sync to all installed agents
    apm sync <provider> --agents a1,a2        Sync to specific agents
    apm sync <provider> --dry-run             Preview changes

    apm switch <provider>                     Alias for sync (all agents)
"""

from __future__ import annotations

import sys

from apm import __version__
from apm.detect import print_scan_results
from apm.providers import (
    add,
    print_detail,
    print_list,
    remove,
    set_active,
)
from apm.sync import print_status, print_sync_results, sync_provider


def cmd_scan(_args: list[str]) -> None:
    """Scan installed agents."""
    print_scan_results()


def cmd_status(_args: list[str]) -> None:
    """Show current provider status."""
    print_status()


def cmd_provider(args: list[str]) -> None:
    """Provider management subcommands."""
    if not args:
        print("  Usage: apm provider <subcommand>")
        print("  Subcommands: add, remove, list, show, use")
        return

    sub = args[0]
    rest = args[1:]

    if sub == "add":
        _cmd_provider_add(rest)
    elif sub == "remove":
        _cmd_provider_remove(rest)
    elif sub == "list":
        print_list()
    elif sub == "show":
        if not rest:
            print("  Usage: apm provider show <name>")
            return
        print_detail(rest[0])
    elif sub == "use":
        if not rest:
            print("  Usage: apm provider use <name>")
            return
        set_active(rest[0])
        print(f"  Active provider set to: {rest[0]}")
    else:
        print(f"  Unknown subcommand: {sub}")


def _cmd_provider_add(args: list[str]) -> None:
    """Add a new provider."""
    import argparse

    parser = argparse.ArgumentParser(prog="apm provider add", add_help=False)
    parser.add_argument("name")
    parser.add_argument("--url", required=True)
    parser.add_argument("--key", required=True)
    parser.add_argument("--protocol", default="openai-compatible")
    parser.add_argument("--models", default="")
    try:
        opts = parser.parse_args(args)
    except SystemExit:
        print("  Usage: apm provider add <name> --url <url> --key <key> [--protocol p] [--models m1,m2]")
        return
    models = [m.strip() for m in opts.models.split(",") if m.strip()]
    slug = add(opts.name, opts.url, opts.key, opts.protocol, models)
    print(f"  Added provider: {slug}")


def _cmd_provider_remove(args: list[str]) -> None:
    """Remove a provider."""
    if not args:
        print("  Usage: apm provider remove <name>")
        return
    try:
        remove(args[0])
        print(f"  Removed provider: {args[0]}")
    except ValueError as e:
        print(f"  Error: {e}")


def cmd_sync(args: list[str]) -> None:
    """Sync a provider to agents."""
    if not args:
        print("  Usage: apm sync <provider> [--agents a1,a2] [--dry-run]")
        return

    provider_name = args[0]
    agents: list[str] | None = None
    dry_run = False

    i = 1
    while i < len(args):
        if args[i] == "--agents" and i + 1 < len(args):
            agents = [a.strip() for a in args[i + 1].split(",")]
            i += 2
        elif args[i] == "--dry-run":
            dry_run = True
            i += 1
        else:
            i += 1

    results = sync_provider(provider_name, agents, dry_run)
    print_sync_results(results, dry_run)


def cmd_switch(args: list[str]) -> None:
    """Switch all agents to a provider (alias for sync)."""
    cmd_sync(args)


def cmd_version(_args: list[str]) -> None:
    """Print version."""
    print(f"apm {__version__}")


def cmd_help(_args: list[str]) -> None:
    """Print help."""
    print(__doc__)


def main(argv: list[str] | None = None) -> None:
    """Main entry point."""
    args = argv if argv is not None else sys.argv[1:]

    if not args:
        cmd_help([])
        return

    cmd = args[0]
    rest = args[1:]

    commands = {
        "scan": cmd_scan,
        "status": cmd_status,
        "provider": cmd_provider,
        "sync": cmd_sync,
        "switch": cmd_switch,
        "version": cmd_version,
        "help": cmd_help,
        "--help": cmd_help,
        "-h": cmd_help,
        "--version": cmd_version,
        "-V": cmd_version,
    }

    handler = commands.get(cmd)
    if handler:
        handler(rest)
    else:
        print(f"  Unknown command: {cmd}")
        print("  Run 'apm --help' for usage.")
        sys.exit(1)


if __name__ == "__main__":
    main()
