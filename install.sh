#!/usr/bin/env bash
#
# Agent Provider Manager — One-line installer
#
# Usage:
#   curl -sSL https://raw.githubusercontent.com/jaxtonzhc/agent-provider-manager/main/install.sh | bash
#
set -euo pipefail

REPO="jaxtonzhc/agent-provider-manager"
PACKAGE="agent-provider-manager"
BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "  ${GREEN}✓${NC} $*"; }
warn()  { echo -e "  ${YELLOW}⚠${NC} $*"; }
error() { echo -e "  ${RED}✗${NC} $*"; }

echo ""
echo -e "  ${BOLD}Agent Provider Manager — Installer${NC}"
echo "  ==================================="
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    error "Python 3 not found. Please install Python 3.9+ first."
    echo "  macOS:  brew install python3"
    echo "  Ubuntu: sudo apt install python3 python3-pip"
    exit 1
fi

PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)

if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 9 ]; }; then
    error "Python 3.9+ required, found $PY_VER"
    exit 1
fi
info "Python $PY_VER found"

# Install method preference: pipx > pip
install_with_pipx() {
    if command -v pipx &>/dev/null; then
        info "pipx found"
        pipx install "$PACKAGE" 2>/dev/null || pipx upgrade "$PACKAGE"
        return 0
    fi

    # Try to install pipx
    info "Installing pipx..."
    if command -v brew &>/dev/null; then
        brew install pipx
        pipx ensurepath
    elif command -v pip3 &>/dev/null; then
        python3 -m pip install --user pipx
        python3 -m pipx ensurepath
    else
        return 1
    fi

    if command -v pipx &>/dev/null; then
        pipx install "$PACKAGE"
        return 0
    fi
    return 1
}

install_with_pip() {
    info "Installing with pip..."
    python3 -m pip install --user "$PACKAGE"
}

# Check if already installed
if command -v apm &>/dev/null; then
    CURRENT=$(apm version 2>/dev/null | awk '{print $2}')
    warn "apm $CURRENT already installed"
    echo -n "  Upgrade? [y/N] "
    read -r answer
    if [[ ! "$answer" =~ ^[Yy]$ ]]; then
        echo "  Skipped."
        exit 0
    fi
fi

# Try installation
if install_with_pipx; then
    info "Installed with pipx"
elif install_with_pip; then
    info "Installed with pip"
else
    error "Installation failed"
    echo "  Try manually:"
    echo "    pip install $PACKAGE"
    echo "    pipx install $PACKAGE"
    exit 1
fi

# Verify
if command -v apm &>/dev/null; then
    echo ""
    info "Installation successful!"
    echo ""
    echo "  Get started:"
    echo "    apm scan              # Scan installed agents"
    echo "    apm provider add      # Add an API provider"
    echo "    apm status            # Show current status"
    echo ""
else
    warn "apm installed but not in PATH"
    echo "  Add to your shell profile:"
    echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
fi
