"""
video_backend/models.py
-----------------------
Pydantic schemas shared across routes, job queue, and adapters.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000, description="Text prompt describing the video")
    negative_prompt: Optional[str] = Field(None, max_length=500)
    num_frames: Optional[int] = Field(None, ge=8, le=200)
    fps: Optional[int] = Field(None, ge=1, le=60)
    width: Optional[int] = Field(None, ge=64, le=1920)
    height: Optional[int] = Field(None, ge=64, le=1080)
    seed: Optional[int] = Field(None, description="Random seed for reproducibility")

    model_config = {"json_schema_extra": {
        "example": {
            "prompt": "A serene mountain lake at sunset, timelapse of clouds moving",
            "num_frames": 49,
            "fps": 8,
        }
    }}


class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    prompt: str
    created_at: datetime
    updated_at: datetime
    video_url: Optional[str] = None
    error: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class JobListResponse(BaseModel):
    jobs: list[JobResponse]
    total: int


# ---------------------------------------------------------------------------
# Internal job record (stored in the in-memory registry)
# ---------------------------------------------------------------------------


class JobRecord(BaseModel):
    job_id: str
    status: JobStatus = JobStatus.PENDING
    request: GenerateRequest
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    video_url: Optional[str] = None
    error: Optional[str] = None
    metadata: dict = Field(default_factory=dict)

    def to_response(self) -> JobResponse:
        return JobResponse(
            job_id=self.job_id,
            status=self.status,
            prompt=self.request.prompt,
            created_at=self.created_at,
            updated_at=self.updated_at,
            video_url=self.video_url,
            error=self.error,
            metadata=self.metadata,
        )
