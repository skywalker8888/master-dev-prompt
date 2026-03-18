"""
video_backend/main.py
---------------------
FastAPI application entry point.

Usage:
    cd video_backend
    uvicorn video_backend.main:app --port 8001 --reload

Or from the repo root:
    uvicorn video_backend.main:app --port 8001

Environment variables:
    MODEL_BACKEND      cogvideox | allegro | stable_video | mock  (default: mock)
    OUTPUT_DIR         Where generated videos are stored  (default: /tmp/video_backend/outputs)
    BASE_VIDEO_URL     Public base URL for serving videos (default: http://localhost:8001/videos)
    MAX_WORKERS        Worker thread count (default: 2)
    SERVER_API_KEY     Optional bearer token for auth (leave unset for open)
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import settings
from .jobs import job_queue
from .routes import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan — start workers, mount static video directory
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
    await job_queue.start()
    logger.info("video_backend ready (backend=%s, output_dir=%s)", settings.MODEL_BACKEND, settings.OUTPUT_DIR)
    yield
    await job_queue.stop()
    logger.info("video_backend shutdown complete")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Video Backend",
    description=(
        "Async text-to-video generation service. "
        "Submit a prompt, poll for status, retrieve the video URL."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(router)

# Serve generated videos at /videos/<job_id>.mp4
os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
app.mount("/videos", StaticFiles(directory=settings.OUTPUT_DIR), name="videos")
