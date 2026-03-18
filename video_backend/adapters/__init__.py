"""video_backend/adapters — T2V model adapters."""

from .allegro import AllegroAdapter
from .base import BaseVideoAdapter, VideoResult
from .cogvideox import CogVideoXAdapter
from .ltxvideo import LTXVideoAdapter
from .mock import MockAdapter
from .stable_video import StableVideoAdapter
from .wan21 import Wan21Adapter

__all__ = [
    "BaseVideoAdapter",
    "VideoResult",
    "MockAdapter",
    "CogVideoXAdapter",
    "AllegroAdapter",
    "StableVideoAdapter",
    "Wan21Adapter",
    "LTXVideoAdapter",
]
