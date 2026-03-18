"""
video_backend/adapters/mock.py
------------------------------
No-GPU mock adapter — writes a tiny placeholder MP4-like file.
Used for local dev, CI, and testing without hardware.
"""

from __future__ import annotations

import os
import time

from ..models import GenerateRequest
from .base import BaseVideoAdapter, VideoResult


class MockAdapter(BaseVideoAdapter):
    """Returns instantly with a 1-byte stub file.  Never needs a GPU."""

    MOCK_DELAY_SECONDS: float = float(os.getenv("MOCK_DELAY_SECONDS", "0.5"))

    @property
    def name(self) -> str:
        return "mock"

    def generate(self, request: GenerateRequest, output_path: str) -> VideoResult:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        num_frames = request.num_frames or 49
        fps = request.fps or 8
        width = request.width or 720
        height = request.height or 480

        # Simulate work
        time.sleep(self.MOCK_DELAY_SECONDS)

        # Write a minimal stub so downstream code can stat the file
        with open(output_path, "wb") as fh:
            fh.write(b"\x00" * 32)  # placeholder bytes

        return VideoResult(
            file_path=output_path,
            duration_seconds=round(num_frames / fps, 2),
            width=width,
            height=height,
            fps=fps,
            num_frames=num_frames,
            extra={"prompt_preview": request.prompt[:80], "backend": "mock"},
        )
