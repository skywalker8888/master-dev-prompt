"""
video_backend/jobs.py
---------------------
In-process async job queue backed by a thread pool.

Design:
  • Jobs are enqueued into an asyncio.Queue and consumed by a pool of
    worker tasks that run adapter.generate() in a thread (run_in_executor)
    so the event loop is never blocked.
  • Job records live in an OrderedDict (bounded by MAX_JOBS) — no Redis
    required for MVP.  Swap out JobRegistry for a Redis-backed one to scale.
  • Each finished video is served via FastAPI's StaticFiles mount.
"""

from __future__ import annotations

import asyncio
import logging
import os
import uuid
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Optional

from .adapters.base import BaseVideoAdapter
from .config import ModelBackend, settings
from .models import GenerateRequest, JobRecord, JobStatus

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Adapter factory
# ---------------------------------------------------------------------------

def _build_adapter(backend: ModelBackend) -> BaseVideoAdapter:
    if backend == ModelBackend.COGVIDEOX:
        from .adapters.cogvideox import CogVideoXAdapter
        return CogVideoXAdapter()
    if backend == ModelBackend.ALLEGRO:
        from .adapters.allegro import AllegroAdapter
        return AllegroAdapter()
    if backend == ModelBackend.STABLE_VIDEO:
        from .adapters.stable_video import StableVideoAdapter
        return StableVideoAdapter()
    if backend == ModelBackend.WAN21:
        from .adapters.wan21 import Wan21Adapter
        return Wan21Adapter()
    if backend == ModelBackend.LTX_VIDEO:
        from .adapters.ltxvideo import LTXVideoAdapter
        return LTXVideoAdapter()
    # default / mock
    from .adapters.mock import MockAdapter
    return MockAdapter()


# ---------------------------------------------------------------------------
# Job registry (bounded in-memory store)
# ---------------------------------------------------------------------------

class JobRegistry:
    """Thread-safe bounded OrderedDict for job records."""

    def __init__(self, max_jobs: int = 500) -> None:
        self._store: OrderedDict[str, JobRecord] = OrderedDict()
        self._lock = asyncio.Lock()
        self._max = max_jobs

    async def put(self, record: JobRecord) -> None:
        async with self._lock:
            if len(self._store) >= self._max:
                # Only evict if the oldest job is in a terminal state to avoid
                # orphaning in-flight jobs.
                oldest_id, oldest = next(iter(self._store.items()))
                if oldest.status in (JobStatus.COMPLETED, JobStatus.FAILED):
                    self._store.popitem(last=False)
                else:
                    logger.warning(
                        "JobRegistry at capacity (%d); oldest job %s is still %s — skipping eviction",
                        self._max, oldest_id, oldest.status,
                    )
            self._store[record.job_id] = record

    async def get(self, job_id: str) -> Optional[JobRecord]:
        async with self._lock:
            return self._store.get(job_id)

    async def update(self, job_id: str, **kwargs) -> Optional[JobRecord]:
        async with self._lock:
            record = self._store.get(job_id)
            if record is None:
                return None
            for k, v in kwargs.items():
                setattr(record, k, v)
            record.updated_at = datetime.now(timezone.utc)
            return record

    async def list_recent(self, limit: int = 50, offset: int = 0) -> list[JobRecord]:
        async with self._lock:
            items = list(reversed(list(self._store.values())))
            return items[offset: offset + limit]

    async def count(self) -> int:
        async with self._lock:
            return len(self._store)


# ---------------------------------------------------------------------------
# Job queue / worker pool
# ---------------------------------------------------------------------------

class JobQueue:
    """
    Manages the asyncio queue, thread pool, and worker lifecycle.
    """

    def __init__(self) -> None:
        self.registry = JobRegistry(max_jobs=settings.MAX_JOBS)
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._executor = ThreadPoolExecutor(max_workers=settings.MAX_WORKERS)
        self._adapter: Optional[BaseVideoAdapter] = None
        self._workers: list[asyncio.Task] = []

    def _get_adapter(self) -> BaseVideoAdapter:
        if self._adapter is None:
            self._adapter = _build_adapter(settings.MODEL_BACKEND)
        return self._adapter

    @property
    def queue_size(self) -> int:
        """Number of jobs currently waiting in the queue (not yet processing)."""
        return self._queue.qsize()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self, num_workers: int = None) -> None:
        n = num_workers or settings.MAX_WORKERS
        for i in range(n):
            task = asyncio.create_task(self._worker(f"worker-{i}"), name=f"video-worker-{i}")
            self._workers.append(task)
        logger.info("JobQueue started with %d workers (backend=%s)", n, settings.MODEL_BACKEND)

    async def stop(self) -> None:
        for task in self._workers:
            task.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        # wait=True so in-flight threads finish cleanly before the process exits
        self._executor.shutdown(wait=True)
        logger.info("JobQueue stopped")

    # ------------------------------------------------------------------
    # Enqueue
    # ------------------------------------------------------------------

    async def enqueue(self, request: GenerateRequest) -> JobRecord:
        job_id = str(uuid.uuid4())
        record = JobRecord(job_id=job_id, request=request)
        await self.registry.put(record)
        await self._queue.put(job_id)
        logger.info("Enqueued job %s (prompt=%.60s…)", job_id, request.prompt)
        return record

    # ------------------------------------------------------------------
    # Worker loop
    # ------------------------------------------------------------------

    async def _worker(self, name: str) -> None:
        logger.info("Worker %s ready", name)
        loop = asyncio.get_event_loop()

        while True:
            try:
                job_id = await self._queue.get()
                record = await self.registry.get(job_id)
                if record is None:
                    logger.warning("Worker %s: job %s not found in registry (evicted?)", name, job_id)
                    self._queue.task_done()
                    continue

                # Skip jobs that were cancelled while queued
                if record.status == JobStatus.FAILED:
                    logger.info("Worker %s: skipping cancelled job %s", name, job_id)
                    self._queue.task_done()
                    continue

                await self.registry.update(job_id, status=JobStatus.PROCESSING)
                logger.info("Worker %s: processing job %s", name, job_id)

                output_path = os.path.join(settings.OUTPUT_DIR, f"{job_id}.mp4")

                try:
                    adapter = self._get_adapter()
                    result = await loop.run_in_executor(
                        self._executor,
                        adapter.generate,
                        record.request,
                        output_path,
                    )

                    video_url = f"{settings.BASE_VIDEO_URL}/{job_id}.mp4"
                    await self.registry.update(
                        job_id,
                        status=JobStatus.COMPLETED,
                        video_url=video_url,
                        metadata={
                            "duration_seconds": result.duration_seconds,
                            "width": result.width,
                            "height": result.height,
                            "fps": result.fps,
                            "num_frames": result.num_frames,
                            "adapter": adapter.name,
                            **result.extra,
                        },
                    )
                    logger.info("Worker %s: job %s completed → %s", name, job_id, video_url)

                except Exception as exc:
                    logger.exception("Worker %s: job %s failed", name, job_id)
                    await self.registry.update(
                        job_id,
                        status=JobStatus.FAILED,
                        error=repr(exc),
                    )

                finally:
                    self._queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Worker %s: unexpected error in loop", name)


# ---------------------------------------------------------------------------
# Singleton — shared across the FastAPI app
# ---------------------------------------------------------------------------

job_queue = JobQueue()
