"""
video_backend/adapters/wan21.py
--------------------------------
Adapter for Wan2.1 / Wan2.2 (Alibaba) — currently the top open-source T2V model.

Key strengths:
  • Apache 2.0 license — safe for commercial use
  • 1.3B variant requires only ~8 GB VRAM (consumer GPU friendly)
  • 14B variant matches closed-source quality
  • Native Chinese + English prompts
  • Generates 480p / 720p video up to 5 seconds

Model variants available on HuggingFace:
  • Wan-AI/Wan2.1-T2V-1.3B   — lightweight, 8 GB VRAM
  • Wan-AI/Wan2.1-T2V-14B    — high-quality, 24+ GB VRAM
  • Wan-AI/Wan2.2-T2V-A14B   — MoE architecture, newest

Requirements (GPU host):
    pip install torch torchvision diffusers transformers accelerate imageio[ffmpeg]

Env vars:
    WAN21_MODEL_PATH    HF model id (default: Wan-AI/Wan2.1-T2V-1.3B)
    WAN21_NUM_FRAMES    Frames to generate (default: 81 ≈ 5 s @ ~16 fps)
    WAN21_FPS           Output FPS (default: 16)
    WAN21_HEIGHT        Output height (default: 480)
    WAN21_WIDTH         Output width  (default: 832)
"""

from __future__ import annotations

import logging
import os

from ..models import GenerateRequest
from .base import BaseVideoAdapter, VideoResult

logger = logging.getLogger(__name__)


class Wan21Adapter(BaseVideoAdapter):
    """
    Wan2.1 / Wan2.2 text-to-video adapter via HuggingFace diffusers.

    The pipeline is lazy-loaded on first call.  On a consumer RTX 3080 (10 GB)
    the 1.3B model generates a 5-second 480p clip in roughly 2–3 minutes with
    CPU offloading enabled.
    """

    def __init__(self) -> None:
        self._model_path: str = os.getenv("WAN21_MODEL_PATH", "Wan-AI/Wan2.1-T2V-1.3B")
        self._default_num_frames: int = int(os.getenv("WAN21_NUM_FRAMES", "81"))
        self._default_fps: int = int(os.getenv("WAN21_FPS", "16"))
        self._default_height: int = int(os.getenv("WAN21_HEIGHT", "480"))
        self._default_width: int = int(os.getenv("WAN21_WIDTH", "832"))
        self._pipe = None

    @property
    def name(self) -> str:
        return "wan21"

    # ------------------------------------------------------------------
    # Pipeline (lazy)
    # ------------------------------------------------------------------

    def _load_pipeline(self):
        if self._pipe is not None:
            return self._pipe

        try:
            import torch
            from diffusers import AutoencoderKLWan, WanPipeline
            from diffusers.schedulers.scheduling_unipc_multistep import UniPCMultistepScheduler
        except ImportError as exc:
            raise RuntimeError(
                "Wan2.1 requires diffusers >= 0.33: "
                "pip install 'diffusers>=0.33' torch transformers accelerate"
            ) from exc

        dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32

        vae = AutoencoderKLWan.from_pretrained(
            self._model_path, subfolder="vae", torch_dtype=torch.float32
        )
        self._pipe = WanPipeline.from_pretrained(
            self._model_path,
            vae=vae,
            torch_dtype=dtype,
        )
        self._pipe.scheduler = UniPCMultistepScheduler.from_config(
            self._pipe.scheduler.config, flow_shift=8.0
        )

        if torch.cuda.is_available():
            self._pipe.enable_model_cpu_offload()
        else:
            logger.warning(
                "Wan2.1: CUDA not available — running on CPU (very slow, for smoke tests only)"
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
                "Wan2.1 requires: pip install 'diffusers>=0.33' torch transformers accelerate imageio[ffmpeg]"
            ) from exc

        pipe = self._load_pipeline()

        num_frames = request.num_frames or self._default_num_frames
        fps = request.fps or self._default_fps
        height = request.height or self._default_height
        width = request.width or self._default_width

        # Wan2.1 expects num_frames to satisfy (num_frames - 1) % 4 == 0
        # Round up to the nearest valid value.
        if (num_frames - 1) % 4 != 0:
            num_frames = ((num_frames - 1) // 4 + 1) * 4 + 1
            logger.debug("Wan2.1: adjusted num_frames to %d", num_frames)

        generator = None
        if request.seed is not None:
            generator = torch.Generator(device="cpu").manual_seed(request.seed)

        output = pipe(
            prompt=request.prompt,
            negative_prompt=request.negative_prompt or "色情、暴力",  # bilingual default negatives
            height=height,
            width=width,
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
