"""
Unit tests for Pydantic models and JobRecord helpers.
"""

from datetime import datetime

import pytest

from video_backend.models import GenerateRequest, JobRecord, JobResponse, JobStatus


def test_generate_request_valid():
    req = GenerateRequest(prompt="A simple test")
    assert req.prompt == "A simple test"
    assert req.num_frames is None
    assert req.fps is None


def test_generate_request_prompt_too_long():
    with pytest.raises(Exception):
        GenerateRequest(prompt="x" * 2001)


def test_generate_request_num_frames_bounds():
    with pytest.raises(Exception):
        GenerateRequest(prompt="test", num_frames=5)  # below ge=8
    with pytest.raises(Exception):
        GenerateRequest(prompt="test", num_frames=201)  # above le=200


def test_job_record_defaults():
    req = GenerateRequest(prompt="hello")
    record = JobRecord(job_id="abc-123", request=req)
    assert record.status == JobStatus.PENDING
    assert record.video_url is None
    assert record.error is None
    assert isinstance(record.created_at, datetime)


def test_job_record_to_response():
    req = GenerateRequest(prompt="test prompt")
    record = JobRecord(job_id="xyz", request=req)
    resp = record.to_response()
    assert isinstance(resp, JobResponse)
    assert resp.job_id == "xyz"
    assert resp.prompt == "test prompt"
    assert resp.status == JobStatus.PENDING
