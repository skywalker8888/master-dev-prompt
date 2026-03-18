"""
Integration tests for the FastAPI routes using the mock adapter.
Runs without GPU.
"""

from __future__ import annotations

import os
import time

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Force mock backend before importing the app
os.environ.setdefault("MODEL_BACKEND", "mock")
os.environ.setdefault("MOCK_DELAY_SECONDS", "0.05")  # fast tests

from video_backend.main import app  # noqa: E402 — env must be set first


@pytest_asyncio.fixture
async def client(tmp_path):
    """
    Each test gets a fresh JobQueue so asyncio.Queue is bound to the
    current event loop (pytest-asyncio STRICT mode creates a new loop per test).
    We patch both the jobs module and the routes module so route handlers
    pick up the fresh queue via their module-level global lookup.
    """
    from video_backend import jobs as jobs_module
    from video_backend import routes as routes_module
    from video_backend.jobs import JobQueue

    fresh_queue = JobQueue()
    # Patch module-level names so route handlers see the fresh queue
    jobs_module.job_queue = fresh_queue
    routes_module.job_queue = fresh_queue

    await fresh_queue.start()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    await fresh_queue.stop()


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["adapter"]["adapter"] == "mock"


# ---------------------------------------------------------------------------
# Job creation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_job_returns_202(client):
    resp = await client.post("/jobs", json={"prompt": "A mountain stream"})
    assert resp.status_code == 202
    data = resp.json()
    assert data["status"] in ("pending", "processing")
    assert "job_id" in data
    assert data["prompt"] == "A mountain stream"


@pytest.mark.asyncio
async def test_create_job_missing_prompt(client):
    resp = await client.post("/jobs", json={})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_job_empty_prompt(client):
    resp = await client.post("/jobs", json={"prompt": ""})
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Job retrieval
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_job_not_found(client):
    resp = await client.get("/jobs/nonexistent-id")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_job_found(client):
    create = await client.post("/jobs", json={"prompt": "Sunset over the sea"})
    job_id = create.json()["job_id"]

    resp = await client.get(f"/jobs/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["job_id"] == job_id


# ---------------------------------------------------------------------------
# Job completion (poll until done)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_job_completes(client):
    create = await client.post("/jobs", json={"prompt": "City timelapse at night", "num_frames": 8, "fps": 4})
    job_id = create.json()["job_id"]

    # Poll up to 5 seconds for completion
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        resp = await client.get(f"/jobs/{job_id}")
        data = resp.json()
        if data["status"] in ("completed", "failed"):
            break
        import asyncio; await asyncio.sleep(0.1)

    assert data["status"] == "completed", f"Job did not complete in time: {data}"
    assert data["video_url"] is not None
    assert "metadata" in data
    assert data["metadata"]["adapter"] == "mock"


# ---------------------------------------------------------------------------
# Job list
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_jobs(client):
    await client.post("/jobs", json={"prompt": "first"})
    await client.post("/jobs", json={"prompt": "second"})

    resp = await client.get("/jobs")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 2
    assert len(data["jobs"]) >= 2


@pytest.mark.asyncio
async def test_list_jobs_pagination(client):
    for i in range(5):
        await client.post("/jobs", json={"prompt": f"prompt {i}"})

    resp = await client.get("/jobs?limit=2&offset=0")
    assert resp.status_code == 200
    assert len(resp.json()["jobs"]) <= 2


# ---------------------------------------------------------------------------
# Cancel
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cancel_nonexistent_job(client):
    resp = await client.delete("/jobs/does-not-exist")
    assert resp.status_code == 404
