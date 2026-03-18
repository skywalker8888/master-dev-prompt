"""
video_backend/adapters/cogvideox.py
------------------------------------
Adapter for CogVideoX (THUDM/CogVideoX-5b or CogVideoX-2b).

Requirements (GPU host only):
    pip install torch torchvision diffusers transformers accelerate imageio[ffmpeg]

Env vars:
    COGVIDEOX_MODEL_PATH   HuggingFace model id or local path (default: THUDM/CogVideoX-5b)
    COGVIDEOX_NUM_FRAMES   Number of frames to generate (default: 49)
    COGVIDEOX_FPS          Output FPS (default: 8)
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from ..models import GenerateRequest
from .base import BaseVideoAdapter, VideoResult

if TYPE_CHECKING:
    pass


class CogVideoXAdapter(BaseVideoAdapter):
    """
    Wraps the CogVideoX diffusion pipeline.

    The pipeline is loaded lazily on first call to avoid import-time GPU
    allocation when the adapter is not actually selected.
    """

    def __init__(self) -> None:
        self._pipe = None
        self._model_path: str = os.getenv("COGVIDEOX_MODEL_PATH", "THUDM/CogVideoX-5b")
        self._default_num_frames: int = int(os.getenv("COGVIDEOX_NUM_FRAMES", "49"))
        self._default_fps: int = int(os.getenv("COGVIDEOX_FPS", "8"))

    @property
    def name(self) -> str:
        return "cogvideox"

    def _load_pipeline(self):
        if self._pipe is not None:
            return self._pipe

        try:
            import torch
            from diffusers import CogVideoXPipeline
        except ImportError as exc:
            raise RuntimeError(
                "CogVideoX requires: pip install torch diffusers transformers accelerate"
            ) from exc

        dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
        self._pipe = CogVideoXPipeline.from_pretrained(
            self._model_path,
            torch_dtype=dtype,
        )

        if torch.cuda.is_available():
            self._pipe = self._pipe.to("cuda")
        else:
            # CPU fallback — very slow but functional for smoke-testing
            self._pipe = self._pipe.to("cpu")

        self._pipe.enable_model_cpu_offload()
        return self._pipe

    def generate(self, request: GenerateRequest, output_path: str) -> VideoResult:
        try:
            import torch
            from diffusers.utils import export_to_video
        except ImportError as exc:
            raise RuntimeError(
                "CogVideoX requires: pip install torch diffusers transformers accelerate imageio[ffmpeg]"
            ) from exc

        pipe = self._load_pipeline()

        num_frames = request.num_frames or self._default_num_frames
        fps = request.fps or self._default_fps
        width = request.width or 720
        height = request.height or 480

        generator = None
        if request.seed is not None:
            generator = torch.Generator().manual_seed(request.seed)

        video_frames = pipe(
            prompt=request.prompt,
            negative_prompt=request.negative_prompt or "",
            num_frames=num_frames,
            height=height,
            width=width,
            generator=generator,
        ).frames[0]

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        export_to_video(video_frames, output_path, fps=fps)

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
