#!/usr/bin/env bash
set -euo pipefail

# ACO Model installer for macOS and Linux
#
# Usage:
#   ./install.sh                  # clone into current directory
#   ./install.sh ~/projects/aco   # clone into specified directory
#
# Remote one-liner:
#   bash <(curl -sSL https://raw.githubusercontent.com/mukor/aco_model/main/install.sh)
#   bash <(curl -sSL https://raw.githubusercontent.com/mukor/aco_model/main/install.sh) ~/my/path

REPO_URL="${ACO_REPO_URL:-git@github.com:mukor/aco_model.git}"
INSTALL_DIR="${1:-${ACO_INSTALL_DIR:-$(pwd)/aco_model}}"
VENV_NAME="aco_model"
PYTHON_MIN="3.10"

# ── Colors ────────────────────────────────────────────────────────────────

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info()  { echo -e "${BLUE}[info]${NC}  $1"; }
ok()    { echo -e "${GREEN}[ok]${NC}    $1"; }
warn()  { echo -e "${YELLOW}[warn]${NC}  $1"; }
fail()  { echo -e "${RED}[error]${NC} $1"; exit 1; }

# ── Check Python ──────────────────────────────────────────────────────────

find_python() {
    for cmd in python3 python; do
        if command -v "$cmd" &>/dev/null; then
            if "$cmd" -c "import sys; exit(0 if sys.version_info >= (3,10) else 1)" 2>/dev/null; then
                echo "$cmd"
                return 0
            fi
        fi
    done
    return 1
}

info "Checking Python..."
PYTHON=$(find_python) || fail "Python ${PYTHON_MIN}+ is required. Install it from https://www.python.org or your package manager."
PYTHON_VER=$("$PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")
ok "Found $PYTHON ($PYTHON_VER)"

# ── Check git ─────────────────────────────────────────────────────────────

command -v git &>/dev/null || fail "git is required. Install it first."

# ── Check virtualenvwrapper ───────────────────────────────────────────────

USE_VENVWRAPPER=false
if command -v mkvirtualenv &>/dev/null; then
    USE_VENVWRAPPER=true
    ok "virtualenvwrapper found"
elif [ -n "${WORKON_HOME:-}" ] && [ -f "${VIRTUALENVWRAPPER_SCRIPT:-/dev/null}" ]; then
    # shellcheck disable=SC1090
    source "$VIRTUALENVWRAPPER_SCRIPT"
    USE_VENVWRAPPER=true
    ok "virtualenvwrapper found (sourced)"
else
    warn "virtualenvwrapper not found — will use plain venv instead"
    warn "Install it later: pip install virtualenvwrapper"
fi

# ── Clone or update repo ─────────────────────────────────────────────────

info "Install directory: $INSTALL_DIR"

if [ -d "$INSTALL_DIR/.git" ]; then
    info "Repository exists, pulling latest..."
    git -C "$INSTALL_DIR" pull --ff-only || warn "Pull failed — continuing with existing code"
    ok "Updated"
elif [ -d "$INSTALL_DIR" ] && [ "$(ls -A "$INSTALL_DIR" 2>/dev/null)" ]; then
    fail "$INSTALL_DIR exists and is not empty. Remove it or choose a different path."
else
    info "Cloning to $INSTALL_DIR..."
    mkdir -p "$(dirname "$INSTALL_DIR")"
    git clone "$REPO_URL" "$INSTALL_DIR"
    ok "Cloned"
fi

cd "$INSTALL_DIR"

# ── Create virtual environment ────────────────────────────────────────────

if [ "$USE_VENVWRAPPER" = true ]; then
    if workon "$VENV_NAME" 2>/dev/null; then
        ok "Activated existing virtualenv '$VENV_NAME'"
    else
        info "Creating virtualenv '$VENV_NAME'..."
        mkvirtualenv -p "$PYTHON" "$VENV_NAME"
        ok "Created virtualenv '$VENV_NAME'"
    fi
    setvirtualenvproject
else
    if [ -d ".venv" ]; then
        ok "Existing .venv found"
    else
        info "Creating .venv..."
        "$PYTHON" -m venv .venv
        ok "Created .venv"
    fi
    # shellcheck disable=SC1091
    source .venv/bin/activate
fi

# ── Install ───────────────────────────────────────────────────────────────

info "Installing dependencies..."
pip install --upgrade pip -q
pip install -e ".[dev,notebook]" -q
ok "Installed aco-model with dev + notebook extras"

# ── Verify ────────────────────────────────────────────────────────────────

info "Running tests..."
if pytest -q 2>/dev/null; then
    ok "All tests passed"
else
    warn "Some tests failed — check output above"
fi

# ── Done ──────────────────────────────────────────────────────────────────

echo ""
echo -e "${GREEN}=== ACO Model installed ===${NC}"
echo ""
echo "  Project: $INSTALL_DIR"
if [ "$USE_VENVWRAPPER" = true ]; then
    echo "  Activate: workon $VENV_NAME"
else
    echo "  Activate: source $INSTALL_DIR/.venv/bin/activate"
fi
echo ""
echo "  Quick start:"
echo "    aco simulate           # run retention simulation"
echo "    aco revenue            # estimate revenue"
echo "    jupyter lab notebooks/ # interactive notebooks"
echo ""
