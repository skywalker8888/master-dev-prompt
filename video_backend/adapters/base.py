"""
video_backend/adapters/base.py
------------------------------
Abstract base class every T2V adapter must implement.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

from ..models import GenerateRequest


@dataclass
class VideoResult:
    """Returned by every adapter on success."""
    file_path: str                    # absolute path to the saved video file
    duration_seconds: float
    width: int
    height: int
    fps: int
    num_frames: int
    extra: dict = field(default_factory=dict)  # adapter-specific metadata


class BaseVideoAdapter(ABC):
    """
    Contract every T2V adapter must satisfy.

    Adapters are *synchronous* — the job queue runs them in a thread pool
    so the FastAPI event loop is never blocked.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable adapter identifier, e.g. 'cogvideox'."""

    @abstractmethod
    def generate(self, request: GenerateRequest, output_path: str) -> VideoResult:
        """
        Run inference and write the video to *output_path*.

        Args:
            request:     The validated GenerateRequest from the user.
            output_path: Full path where the adapter must write the result
                         (e.g. /tmp/video_backend/outputs/<job_id>.mp4).

        Returns:
            VideoResult with metadata about the generated clip.

        Raises:
            RuntimeError on any unrecoverable generation error.
        """

    def health_check(self) -> dict:
        """
        Optional liveness check.  Override to test GPU / API connectivity.
        Returns a dict with at least {"status": "ok" | "degraded" | "down"}.
        """
        return {"status": "ok", "adapter": self.name}
