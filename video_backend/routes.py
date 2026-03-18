"""
video_backend/routes.py
-----------------------
All HTTP endpoints for the video-generation service.

Routes:
    POST   /jobs           — submit a generation request
    GET    /jobs           — list recent jobs
    GET    /jobs/{job_id}  — get a single job's status
    DELETE /jobs/{job_id}  — cancel a pending job (best-effort)
    GET    /health         — liveness + adapter check
"""

from __future__ import annotations

import hmac
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query

from .config import settings
from .jobs import job_queue
from .models import GenerateRequest, JobListResponse, JobResponse, JobStatus

router = APIRouter()


# ---------------------------------------------------------------------------
# Optional API-key auth — key is read from settings (cached at startup)
# ---------------------------------------------------------------------------

async def verify_api_key(x_api_key: Annotated[Optional[str], Header()] = None) -> None:
    if not settings.SERVER_API_KEY:
        return
    if not x_api_key or not hmac.compare_digest(x_api_key, settings.SERVER_API_KEY):
        raise HTTPException(status_code=401, detail="Unauthorized")


Auth = Annotated[None, Depends(verify_api_key)]


# ---------------------------------------------------------------------------
# Job routes
# ---------------------------------------------------------------------------

@router.post("/jobs", response_model=JobResponse, status_code=202)
async def create_job(request: GenerateRequest, _: Auth) -> JobResponse:
    """Submit a text-to-video generation job. Returns immediately with status=pending."""
    record = await job_queue.enqueue(request)
    return record.to_response()


@router.get("/jobs", response_model=JobListResponse)
async def list_jobs(
    _: Auth,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    status: Optional[JobStatus] = Query(None),
) -> JobListResponse:
    """List recent jobs, newest first.  Optionally filter by status."""
    total = await job_queue.registry.count()

    if status is not None:
        # When filtering by status we must over-fetch and then slice,
        # since we can't predict how many matching records exist before offset.
        all_records = await job_queue.registry.list_recent(limit=total, offset=0)
        filtered = [r for r in all_records if r.status == status]
        page = filtered[offset: offset + limit]
    else:
        page = await job_queue.registry.list_recent(limit=limit, offset=offset)

    return JobListResponse(jobs=[r.to_response() for r in page], total=total)


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, _: Auth) -> JobResponse:
    """Fetch the current status of a single job."""
    record = await job_queue.registry.get(job_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id!r} not found")
    return record.to_response()


@router.delete("/jobs/{job_id}", status_code=204)
async def cancel_job(job_id: str, _: Auth) -> None:
    """
    Cancel a pending job (best-effort — cannot stop a job that is already
    in PROCESSING state since the adapter runs in a thread).
    """
    record = await job_queue.registry.get(job_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id!r} not found")
    if record.status != JobStatus.PENDING:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot cancel job in state {record.status.value!r}",
        )
    await job_queue.registry.update(job_id, status=JobStatus.FAILED, error="Cancelled by user")


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@router.get("/health")
async def health(_: Auth) -> dict:
    """Liveness check + adapter health. Never raises — always returns a status dict."""
    try:
        adapter = job_queue._get_adapter()
        adapter_health = adapter.health_check()
    except Exception as exc:
        adapter_health = {"status": "down", "reason": repr(exc)}

    total_jobs = await job_queue.registry.count()
    return {
        "status": "ok",
        "queue_depth": job_queue.queue_size,
        "total_jobs": total_jobs,
        "adapter": adapter_health,
    }
