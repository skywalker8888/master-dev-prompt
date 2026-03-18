"""
video_backend/config.py
-----------------------
All configuration sourced from environment variables with sensible defaults.
"""

from __future__ import annotations

import os
from enum import Enum


class ModelBackend(str, Enum):
    COGVIDEOX = "cogvideox"
    ALLEGRO = "allegro"
    STABLE_VIDEO = "stable_video"
    MOCK = "mock"


class Settings:
    # Which T2V adapter to use (mock requires no GPU)
    MODEL_BACKEND: ModelBackend = ModelBackend(
        os.getenv("MODEL_BACKEND", ModelBackend.MOCK)
    )

    # Where finished videos are served from / stored
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "/tmp/video_backend/outputs")
    BASE_VIDEO_URL: str = os.getenv("BASE_VIDEO_URL", "http://localhost:8001/videos")

    # In-memory queue concurrency
    MAX_WORKERS: int = int(os.getenv("MAX_WORKERS", "2"))

    # Job retention (max jobs kept in memory)
    MAX_JOBS: int = int(os.getenv("MAX_JOBS", "500"))

    # CogVideoX settings
    COGVIDEOX_MODEL_PATH: str = os.getenv(
        "COGVIDEOX_MODEL_PATH", "THUDM/CogVideoX-5b"
    )
    COGVIDEOX_NUM_FRAMES: int = int(os.getenv("COGVIDEOX_NUM_FRAMES", "49"))
    COGVIDEOX_FPS: int = int(os.getenv("COGVIDEOX_FPS", "8"))

    # Allegro settings
    ALLEGRO_API_URL: str = os.getenv("ALLEGRO_API_URL", "")
    ALLEGRO_API_KEY: str = os.getenv("ALLEGRO_API_KEY", "")

    # Stable Video Diffusion settings
    SVD_MODEL_PATH: str = os.getenv(
        "SVD_MODEL_PATH", "stabilityai/stable-video-diffusion-img2vid-xt"
    )
    SVD_NUM_FRAMES: int = int(os.getenv("SVD_NUM_FRAMES", "25"))
    SVD_FPS: int = int(os.getenv("SVD_FPS", "7"))

    # Optional server API key (leave unset for open / local dev)
    SERVER_API_KEY: str = os.getenv("SERVER_API_KEY", "")


settings = Settings()
