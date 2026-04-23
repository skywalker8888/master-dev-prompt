# AGENTS.md

## Cursor Cloud specific instructions

### Project snapshot

- Python 3.11+ single-service app for processing meeting transcripts with LLM prompts.
- Main interfaces:
  - CLI scripts (`run_master_dev.sh`, `batch_run_master_dev.sh`)
  - FastAPI server (`app.py`)
  - File watcher (`watcher.py`)
- No database, container, or migration setup is required.

### Setup

1. Install dependencies:
   - `pip install -r requirements.txt`
2. Ensure scripts are executable (first run in fresh environments):
   - `chmod +x run_master_dev.sh batch_run_master_dev.sh`

### High-signal commands

| Task | Command |
|------|---------|
| Run tests | `python3 -m pytest tests/ -v` |
| Run a focused test file | `python3 -m pytest tests/test_watcher.py -v` |
| Run local CI-equivalent checks | `make ci` |
| Validate one output JSON | `python3 validate_output.py <file.json>` |
| Validate all outputs in `outputs/` | `make validate-outputs` |
| Run CLI pipeline in mock mode | `./run_master_dev.sh sample_transcript.txt --mock` |
| Run watcher | `python3 watcher.py` |
| Start FastAPI dev server | `python3 -m uvicorn app:app --reload --host 0.0.0.0 --port 8000` |

### Runtime behavior and caveats

- Use `python3 -m pytest` instead of plain `pytest` (PATH is not always reliable).
- `POST /process` and `POST /process/stream` require `ANTHROPIC_API_KEY` for live model calls.
- The server can still start without `ANTHROPIC_API_KEY`; process endpoints return HTTP 500 in that case.
- CLI mock mode requires either:
  - second arg `--mock`, or
  - env var `MOCK_OUTPUT=1`.
- Mock mode emits `outputs/sample.json` and does not need model CLI/API credentials.
- `run_master_dev.sh` auto-selects backend CLI:
  - prefers `claude`
  - falls back to `codex exec`.
- If `SERVER_API_KEY` is set, all API routes require matching `X-Api-Key` header.
- UI is static (`static/index.html`) served at `GET /`.
- Health endpoint: `GET /health` returns `{"status":"ok","prompt_loaded":true}` when prompt exists.

### Validation/testing expectations for agent edits

- For Python logic changes (`app.py`, `watcher.py`, validator logic), run targeted `python3 -m pytest ...` first, then broader checks if needed.
- For shell script changes, run at least one realistic command path (prefer mock mode for deterministic local verification).
- For API/UI changes, run server and verify:
  - `GET /health`
  - relevant endpoint behavior (`/process` or `/process/stream`)
  - browser UI flow if `static/index.html` changed.

### Key files

- `app.py` — FastAPI endpoints and server behavior.
- `run_master_dev.sh` — single transcript CLI runner with retries, timeout, and mock mode.
- `batch_run_master_dev.sh` — batch transcript processing helper.
- `watcher.py` — auto-process new transcript files.
- `validate_output.py` — strict JSON schema/enum validation.
- `tests/test_watcher.py` — current automated test coverage.
