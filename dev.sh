#!/bin/bash
# ─────────────────────────────────────────────
# dev.sh
# One-command local dev launcher: installs deps into a venv and starts
# the FastAPI server (app.py) with auto-reload.
#
# Usage: ./dev.sh
#
# Env vars:
#   ANTHROPIC_API_KEY   required by app.py to call Claude (or set in .env)
#   SERVER_API_KEY       optional — require X-Api-Key header on requests
#   PORT                 default 8000
# ─────────────────────────────────────────────

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR="$SCRIPT_DIR/.venv"
PORT="${PORT:-8000}"

if [ ! -d "$VENV_DIR" ]; then
  echo "Creating virtualenv at $VENV_DIR..."
  python3 -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

echo "Installing dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

if [ -f .env ]; then
  echo "Loading environment from .env"
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
  echo "Warning: ANTHROPIC_API_KEY is not set. /process requests will fail until it is." >&2
fi

echo "Starting server on http://localhost:${PORT} (Ctrl+C to stop)..."
exec uvicorn app:app --reload --port "$PORT"
