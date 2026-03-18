"""
Tests for MockAdapter — no GPU, no external deps.
"""

import os
import tempfile

import pytest

from video_backend.adapters.mock import MockAdapter
from video_backend.models import GenerateRequest


@pytest.fixture
def adapter():
    return MockAdapter()


@pytest.fixture
def basic_request():
    return GenerateRequest(prompt="A calm ocean at sunrise")


def test_adapter_name(adapter):
    assert adapter.name == "mock"


def test_generate_creates_file(adapter, basic_request, tmp_path):
    output = str(tmp_path / "out.mp4")
    result = adapter.generate(basic_request, output)
    assert os.path.exists(output)
    assert result.file_path == output


def test_generate_returns_correct_defaults(adapter, basic_request, tmp_path):
    output = str(tmp_path / "out.mp4")
    result = adapter.generate(basic_request, output)
    # default num_frames=49, fps=8
    assert result.num_frames == 49
    assert result.fps == 8
    assert result.duration_seconds == pytest.approx(49 / 8, rel=1e-3)


def test_generate_respects_custom_params(adapter, tmp_path):
    request = GenerateRequest(prompt="test", num_frames=24, fps=12, width=640, height=360)
    output = str(tmp_path / "out.mp4")
    result = adapter.generate(request, output)
    assert result.num_frames == 24
    assert result.fps == 12
    assert result.width == 640
    assert result.height == 360


def test_health_check(adapter):
    h = adapter.health_check()
    assert h["status"] == "ok"
    assert h["adapter"] == "mock"
