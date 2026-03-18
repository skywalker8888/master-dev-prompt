"""
video_backend/adapters/ltxvideo.py
------------------------------------
Adapter for LTX-Video (Lightricks) — the fastest open-source T2V model.

Key strengths:
  • Generates 30 fps video at 1216×704 faster than real-time on capable GPUs
  • Runs on 12 GB VRAM
  • Apache 2.0 license
  • Native text-to-video and image-to-video

Requirements (GPU host):
    pip install torch torchvision diffusers transformers accelerate imageio[ffmpeg]

Env vars:
    LTX_MODEL_PATH    HF model id (default: Lightricks/LTX-Video)
    LTX_NUM_FRAMES    Frames to generate (default: 121 ≈ 4 s @ 30 fps)
    LTX_FPS           Output FPS (default: 30)
    LTX_HEIGHT        Output height in pixels (default: 480)
    LTX_WIDTH         Output width  in pixels (default: 704)
"""

from __future__ import annotations

import logging
import os

from ..models import GenerateRequest
from .base import BaseVideoAdapter, VideoResult

logger = logging.getLogger(__name__)


class LTXVideoAdapter(BaseVideoAdapter):
    """
    LTX-Video adapter via HuggingFace diffusers.

    LTX-Video is the fastest open-source T2V option — it generates a 4-second
    clip in roughly 10–30 seconds on a modern GPU, making it excellent for
    rapid iteration and low-latency use cases.
    """

    def __init__(self) -> None:
        self._model_path: str = os.getenv("LTX_MODEL_PATH", "Lightricks/LTX-Video")
        self._default_num_frames: int = int(os.getenv("LTX_NUM_FRAMES", "121"))
        self._default_fps: int = int(os.getenv("LTX_FPS", "30"))
        self._default_height: int = int(os.getenv("LTX_HEIGHT", "480"))
        self._default_width: int = int(os.getenv("LTX_WIDTH", "704"))
        self._pipe = None

    @property
    def name(self) -> str:
        return "ltxvideo"

    # ------------------------------------------------------------------
    # Pipeline (lazy)
    # ------------------------------------------------------------------

    def _load_pipeline(self):
        if self._pipe is not None:
            return self._pipe

        try:
            import torch
            from diffusers import LTXPipeline
        except ImportError as exc:
            raise RuntimeError(
                "LTX-Video requires diffusers >= 0.32: "
                "pip install 'diffusers>=0.32' torch transformers accelerate"
            ) from exc

        dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
        self._pipe = LTXPipeline.from_pretrained(
            self._model_path,
            torch_dtype=dtype,
        )

        if torch.cuda.is_available():
            self._pipe.enable_model_cpu_offload()
        else:
            logger.warning(
                "LTX-Video: CUDA not available — running on CPU (very slow)"
            )

        return self._pipe

    # ------------------------------------------------------------------
    # generate
    # ------------------------------------------------------------------

    def generate(self, request: GenerateRequest, output_path: str) -> VideoResult:
        try:
            import torch
            from diffusers.utils import export_to_video
        except ImportError as exc:
            raise RuntimeError(
                "LTX-Video requires: pip install 'diffusers>=0.32' torch transformers accelerate imageio[ffmpeg]"
            ) from exc

        pipe = self._load_pipeline()

        num_frames = request.num_frames or self._default_num_frames
        fps = request.fps or self._default_fps
        height = request.height or self._default_height
        width = request.width or self._default_width

        # LTX-Video requires (height, width) to be divisible by 32
        height = (height // 32) * 32
        width = (width // 32) * 32

        # num_frames must satisfy: (num_frames - 1) % 8 == 0
        if (num_frames - 1) % 8 != 0:
            num_frames = ((num_frames - 1) // 8 + 1) * 8 + 1
            logger.debug("LTX-Video: adjusted num_frames to %d", num_frames)

        generator = None
        if request.seed is not None:
            generator = torch.Generator(device="cpu").manual_seed(request.seed)

        output = pipe(
            prompt=request.prompt,
            negative_prompt=request.negative_prompt or "worst quality, inconsistent motion, blurry, jittery, distorted",
            width=width,
            height=height,
            num_frames=num_frames,
            generator=generator,
        )
        frames = output.frames[0]

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        export_to_video(frames, output_path, fps=fps)

        return VideoResult(
            file_path=output_path,
            duration_seconds=round(num_frames / fps, 2),
            width=width,
            height=height,
            fps=fps,
            num_frames=num_frames,
            extra={"model": self._model_path},
        )

    def health_check(self) -> dict:
        try:
            import torch
            return {
                "status": "ok",
                "adapter": self.name,
                "model_path": self._model_path,
                "cuda_available": torch.cuda.is_available(),
                "pipeline_loaded": self._pipe is not None,
            }
        except ImportError:
            return {
                "status": "degraded",
                "adapter": self.name,
                "reason": "torch/diffusers not installed",
            }
