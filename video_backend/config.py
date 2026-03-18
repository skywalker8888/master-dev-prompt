"""
video_backend/config.py
-----------------------
All configuration sourced from environment variables with sensible defaults.
"""

from __future__ import annotations

import os
from enum import Enum


class ModelBackend(str, Enum):
    # --- New top-tier models (2025–2026) ---
    WAN21 = "wan21"            # Wan2.1/2.2 — best open-source T2V, Apache 2.0, 8 GB VRAM min
    LTX_VIDEO = "ltxvideo"     # LTX-Video — fastest open-source T2V (real-time on high-end GPU)
    # --- Original adapters ---
    COGVIDEOX = "cogvideox"    # THUDM/CogVideoX-5b — good quality, modest hardware
    ALLEGRO = "allegro"        # rhymes-ai/Allegro — local or remote API
    STABLE_VIDEO = "stable_video"  # Stable Video Diffusion (image-to-video)
    MOCK = "mock"              # No-GPU stub for dev/CI


class Settings:
    # Which T2V adapter to use (mock requires no GPU)
    MODEL_BACKEND: ModelBackend = ModelBackend(
        os.getenv("MODEL_BACKEND", ModelBackend.MOCK)
    )

    # Where finished videos are stored / served from
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "/tmp/video_backend/outputs")
    BASE_VIDEO_URL: str = os.getenv("BASE_VIDEO_URL", "http://localhost:8001/videos")

    # In-memory queue concurrency
    MAX_WORKERS: int = int(os.getenv("MAX_WORKERS", "2"))

    # Job retention (max jobs kept in memory)
    MAX_JOBS: int = int(os.getenv("MAX_JOBS", "500"))

    # --- Wan2.1 / Wan2.2 settings ---
    # Lightweight: Wan-AI/Wan2.1-T2V-1.3B (8 GB VRAM)
    # High quality: Wan-AI/Wan2.1-T2V-14B  (24+ GB VRAM)
    # Newest MoE:   Wan-AI/Wan2.2-T2V-A14B
    WAN21_MODEL_PATH: str = os.getenv("WAN21_MODEL_PATH", "Wan-AI/Wan2.1-T2V-1.3B")
    WAN21_NUM_FRAMES: int = int(os.getenv("WAN21_NUM_FRAMES", "81"))
    WAN21_FPS: int = int(os.getenv("WAN21_FPS", "16"))

    # --- LTX-Video settings ---
    LTX_MODEL_PATH: str = os.getenv("LTX_MODEL_PATH", "Lightricks/LTX-Video")
    LTX_NUM_FRAMES: int = int(os.getenv("LTX_NUM_FRAMES", "121"))
    LTX_FPS: int = int(os.getenv("LTX_FPS", "30"))

    # --- CogVideoX settings ---
    COGVIDEOX_MODEL_PATH: str = os.getenv("COGVIDEOX_MODEL_PATH", "THUDM/CogVideoX-5b")
    COGVIDEOX_NUM_FRAMES: int = int(os.getenv("COGVIDEOX_NUM_FRAMES", "49"))
    COGVIDEOX_FPS: int = int(os.getenv("COGVIDEOX_FPS", "8"))

    # --- Allegro settings ---
    ALLEGRO_API_URL: str = os.getenv("ALLEGRO_API_URL", "")
    ALLEGRO_API_KEY: str = os.getenv("ALLEGRO_API_KEY", "")
    ALLEGRO_MAX_POLL_WAIT: int = int(os.getenv("ALLEGRO_MAX_POLL_WAIT", "600"))
    ALLEGRO_MAX_VIDEO_MB: int = int(os.getenv("ALLEGRO_MAX_VIDEO_MB", "500"))

    # --- Stable Video Diffusion settings ---
    SVD_MODEL_PATH: str = os.getenv(
        "SVD_MODEL_PATH", "stabilityai/stable-video-diffusion-img2vid-xt"
    )
    SVD_NUM_FRAMES: int = int(os.getenv("SVD_NUM_FRAMES", "25"))
    SVD_FPS: int = int(os.getenv("SVD_FPS", "7"))

    # Optional server API key (leave unset for open / local dev)
    SERVER_API_KEY: str = os.getenv("SERVER_API_KEY", "")


settings = Settings()
