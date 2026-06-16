# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project does

Single-service Python 3.11+ tool that pipes meeting transcripts through Claude and returns a structured JSON "engineering package" with six views: `design_doc`, `pm_summary`, `actions`, `implementation_plan`, `code_suggestions`, and `agent_task_report`. The system prompt lives in `master_dev_prompt.txt` and is the core artifact — the rest of the code is scaffolding to invoke it and validate its output.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests (always use python3 -m pytest, not bare pytest)
python3 -m pytest tests/ -v

# Run a single test
python3 -m pytest tests/test_watcher.py::test_should_process_returns_true_for_new_txt -v

# Start dev server (requires ANTHROPIC_API_KEY)
python3 -m uvicorn app:app --reload --host 0.0.0.0 --port 8000

# CLI pipeline — live
./run_master_dev.sh sample_transcript.txt

# CLI pipeline — mock (no API key needed, emits outputs/sample.json)
./run_master_dev.sh sample_transcript.txt --mock
MOCK_OUTPUT=1 ./run_master_dev.sh sample_transcript.txt

# Validate a JSON output
python3 validate_output.py outputs/sample.json
make validate-file FILE=outputs/sample.json

# Batch process all transcripts/*.txt
./batch_run_master_dev.sh
./batch_run_master_dev.sh ./my_transcripts ./my_outputs

# Validate all outputs at once
make validate-outputs

# Full CI check (runs test-validator + validate-outputs)
make ci

# Autopilot watcher (processes any .txt dropped into transcripts/)
python3 watcher.py
python3 watcher.py --transcripts ./my-transcripts --outputs ./my-outputs
```

Shell scripts need `chmod +x` on first use.

## Architecture

Three entry points, one shared system prompt:

**`run_master_dev.sh` (CLI)**  
Concatenates `master_dev_prompt.txt` + the transcript + a closing `"""`, pipes it to `claude` (falls back to `codex exec`). Supports `--mock`/`MOCK_OUTPUT=1` to emit `outputs/sample.json` without any API call. Env vars `MAX_RETRIES`, `RETRY_DELAY_SECONDS`, and `MASTER_DEV_TIMEOUT_SECONDS` control retry behavior.

**`app.py` (FastAPI server)**  
- `POST /process` — synchronous: loads `master_dev_prompt.txt` once (cached in `_system_prompt`), calls `claude-sonnet-4-6` via the Anthropic SDK, parses and returns JSON.
- `POST /process/stream` — streaming variant using `client.messages.stream`, emits SSE chunks then a final `done` event.
- `GET /` — serves `static/index.html` (terminal-style paste UI).
- `GET /health` — liveness check.
- Optional auth: set `SERVER_API_KEY` env var; enforced via `X-Api-Key` header with `hmac.compare_digest`.

**`watcher.py` (autopilot)**  
Uses `watchdog` to monitor `transcripts/` for new `.txt` files. On creation it calls `process_transcript()` which shells out to `run_master_dev.sh`, writes stdout to `outputs/<name>.json`, and stderr to `outputs/<name>.log`. Files are skipped if a matching `.json` already exists.

## Output schema and validation

`validate_output.py` enforces the schema strictly:
- All top-level keys must be present exactly.
- Nine array fields must each have at least one item: `actions.items`, `implementation_plan.milestones`, `implementation_plan.tech_tasks`, `code_suggestions.snippets`, `agent_task_report.qualification_checks`, `agent_task_report.task_slides`, `agent_task_report.master_checklist`, `agent_task_report.review_checkpoints`, `agent_task_report.escalation_rules`.
- Enum fields must use exact values: `priority` (low/medium/high), `type` (feature/bug/infra/research/decision/follow-up), `area` (backend/frontend/infra/data/devops/testing), `complexity` (S/M/L), `result` (pass/fail), `status` (Done/In Progress/Blocked).

The fixture at `ci/fixtures/valid_output.json` is the canonical valid example used by `make test-validator`.

Batch output naming: successful runs → `outputs/<name>.json`; schema failures → `outputs/<name>.invalid.json`; `make validate-outputs` ignores `*.invalid.json`.

## CI

GitHub Actions (`.github/workflows/validate-master-dev-prompt.yml`) runs on PRs: batch-processes `transcripts/` in mock mode then validates the output with `validate_output.py`. No API key is needed in CI.
