"""Interactive menu utilities — stdlib only, no curses."""

from __future__ import annotations

import sys


def _is_interactive() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def pick(
    title: str,
    options: list[dict],
    *,
    allow_filter: bool = True,
    key_field: str = "label",
    detail_field: str | None = "detail",
) -> dict | None:
    """Show a numbered list and let user pick one.

    Each option is a dict with at least ``key_field`` (display label).
    If ``detail_field`` is set and present, shows it below the label.

    Returns the chosen dict, or None on EOF/Ctrl-C.
    """
    if not _is_interactive():
        print("  Error: interactive mode required. Specify arguments directly, e.g.:")
        print("    apm sync <provider>")
        print("    apm provider add <name> --key-env VAR")
        return None
    if not options:
        print("  (no options available)")
        return None

    from apm.colors import bold, cyan, dim

    def _render(items: list[tuple[int, dict]]) -> None:
        print(f"\n  {bold(title)}")
        print("  " + "─" * 50)
        for idx, (orig_idx, opt) in enumerate(items, 1):
            label = opt[key_field]
            print(f"  {cyan(str(idx).rjust(3))}  {label}")
            if detail_field and opt.get(detail_field):
                print(f"       {dim(opt[detail_field])}")
        print()

    indexed = list(enumerate(options))  # [(orig_index, opt), ...]

    while True:
        _render(indexed)
        prompt = "  Enter number"
        if allow_filter and len(options) > 5:
            prompt += " or keyword to filter"
        prompt += f" (1-{len(indexed)}, q=quit): "

        try:
            raw = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return None

        if not raw or raw.lower() == "q":
            return None

        # Try as number first
        try:
            num = int(raw)
            if 1 <= num <= len(indexed):
                return indexed[num - 1][1]
            print(f"  ⚠ Please enter 1-{len(indexed)}")
            continue
        except ValueError:
            pass

        # Filter mode
        if allow_filter:
            keyword = raw.lower()
            matched = [
                (i, opt) for i, opt in enumerate(options)
                if keyword in opt[key_field].lower()
                or (detail_field and keyword in str(opt.get(detail_field, "")).lower())
            ]
            if not matched:
                print(f"  ⚠ No match for '{raw}', showing all")
                indexed = list(enumerate(options))
            elif len(matched) == 1:
                return matched[0][1]
            else:
                indexed = matched
        else:
            print(f"  ⚠ Invalid input: {raw}")


def confirm(prompt: str, default: bool = True) -> bool:
    """Ask a yes/no question. Returns bool."""
    if not _is_interactive():
        return default
    suffix = " [Y/n]: " if default else " [y/N]: "
    try:
        raw = input(f"  {prompt}{suffix}").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return default
    if not raw:
        return default
    return raw in ("y", "yes")


def prompt_input(label: str, default: str = "") -> str:
    """Prompt for a text value."""
    if not _is_interactive():
        return default
    suffix = f" [{default}]" if default else ""
    try:
        raw = input(f"  {label}{suffix}: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return default
    return raw or default
