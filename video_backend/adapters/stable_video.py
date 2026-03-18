"""
video_backend/adapters/stable_video.py
----------------------------------------
Adapter for Stable Video Diffusion (stabilityai/stable-video-diffusion-img2vid-xt).

SVD is technically an image-to-video model; this adapter auto-generates a
conditioning image from the text prompt using SDXL (or a simpler pipeline),
then runs SVD on that image.  If SDXL is unavailable it falls back to a
solid-colour placeholder frame.

Requirements (GPU host):
    pip install torch torchvision diffusers transformers accelerate imageio[ffmpeg]

Env vars:
    SVD_MODEL_PATH    HF model id (default: stabilityai/stable-video-diffusion-img2vid-xt)
    SVD_NUM_FRAMES    Frames to generate (default: 25)
    SVD_FPS           Output FPS (default: 7)
    SVD_SDXL_PATH     SDXL model for conditioning image (default: stabilityai/stable-diffusion-xl-base-1.0)
"""

from __future__ import annotations

import os

from ..models import GenerateRequest
from .base import BaseVideoAdapter, VideoResult


class StableVideoAdapter(BaseVideoAdapter):
    """
    Stable Video Diffusion — text → conditioning image → video.
    """

    def __init__(self) -> None:
        self._model_path: str = os.getenv(
            "SVD_MODEL_PATH", "stabilityai/stable-video-diffusion-img2vid-xt"
        )
        self._sdxl_path: str = os.getenv(
            "SVD_SDXL_PATH", "stabilityai/stable-diffusion-xl-base-1.0"
        )
        self._default_num_frames: int = int(os.getenv("SVD_NUM_FRAMES", "25"))
        self._default_fps: int = int(os.getenv("SVD_FPS", "7"))
        self._svd_pipe = None
        self._sdxl_pipe = None

    @property
    def name(self) -> str:
        return "stable_video"

    # ------------------------------------------------------------------
    # Pipeline loading (lazy)
    # ------------------------------------------------------------------

    def _load_svd(self):
        if self._svd_pipe is not None:
            return self._svd_pipe
        try:
            import torch
            from diffusers import StableVideoDiffusionPipeline
        except ImportError as exc:
            raise RuntimeError(
                "SVD requires: pip install torch diffusers transformers accelerate"
            ) from exc

        dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        self._svd_pipe = StableVideoDiffusionPipeline.from_pretrained(
            self._model_path,
            torch_dtype=dtype,
            variant="fp16" if torch.cuda.is_available() else None,
        )
        if torch.cuda.is_available():
            self._svd_pipe = self._svd_pipe.to("cuda")
        self._svd_pipe.enable_model_cpu_offload()
        return self._svd_pipe

    def _load_sdxl(self):
        if self._sdxl_pipe is not None:
            return self._sdxl_pipe
        try:
            import torch
            from diffusers import DiffusionPipeline
        except ImportError:
            return None

        try:
            dtype = torch.float16 if torch.cuda.is_available() else torch.float32
            self._sdxl_pipe = DiffusionPipeline.from_pretrained(
                self._sdxl_path, torch_dtype=dtype, use_safetensors=True
            )
            if torch.cuda.is_available():
                self._sdxl_pipe = self._sdxl_pipe.to("cuda")
            self._sdxl_pipe.enable_model_cpu_offload()
        except Exception:
            # SDXL optional; fall back to placeholder image
            self._sdxl_pipe = None
        return self._sdxl_pipe

    # ------------------------------------------------------------------
    # Conditioning image helpers
    # ------------------------------------------------------------------

    def _make_conditioning_image(self, prompt: str, width: int, height: int, seed=None):
        """
        Try SDXL first, then fall back to a solid-colour PIL image.
        Returns a PIL.Image.
        """
        from PIL import Image

        sdxl = self._load_sdxl()
        if sdxl is not None:
            try:
                import torch
                generator = torch.Generator().manual_seed(seed) if seed is not None else None
                result = sdxl(
                    prompt=prompt,
                    height=height,
                    width=width,
                    num_inference_steps=30,
                    generator=generator,
                )
                return result.images[0]
            except Exception:
                pass  # fall through to solid colour

        # Fallback: grey placeholder
        return Image.new("RGB", (width, height), color=(128, 128, 128))

    # ------------------------------------------------------------------
    # generate
    # ------------------------------------------------------------------

    def generate(self, request: GenerateRequest, output_path: str) -> VideoResult:
        try:
            from diffusers.utils import export_to_video
        except ImportError as exc:
            raise RuntimeError(
                "SVD requires: pip install torch diffusers transformers accelerate imageio[ffmpeg]"
            ) from exc

        num_frames = request.num_frames or self._default_num_frames
        fps = request.fps or self._default_fps
        width = request.width or 1024
        height = request.height or 576

        conditioning_image = self._make_conditioning_image(
            request.prompt, width, height, request.seed
        )

        import torch
        svd = self._load_svd()
        generator = None
        if request.seed is not None:
            generator = torch.Generator().manual_seed(request.seed)

        frames = svd(
            conditioning_image,
            num_frames=num_frames,
            generator=generator,
        ).frames[0]

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        export_to_video(frames, output_path, fps=fps)

        return VideoResult(
            file_path=output_path,
            duration_seconds=round(num_frames / fps, 2),
            width=width,
            height=height,
            fps=fps,
            num_frames=num_frames,
            extra={"model": self._model_path, "conditioning": "sdxl_or_placeholder"},
        )

    def health_check(self) -> dict:
        try:
            import torch
            return {
                "status": "ok",
                "adapter": self.name,
                "model_path": self._model_path,
                "cuda_available": torch.cuda.is_available(),
                "svd_loaded": self._svd_pipe is not None,
                "sdxl_loaded": self._sdxl_pipe is not None,
            }
        except ImportError:
            return {
                "status": "degraded",
                "adapter": self.name,
                "reason": "torch/diffusers not installed",
            }
