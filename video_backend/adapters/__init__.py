"""video_backend/adapters — T2V model adapters."""

from .allegro import AllegroAdapter
from .base import BaseVideoAdapter, VideoResult
from .cogvideox import CogVideoXAdapter
from .mock import MockAdapter
from .stable_video import StableVideoAdapter

__all__ = [
    "BaseVideoAdapter",
    "VideoResult",
    "MockAdapter",
    "CogVideoXAdapter",
    "AllegroAdapter",
    "StableVideoAdapter",
]
