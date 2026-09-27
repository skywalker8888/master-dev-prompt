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
| Run a focused test file | `python3 -m pytest tests/test_app.py -v` |
| Run local CI-equivalent checks | `make ci` |
| Validate one output JSON | `python3 validate_output.py <file.json>` |
| Validate all outputs in `outputs/` | `make validate-outputs` |
| Run CLI pipeline in mock mode | `./run_master_dev.sh sample_transcript.txt --mock` |
| Run watcher (offline) | `MOCK_OUTPUT=1 python3 watcher.py` |
| Start FastAPI dev server | `python3 -m uvicorn app:app --reload --host 0.0.0.0 --port 8000` |

### Runtime behavior and caveats

- Use `python3 -m pytest` / `python3 -m uvicorn` rather than bare `pytest` / `uvicorn`; `pip install --user` puts console scripts in `~/.local/bin`, which is not on PATH.
- `POST /process` and `POST /process/stream` use live Anthropic when `ANTHROPIC_API_KEY` is set. If the key is missing, or `MOCK_OUTPUT=1` is set, they return `outputs/sample.json` instead of HTTP 500 (so Vercel works before the key is configured).
- Model defaults to `claude-sonnet-5`; override with `ANTHROPIC_MODEL`.
- Health endpoint: `GET /health` returns `{"status":"ok","prompt_loaded":true,"mock":true|false}`.
- If `SERVER_API_KEY` is set, `POST /process` and `POST /process/stream` require a matching `X-Api-Key` header. `GET /` (UI) and `GET /health` stay public.
- UI is a single static file (`static/index.html`) served at `GET /`. It posts to `/process/stream`; in mock mode the header badge shows mock mode.
- CLI mock mode (`--mock` second arg or `MOCK_OUTPUT=1`) prints `outputs/sample.json` to stdout and needs no model CLI/API credentials.
- `run_master_dev.sh` auto-selects backend CLI: prefers `claude`, falls back to `codex exec`.
- The watcher shells out to `run_master_dev.sh` without `--mock`, so test it offline with `MOCK_OUTPUT=1`. Drop a `.txt` into `transcripts/` and a validated `.json` appears in `outputs/` (`.txt` files whose `.json` already exists are skipped).
- Cloud Agent start launches uvicorn on `0.0.0.0:8000` if `/health` is not already up, then returns. Re-running start is a no-op when the server is healthy.

### Validation/testing expectations for agent edits

- For Python logic changes (`app.py`, `watcher.py`, validator logic), run targeted `python3 -m pytest ...` first, then `make ci`.
- For shell script changes, run at least one realistic command path (prefer mock mode for deterministic local verification).
- For API/UI changes, run the server and verify:
  - `GET /health`
  - relevant endpoint behavior (`/process` or `/process/stream`)
  - browser UI flow if `static/index.html` changed.

### Key files

- `app.py` — FastAPI endpoints, mock fallback, model selection.
- `run_master_dev.sh` — single transcript CLI runner with retries, timeout, and mock mode.
- `batch_run_master_dev.sh` — batch transcript processing helper.
- `watcher.py` — auto-process new transcript files.
- `validate_output.py` — strict JSON schema/enum validation.
- `tests/test_app.py` — API, mock-mode, and model-default tests.
- `tests/test_watcher.py` — watcher tests.
