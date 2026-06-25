# AGENTS.md

## Cursor Cloud specific instructions

This is a Python 3.11+ single-service monolithic app (FastAPI + CLI scripts) for processing meeting transcripts via LLM. No databases or containers required.

### Key commands

| Task | Command |
|------|---------|
| Install deps | `pip install -r requirements.txt` |
| Run tests | `python3 -m pytest tests/ -v` |
| Run CI checks | `make ci` |
| Start dev server | `python3 -m uvicorn app:app --reload --host 0.0.0.0 --port 8000` |
| Mock CLI pipeline | `./run_master_dev.sh sample_transcript.txt --mock` |
| Validate JSON | `python3 validate_output.py <file.json>` |

### Caveats

- Use `python3 -m pytest` rather than bare `pytest`; the latter may not be on PATH.
- The FastAPI server (`POST /process`) requires `ANTHROPIC_API_KEY` env var for live mode. Without it, the server starts but returns HTTP 500 on process requests. Mock mode (`--mock` flag or `MOCK_OUTPUT=1` env var) works without any API key for CLI scripts.
- Shell scripts (`run_master_dev.sh`, `batch_run_master_dev.sh`) must be `chmod +x` before first use.
- The web UI is a single static HTML file at `static/index.html`, served by FastAPI at `GET /`. It posts to `/process/stream`, so the browser UI also needs `ANTHROPIC_API_KEY` to produce results; without it the server returns HTTP 500.
- Health check: `GET /health` returns `{"status":"ok","prompt_loaded":true}`.
- The autopilot watcher (`watcher.py`) shells out to `run_master_dev.sh` without `--mock`, so to test it offline (no model CLI / no API key) run it with the mock env var: `MOCK_OUTPUT=1 python3 watcher.py`. Drop a `.txt` into `transcripts/` and a validated `.json` appears in `outputs/` (existing `.txt` files whose `.json` already exists are skipped).
- `pip install --user` puts console scripts (`uvicorn`, `pytest`) in `~/.local/bin`, which is not on PATH; this is why the `python3 -m ...` invocations above are used.
