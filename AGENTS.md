# AGENTS.md

## Cursor Cloud specific instructions

### Overview

This is a pure Python project (no Node.js, no Docker, no databases). It processes meeting transcripts through an LLM and produces structured JSON engineering artifacts. Four runtime modes exist: CLI scripts, FastAPI HTTP server, batch processor, and a filesystem watcher.

### Running services

- **FastAPI dev server**: `python3 -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload` (note: `uvicorn` alone may not be on `PATH`; always use `python3 -m uvicorn`)
- **Health check**: `curl http://localhost:8000/health` should return `{"status":"ok","prompt_loaded":true}`
- The `/process` and `/process/stream` endpoints require `ANTHROPIC_API_KEY` to call the real LLM. Without it, the server still starts and serves the web UI and health endpoint.

### Testing

- **Unit tests**: `python3 -m pytest tests/ -v` (5 tests covering the watcher module)
- **CI checks**: `make ci` (validates JSON fixtures and output files)
- **CLI mock mode**: `MOCK_OUTPUT=1 ./run_master_dev.sh sample_transcript.txt` — produces valid JSON output without needing any model CLI or API key
- **Validate any output**: `python3 validate_output.py <file.json>`

### Gotchas

- The `uvicorn` binary is not on `PATH` after `pip install`; use `python3 -m uvicorn` instead.
- Mock mode (`--mock` or `MOCK_OUTPUT=1`) is the recommended way to test CLI flows without an API key or model CLI installation.
- See `README.md` for full usage docs and `INSTALL.md` for model CLI installation instructions.
