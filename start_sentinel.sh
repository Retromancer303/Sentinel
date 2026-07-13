#!/usr/bin/env bash
# Sentinel launcher — macOS / Linux
# Detects Python, sets up the virtual environment, installs deps, and starts the backend.
set -e

# ── Resolve project root ────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# ── Find Python 3 ───────────────────────────────────────────────────────────
if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    echo "ERROR: Python 3 not found. Install it from https://python.org"
    exit 1
fi

# ── Set up virtual environment if needed ─────────────────────────────────────
VENV_DIR="$SCRIPT_DIR/.venv"
VENV_PYTHON="$VENV_DIR/bin/python"

if [ ! -f "$VENV_PYTHON" ]; then
    echo "Creating virtual environment..."
    "$PYTHON" -m venv "$VENV_DIR"
fi

# ── Install dependencies if needed ──────────────────────────────────────────
REQ_FILE="$SCRIPT_DIR/risk-engine/requirements.txt"
if [ ! -f "$VENV_DIR/.deps-installed" ]; then
    echo "Installing Python dependencies..."
    "$VENV_PYTHON" -m pip install -r "$REQ_FILE" --quiet
    touch "$VENV_DIR/.deps-installed"
fi

# ── Set environment variables for Ollama ─────────────────────────────────────
export AI_PROVIDER="${AI_PROVIDER:-ollama}"
export OLLAMA_MODEL="${OLLAMA_MODEL:-llama3:latest}"
export OLLAMA_HOST="${OLLAMA_HOST:-http://localhost:11434}"
export REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"

# ── Stop any existing Sentinel backend ──────────────────────────────────────
pkill -f "uvicorn app.main:app" 2>/dev/null && sleep 1 || true

# ── Start backend ───────────────────────────────────────────────────────────
echo "Starting Sentinel backend..."
echo "AI Provider: $AI_PROVIDER"
echo "Ollama: $OLLAMA_HOST / $OLLAMA_MODEL"

cd "$SCRIPT_DIR/risk-engine"
"$VENV_PYTHON" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# ── Wait for backend to be ready ────────────────────────────────────────────
echo -n "Waiting for backend..."
for i in $(seq 1 30); do
    if curl -s http://127.0.0.1:8000/ > /dev/null 2>&1; then
        echo " ready."
        break
    fi
    sleep 1
    echo -n "."
done

# ── Open the frontend ───────────────────────────────────────────────────────
FRONTEND_PATH="$SCRIPT_DIR/frontend/index.html"
if command -v open &>/dev/null; then
    open "$FRONTEND_PATH"        # macOS
elif command -v xdg-open &>/dev/null; then
    xdg-open "$FRONTEND_PATH"    # Linux
fi

echo "Backend running on http://127.0.0.1:8000"
echo "Press Ctrl+C to stop."

# ── Keep running until interrupted ──────────────────────────────────────────
wait $BACKEND_PID
