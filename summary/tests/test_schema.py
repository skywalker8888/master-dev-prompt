"""Tests for SummaryConfig validation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from summary.schema import SummaryConfig

_FIXTURES = Path(__file__).parent.parent / "fixtures"


class TestSummaryConfig:
    def _valid(self, **overrides) -> dict:
        base = {
            "title": "Test Summary",
            "subtitle": "2026-03-18 · Test Run",
            "modules": ["design", "pm_summary"],
            "summary_bullets": ["Bullet one.", "Bullet two.", "Bullet three."],
        }
        base.update(overrides)
        return base

    def test_valid_config_parses(self):
        cfg = SummaryConfig(**self._valid())
        assert cfg.title == "Test Summary"
        assert len(cfg.summary_bullets) == 3

    def test_golden_fixture_is_valid(self):
        raw = json.loads((_FIXTURES / "golden_config.json").read_text())
        cfg = SummaryConfig(**raw)
        assert cfg.template_version == "1.2.0"
        assert len(cfg.modules) >= 1

    def test_modules_must_be_canonical(self):
        with pytest.raises(ValidationError, match="Unknown module"):
            SummaryConfig(**self._valid(modules=["design", "not_a_module"]))

    def test_modules_deduplication(self):
        cfg = SummaryConfig(**self._valid(modules=["design", "design", "pm_summary"]))
        assert cfg.modules == ["design", "pm_summary"]

    def test_summary_bullets_must_be_exactly_3(self):
        with pytest.raises(ValidationError):
            SummaryConfig(**self._valid(summary_bullets=["only one"]))
        with pytest.raises(ValidationError):
            SummaryConfig(
                **self._valid(summary_bullets=["a", "b", "c", "d"])
            )

    def test_blank_bullet_rejected(self):
        with pytest.raises(ValidationError, match="must not be blank"):
            SummaryConfig(**self._valid(summary_bullets=["ok", "  ", "ok"]))

    def test_optional_system_note_max_length(self):
        with pytest.raises(ValidationError):
            SummaryConfig(**self._valid(optional_system_note="x" * 121))

    def test_optional_system_note_absent_is_ok(self):
        cfg = SummaryConfig(**self._valid())
        assert cfg.optional_system_note is None

    def test_title_max_length(self):
        with pytest.raises(ValidationError):
            SummaryConfig(**self._valid(title="t" * 81))

    def test_empty_modules_rejected(self):
        with pytest.raises(ValidationError):
            SummaryConfig(**self._valid(modules=[]))
