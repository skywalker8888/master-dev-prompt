#!/bin/bash
# ─────────────────────────────────────────────
# run_master_dev.sh
# Usage: ./run_master_dev.sh transcript.txt
# Or:    ./run_master_dev.sh transcript.txt > output.json
# ─────────────────────────────────────────────

set -euo pipefail

SCRIPT_DIR="$(dirname "$0")"
PROMPT_FILE="$SCRIPT_DIR/master_dev_prompt.txt"
TRANSCRIPT_FILE="${1:-}"
MOCK_FLAG="${2:-}"
MAX_RETRIES="${MAX_RETRIES:-3}"
RETRY_DELAY_SECONDS="${RETRY_DELAY_SECONDS:-2}"
MASTER_DEV_TIMEOUT_SECONDS="${MASTER_DEV_TIMEOUT_SECONDS:-0}"

if [ -z "$TRANSCRIPT_FILE" ]; then
  echo "Usage: ./run_master_dev.sh <transcript.txt>"
  exit 1
fi

if [ ! -f "$TRANSCRIPT_FILE" ]; then
  echo "Error: transcript file '$TRANSCRIPT_FILE' not found"
  exit 1
fi

if [ ! -f "$PROMPT_FILE" ]; then
  echo "Error: master_dev_prompt.txt not found alongside this script"
  exit 1
fi

# Mock mode: if second arg is "--mock" or env MOCK_OUTPUT is set, emit the
# pre-generated `outputs/sample.json` (useful when model CLIs aren't installed).
if [ "$MOCK_FLAG" = "--mock" ] || [ "${MOCK_OUTPUT:-}" = "1" ]; then
  SAMPLE_JSON="$SCRIPT_DIR/outputs/sample.json"
  if [ -f "$SAMPLE_JSON" ]; then
    cat "$SAMPLE_JSON"
    exit 0
  else
    echo "Error: mock output requested but '$SAMPLE_JSON' not found" >&2
    exit 2
  fi
fi

# Build full prompt payload
build_payload() {
  cat "$PROMPT_FILE"
  python3 - "$TRANSCRIPT_FILE" "$SCRIPT_DIR" <<'PY'
import sys
from pathlib import Path

try:
    sys.path.insert(0, sys.argv[2])
    from transcript_sanitizer import sanitize_transcript
except Exception as exc:
    print(f"Error: failed to load transcript sanitizer: {exc}", file=sys.stderr)
    sys.exit(2)

try:
    raw_transcript = Path(sys.argv[1]).read_text()
except Exception as exc:
    print(f"Error: failed to read transcript file: {exc}", file=sys.stderr)
    sys.exit(2)

print(sanitize_transcript(raw_transcript), end="")
PY
  echo ""
  echo '"""'
}

TIMEOUT_BIN=""
if [ "$MASTER_DEV_TIMEOUT_SECONDS" -gt 0 ]; then
  if command -v timeout >/dev/null 2>&1; then
    TIMEOUT_BIN="timeout"
  elif command -v gtimeout >/dev/null 2>&1; then
    TIMEOUT_BIN="gtimeout"
  else
    echo "Warning: MASTER_DEV_TIMEOUT_SECONDS is set but no timeout command found." >&2
  fi
fi

BACKEND=""
if command -v claude >/dev/null 2>&1; then
  BACKEND="claude"
elif command -v codex >/dev/null 2>&1; then
  BACKEND="codex"
fi

if [ -z "$BACKEND" ]; then
  echo "Error: neither 'claude' nor 'codex' CLI is installed."
  echo "Install Claude Code CLI, or install/login to Codex CLI and rerun."
  exit 1
fi

run_once() {
  if [ "$BACKEND" = "claude" ]; then
    if [ -n "$TIMEOUT_BIN" ]; then
      build_payload | "$TIMEOUT_BIN" "$MASTER_DEV_TIMEOUT_SECONDS" claude
    else
      build_payload | claude
    fi
  else
    # codex exec reads prompt from stdin when "-" is used as PROMPT.
    if [ -n "$TIMEOUT_BIN" ]; then
      build_payload | "$TIMEOUT_BIN" "$MASTER_DEV_TIMEOUT_SECONDS" codex exec --skip-git-repo-check -
    else
      build_payload | codex exec --skip-git-repo-check -
    fi
  fi
}

attempt=1
while [ "$attempt" -le "$MAX_RETRIES" ]; do
  if run_once; then
    exit 0
  else
    status=$?
  fi

  if [ "$attempt" -lt "$MAX_RETRIES" ]; then
    echo "Attempt $attempt/$MAX_RETRIES failed with exit code $status; retrying in ${RETRY_DELAY_SECONDS}s..." >&2
    sleep "$RETRY_DELAY_SECONDS"
  fi
  attempt=$((attempt + 1))
done

echo "Error: all $MAX_RETRIES attempts failed." >&2
exit 1
