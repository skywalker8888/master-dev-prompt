#!/bin/bash
# Run master prompt generation for every transcript and validate each JSON output.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNNER="$SCRIPT_DIR/run_master_dev.sh"
VALIDATOR="$SCRIPT_DIR/validate_output.py"

OBSIDIAN_VAULT_PATH="${OBSIDIAN_VAULT_PATH:-}"
OBSIDIAN_TRANSCRIPTS_SUBDIR="${OBSIDIAN_TRANSCRIPTS_SUBDIR:-transcripts}"
OBSIDIAN_OUTPUTS_SUBDIR="${OBSIDIAN_OUTPUTS_SUBDIR:-outputs}"

DEFAULT_TRANSCRIPTS_DIR="$SCRIPT_DIR/transcripts"
DEFAULT_OUTPUT_DIR="$SCRIPT_DIR/outputs"

if [ -n "${MASTER_DEV_TRANSCRIPTS_DIR:-}" ]; then
  DEFAULT_TRANSCRIPTS_DIR="${MASTER_DEV_TRANSCRIPTS_DIR}"
elif [ -n "$OBSIDIAN_VAULT_PATH" ]; then
  DEFAULT_TRANSCRIPTS_DIR="$OBSIDIAN_VAULT_PATH/$OBSIDIAN_TRANSCRIPTS_SUBDIR"
fi

if [ -n "${MASTER_DEV_OUTPUTS_DIR:-}" ]; then
  DEFAULT_OUTPUT_DIR="${MASTER_DEV_OUTPUTS_DIR}"
elif [ -n "$OBSIDIAN_VAULT_PATH" ]; then
  DEFAULT_OUTPUT_DIR="$OBSIDIAN_VAULT_PATH/$OBSIDIAN_OUTPUTS_SUBDIR"
fi

TRANSCRIPTS_DIR="${1:-$DEFAULT_TRANSCRIPTS_DIR}"
OUTPUT_DIR="${2:-$DEFAULT_OUTPUT_DIR}"
MOCK_FLAG="${3:-}"

if [ ! -x "$RUNNER" ]; then
  echo "Error: runner not executable: $RUNNER" >&2
  echo "Run: chmod +x $RUNNER" >&2
  exit 1
fi

if [ ! -f "$VALIDATOR" ]; then
  echo "Error: validator not found: $VALIDATOR" >&2
  exit 1
fi

if [ ! -d "$TRANSCRIPTS_DIR" ]; then
  echo "Error: transcripts directory not found: $TRANSCRIPTS_DIR" >&2
  exit 1
fi

mkdir -p "$OUTPUT_DIR"

transcript_files=()
while IFS= read -r file_path; do
  transcript_files+=("$file_path")
done < <(find "$TRANSCRIPTS_DIR" -type f -name "*.txt" | sort)

if [ "${#transcript_files[@]}" -eq 0 ]; then
  echo "Error: no .txt transcript files found in $TRANSCRIPTS_DIR" >&2
  exit 1
fi

pass_count=0
fail_count=0

for transcript in "${transcript_files[@]}"; do
  base_name="$(basename "$transcript" .txt)"
  output_json="$OUTPUT_DIR/${base_name}.json"
  output_tmp="$OUTPUT_DIR/${base_name}.tmp.json"
  output_log="$OUTPUT_DIR/${base_name}.log"

  rm -f "$output_tmp"

  echo "Processing: $transcript"
  # If batch mock requested, pass --mock to the runner (or set MOCK_OUTPUT=1)
  if [ "$MOCK_FLAG" = "--mock" ] || [ "${MOCK_OUTPUT:-}" = "1" ]; then
    if "$RUNNER" "$transcript" --mock >"$output_tmp" 2>"$output_log"; then
      runner_status=0
    else
      runner_status=$?
    fi
  else
    if "$RUNNER" "$transcript" >"$output_tmp" 2>"$output_log"; then
      runner_status=0
    else
      runner_status=$?
    fi
  fi

  if [ "$runner_status" -eq 0 ]; then
    if python3 "$VALIDATOR" "$output_tmp" >>"$output_log" 2>&1; then
      mv "$output_tmp" "$output_json"
      pass_count=$((pass_count + 1))
      echo "  PASS: $output_json"
    else
      mv "$output_tmp" "$OUTPUT_DIR/${base_name}.invalid.json"
      fail_count=$((fail_count + 1))
      echo "  FAIL (invalid JSON schema): $OUTPUT_DIR/${base_name}.invalid.json"
    fi
  else
    rm -f "$output_tmp"
    fail_count=$((fail_count + 1))
    echo "  FAIL (runner error): $transcript"
  fi
done

echo ""
echo "Summary: pass=$pass_count fail=$fail_count total=${#transcript_files[@]}"

if [ "$fail_count" -gt 0 ]; then
  exit 1
fi
