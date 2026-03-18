# Copilot Coding Agent Instructions

## About This Repository

This is the **Master Developer Prompt Kit** — a FastAPI backend that processes conversation transcripts through Claude to produce structured engineering artifacts (PRDs, architecture plans, task breakdowns, etc.).

## Coding Conventions

- **Python 3.11+** — use type hints, f-strings, and `asyncio` patterns throughout
- **FastAPI** for all HTTP endpoints; use `async def` handlers
- **Pydantic v2** for request/response models and validation
- **No implicit returns** — every function must have an explicit return type annotation
- Line length: 100 characters max
- Use `snake_case` for variables/functions, `PascalCase` for classes, `UPPER_SNAKE` for constants

## Project Structure

```
app.py                   # FastAPI application entry point
video_backend/           # T2V (text-to-video) generation subsystem
  adapters/              # Model-specific adapters (LTX-Video, Wan2.1, etc.)
  queue/                 # Async job queue for GPU-bound inference
  storage/               # Video file storage abstraction
static/                  # Frontend assets (served by FastAPI)
tests/                   # Pytest test suite (async-first)
```

## Key Patterns

- All GPU-bound work goes through the job queue — never block the HTTP thread
- Storage is abstracted behind a `StorageBackend` interface — do not hardcode file paths
- Model adapters implement a common `VideoAdapter` interface
- Return `job_id` from generation endpoints; callers poll `/jobs/{job_id}` for status

## PRs and Issues

- All PRs must reference the related issue (use `Closes #N` in the PR body)
- Branch names follow: `claude/description-sessionId` or `feature/short-name`
- Write tests for any new endpoint or adapter; run `pytest tests/` before opening a PR
- Tag `@skywalker8888` for review on any PR that touches `video_backend/` or `app.py`

## What to Avoid

- Do not add `print()` statements — use Python `logging`
- Do not commit `.env` files, API keys, or model weights
- Do not introduce synchronous blocking calls inside async handlers
- Do not add new dependencies without updating `requirements.txt`
