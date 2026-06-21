#!/usr/bin/env bash
# Install APM skill to all AI coding agents.
# Usage: bash install-skill.sh
set -euo pipefail

SKILL_SRC="$(cd "$(dirname "$0")" && pwd)"
SKILL_NAME="apm"
SKILL_FILE="$SKILL_SRC/SKILL.md"

if [ ! -f "$SKILL_FILE" ]; then
    echo "Error: SKILL.md not found in $SKILL_SRC"
    exit 1
fi

TARGETS=(
    "$HOME/.cursor/skills-cursor/$SKILL_NAME"
    "$HOME/.claude/skills/$SKILL_NAME"
    "$HOME/.codex/skills/$SKILL_NAME"
    "$HOME/.hermes/skills/$SKILL_NAME"
    "$HOME/.openclaw/skills/$SKILL_NAME"
    "$HOME/.pi/agent/skills/$SKILL_NAME"
    "$HOME/.omp/agent/skills/$SKILL_NAME"
    "$HOME/.agents/skills/$SKILL_NAME"
)

echo "APM Skill Installer"
echo "==================="
echo

# Step 1: Install apm CLI if not present
if ! command -v apm &>/dev/null; then
    echo "Installing apm CLI..."
    pip3 install -e "$SKILL_SRC" 2>/dev/null || pip install -e "$SKILL_SRC"
    echo "  ✓ apm CLI installed"
else
    echo "  ✓ apm CLI already installed ($(apm -V 2>/dev/null || echo 'unknown version'))"
fi

echo

# Step 2: Install skill to each agent
for target in "${TARGETS[@]}"; do
    parent="$(dirname "$target")"
    # Only install if the parent skills directory exists
    if [ -d "$parent" ]; then
        mkdir -p "$target"
        cp "$SKILL_FILE" "$target/SKILL.md"
        echo "  ✓ Installed to $target"
    else
        echo "  ⊘ Skipped $target (agent not found)"
    fi
done

echo
echo "Done. All agents with skill directories now have the APM skill."
echo "Run 'apm init' to get started."
