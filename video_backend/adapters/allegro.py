"""
video_backend/adapters/allegro.py
----------------------------------
Adapter for Allegro (rhymes-ai/Allegro) text-to-video model.

Two modes:
  1. Local inference — loads the HuggingFace pipeline directly (GPU required).
  2. Remote API    — hits an Allegro-compatible REST endpoint
                     (set ALLEGRO_API_URL + ALLEGRO_API_KEY).

Env vars:
    ALLEGRO_API_URL        If set, use remote mode (e.g. https://api.rhymes.ai/v1)
    ALLEGRO_API_KEY        Bearer token for remote mode
    ALLEGRO_MODEL_PATH     HF model id for local mode (default: rhymes-ai/Allegro)
    ALLEGRO_MAX_POLL_WAIT  Max seconds to poll remote API (default: 600)
    ALLEGRO_MAX_VIDEO_MB   Max video file size to download in MB (default: 500)
"""

from __future__ import annotations

import logging
import os
import time
from typing import Optional

import httpx

from ..models import GenerateRequest
from .base import BaseVideoAdapter, VideoResult

logger = logging.getLogger(__name__)

_MAX_POLL_WAIT = int(os.getenv("ALLEGRO_MAX_POLL_WAIT", "600"))
_MAX_VIDEO_BYTES = int(os.getenv("ALLEGRO_MAX_VIDEO_MB", "500")) * 1024 * 1024
_POLL_INTERVAL = 5  # seconds between status checks


class AllegroAdapter(BaseVideoAdapter):
    """
    Allegro T2V adapter — local or remote depending on ALLEGRO_API_URL.
    """

    def __init__(self) -> None:
        self._api_url: str = os.getenv("ALLEGRO_API_URL", "").rstrip("/")
        self._api_key: str = os.getenv("ALLEGRO_API_KEY", "")
        self._model_path: str = os.getenv("ALLEGRO_MODEL_PATH", "rhymes-ai/Allegro")
        self._pipe = None
        # Persistent client for remote mode (connection pooling)
        self._http_client: Optional[httpx.Client] = None

    @property
    def name(self) -> str:
        return "allegro"

    def _get_http_client(self) -> httpx.Client:
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.Client(timeout=httpx.Timeout(connect=10, read=60, write=30, pool=5))
        return self._http_client

    # ------------------------------------------------------------------
    # Local inference
    # ------------------------------------------------------------------

    def _load_pipeline(self):
        if self._pipe is not None:
            return self._pipe

        try:
            import torch
            from diffusers import AllegroPipeline
        except ImportError as exc:
            raise RuntimeError(
                "Allegro local mode requires: pip install torch diffusers transformers accelerate"
            ) from exc

        dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
        self._pipe = AllegroPipeline.from_pretrained(
            self._model_path,
            torch_dtype=dtype,
        )
        if torch.cuda.is_available():
            self._pipe = self._pipe.to("cuda")
        self._pipe.enable_model_cpu_offload()
        return self._pipe

    def _generate_local(self, request: GenerateRequest, output_path: str) -> VideoResult:
        try:
            import torch
            from diffusers.utils import export_to_video
        except ImportError as exc:
            raise RuntimeError(
                "Allegro local mode requires: pip install torch diffusers transformers accelerate imageio[ffmpeg]"
            ) from exc

        pipe = self._load_pipeline()
        num_frames = request.num_frames or 88
        fps = request.fps or 15
        width = request.width or 1280
        height = request.height or 720

        generator = None
        if request.seed is not None:
            generator = torch.Generator().manual_seed(request.seed)

        frames = pipe(
            prompt=request.prompt,
            negative_prompt=request.negative_prompt or "",
            num_frames=num_frames,
            height=height,
            width=width,
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
            extra={"model": self._model_path, "mode": "local"},
        )

    # ------------------------------------------------------------------
    # Remote API mode
    # ------------------------------------------------------------------

    def _generate_remote(self, request: GenerateRequest, output_path: str) -> VideoResult:
        """
        Submit a generation job to an Allegro-compatible REST API, poll until
        complete, then download with size and timeout protection.
        """
        client = self._get_http_client()
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "refined_prompt": request.prompt,
            "num_step": 100,
            "cfg_scale": 7.5,
            "user_prompt": request.prompt,
            "rand_seed": request.seed or 42,
        }
        if request.negative_prompt:
            payload["negative_prompt"] = request.negative_prompt

        # Submit
        resp = client.post(f"{self._api_url}/generate_video", json=payload, headers=headers)
        resp.raise_for_status()
        job_data = resp.json()
        request_id = job_data.get("data")
        if not request_id:
            raise RuntimeError(f"Allegro API returned no request_id; response: {job_data}")

        # Poll with timeout
        deadline = time.monotonic() + _MAX_POLL_WAIT
        video_url: Optional[str] = None

        while time.monotonic() < deadline:
            time.sleep(_POLL_INTERVAL)
            poll = client.get(
                f"{self._api_url}/get_inference_job",
                params={"requestId": request_id},
                headers=headers,
            )
            poll.raise_for_status()
            poll_data = poll.json()
            job_info = poll_data.get("data") or {}
            status = job_info.get("status")

            if status == "success":
                outputs = job_info.get("output_data") or []
                if not outputs:
                    raise RuntimeError(f"Allegro API job {request_id!r} succeeded but returned no output_data")
                video_url = outputs[0]
                break
            elif status in ("failed", "error", "cancelled"):
                raise RuntimeError(f"Allegro API job {request_id!r} ended with status {status!r}: {job_info}")
            elif status in ("queued", "processing", "running", None):
                logger.debug("Allegro job %s status=%s, continuing to poll", request_id, status)
            else:
                logger.warning("Allegro job %s: unknown status %r — continuing to poll", request_id, status)

        if video_url is None:
            raise RuntimeError(
                f"Allegro API job {request_id!r} did not complete within {_MAX_POLL_WAIT}s"
            )

        # Download with size guard
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        downloaded = 0
        with client.stream("GET", video_url, timeout=httpx.Timeout(connect=10, read=120)) as stream:
            stream.raise_for_status()
            with open(output_path, "wb") as fh:
                for chunk in stream.iter_bytes(chunk_size=65536):
                    downloaded += len(chunk)
                    if downloaded > _MAX_VIDEO_BYTES:
                        raise RuntimeError(
                            f"Allegro download exceeded {_MAX_VIDEO_BYTES // (1024*1024)} MB limit"
                        )
                    fh.write(chunk)

        fps = request.fps or 15
        num_frames = request.num_frames or 88
        return VideoResult(
            file_path=output_path,
            duration_seconds=round(num_frames / fps, 2),
            width=request.width or 1280,
            height=request.height or 720,
            fps=fps,
            num_frames=num_frames,
            extra={"request_id": request_id, "source_url": video_url, "mode": "remote"},
        )

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------

    def generate(self, request: GenerateRequest, output_path: str) -> VideoResult:
        if self._api_url:
            return self._generate_remote(request, output_path)
        return self._generate_local(request, output_path)

    def health_check(self) -> dict:
        base = {"adapter": self.name, "mode": "remote" if self._api_url else "local"}
        if self._api_url:
            try:
                resp = httpx.get(f"{self._api_url}/health", timeout=5)
                base["status"] = "ok" if resp.status_code < 400 else "degraded"
                base["api_url"] = self._api_url
            except Exception as exc:
                base["status"] = "down"
                base["reason"] = repr(exc)
        else:
            try:
                import torch
                base["status"] = "ok"
                base["cuda_available"] = torch.cuda.is_available()
            except ImportError:
                base["status"] = "degraded"
                base["reason"] = "torch not installed"
        return base
