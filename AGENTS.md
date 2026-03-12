# AGENTS.md

## Cursor Cloud specific instructions

### Overview

This is the **Master Developer Prompt Kit** — a single-service Python/FastAPI application that transforms meeting transcripts into structured engineering artifacts via the Anthropic Claude API. No database, Docker, or container orchestration is needed.

### Running services

- **FastAPI server**: `python3 -m uvicorn app:app --reload --host 0.0.0.0 --port 8000` (note: use `python3 -m uvicorn`, not bare `uvicorn`, as the latter may not be on PATH)
- **Health check**: `GET http://localhost:8000/health`
- The `/process` and `/process/stream` endpoints require `ANTHROPIC_API_KEY` to be set.

### Testing

- **Unit tests**: `python3 -m pytest tests/ -v` — runs offline, no API key needed.
- **CI checks**: `make ci` — validates the fixture and all JSON outputs in `outputs/`.
- **Mock CLI pipeline**: `MOCK_OUTPUT=1 ./run_master_dev.sh sample_transcript.txt` — runs the full pipeline without an API key using `outputs/sample.json` as mock output.
- **Validate a single output**: `python3 validate_output.py <path-to-output.json>`

### Key caveats

- There is no dedicated linter (e.g. ruff, flake8, pylint) configured in this repo. The CI target (`make ci`) runs JSON schema validation only.
- The `SERVER_API_KEY` env var is optional; when unset, all endpoints are open (suitable for local dev).
- The watcher (`python3 watcher.py`) is an optional background service; it is not required for the web UI or CLI to function.
