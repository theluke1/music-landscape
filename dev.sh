#!/usr/bin/env bash
# dev.sh — start the full Harmonic Landscape stack
#
# Usage (from the project root):
#   ./dev.sh
#
# What it does:
#   1. Creates backend/.venv and installs Python deps on first run
#   2. Starts uvicorn (backend) on port 8000 in the background
#   3. Installs frontend npm deps on first run
#   4. Starts Vite (frontend) and opens the browser automatically
#   5. Ctrl+C kills both servers cleanly

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$ROOT/backend/.venv"
BACKEND_PORT=8000

# ── colours ────────────────────────────────────────────────────────────────
BOLD="\033[1m"; RESET="\033[0m"; DIM="\033[2m"; GREEN="\033[32m"; YELLOW="\033[33m"
info()    { echo -e "${BOLD}$*${RESET}"; }
success() { echo -e "${GREEN}✓ $*${RESET}"; }
dim()     { echo -e "${DIM}$*${RESET}"; }

# ── cleanup on exit ─────────────────────────────────────────────────────────
BACKEND_PID=""
cleanup() {
    echo ""
    info "Shutting down…"
    [[ -n "$BACKEND_PID" ]] && kill "$BACKEND_PID" 2>/dev/null || true
    exit 0
}
trap cleanup INT TERM

# ── 1. Python venv ──────────────────────────────────────────────────────────
if [[ ! -d "$VENV" ]]; then
    info "First run: creating Python virtual environment…"
    python3 -m venv "$VENV"
fi

if [[ ! -f "$VENV/lib/python3.*/site-packages/fastapi/__init__.py" ]] 2>/dev/null || \
   [[ "$ROOT/backend/requirements.txt" -nt "$VENV/.installed" ]]; then
    info "Installing Python dependencies (this takes a few minutes the first time)…"
    "$VENV/bin/pip" install --quiet --upgrade pip
    "$VENV/bin/pip" install --quiet -r "$ROOT/backend/requirements.txt"
    touch "$VENV/.installed"
    success "Python deps installed"
fi

# ── 2. Backend ──────────────────────────────────────────────────────────────
info "Starting backend on port $BACKEND_PORT…"
(
    cd "$ROOT/backend"
    "$VENV/bin/uvicorn" api.server:app \
        --reload \
        --port "$BACKEND_PORT" \
        --log-level warning \
        2>&1 | sed "s/^/${DIM}[backend] ${RESET}/"
) &
BACKEND_PID=$!

# Wait for the health endpoint (max 10 s)
dim "Waiting for backend…"
for _ in $(seq 1 20); do
    if curl -sf "http://localhost:$BACKEND_PORT/health" >/dev/null 2>&1; then
        success "Backend ready"
        break
    fi
    sleep 0.5
done

# ── 3. Frontend npm deps ─────────────────────────────────────────────────────
if [[ ! -d "$ROOT/frontend/node_modules" ]]; then
    info "First run: installing frontend dependencies…"
    (cd "$ROOT/frontend" && npm install --silent)
    success "Frontend deps installed"
fi

# ── 4. Frontend dev server (foreground — blocks until Ctrl+C) ───────────────
info "Starting frontend…"
cd "$ROOT/frontend"
npm run dev -- --open --port 5173
