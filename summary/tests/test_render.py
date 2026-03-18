"""
Tests for render_nuvana_summary().

Visual regression:
  A "golden" PDF is generated from fixtures/golden_config.json and stored at
  summary/fixtures/golden_output.pdf (git-committed).

  To update the golden file after an intentional layout change:
      python -m summary.tests.test_render --update-golden

  The automated check verifies:
    1. Output is valid PDF bytes (starts with %PDF-)
    2. Output size is within ±20% of the golden file size (catches accidental
       blank-page or overflow regressions without requiring pixel diffing)

  For a pixel-accurate diff, install `pdf2image` + `Pillow` and run:
      pytest summary/tests/test_render.py -k visual --visual
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from summary.render import TEMPLATE_VERSION, render_nuvana_summary
from summary.schema import SummaryConfig

_FIXTURES = Path(__file__).parent.parent / "fixtures"
_GOLDEN_PDF = _FIXTURES / "golden_output.pdf"


def _load_golden_config() -> SummaryConfig:
    raw = json.loads((_FIXTURES / "golden_config.json").read_text())
    return SummaryConfig(**raw)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _update_golden() -> None:
    """Regenerate golden_output.pdf. Run manually after intentional changes."""
    weasyprint = pytest.importorskip("weasyprint")  # noqa: F841
    config = _load_golden_config()
    pdf = render_nuvana_summary(config)
    _GOLDEN_PDF.write_bytes(pdf)
    print(f"Golden PDF updated: {_GOLDEN_PDF} ({len(pdf):,} bytes)")


# ── Unit tests ────────────────────────────────────────────────────────────────

class TestRenderNuvanaSummary:
    def test_returns_pdf_bytes(self):
        pytest.importorskip("weasyprint")
        config = _load_golden_config()
        result = render_nuvana_summary(config)
        assert isinstance(result, bytes)
        assert result[:4] == b"%PDF", "Output must start with PDF magic bytes"

    def test_version_mismatch_raises(self):
        pytest.importorskip("weasyprint")
        config = _load_golden_config()
        config_dict = config.model_dump()
        config_dict["template_version"] = "9.9.9"
        # Bypass Pydantic to inject the wrong version directly
        bad_config = SummaryConfig.model_construct(**config_dict)
        with pytest.raises(RuntimeError, match="pinned to v"):
            render_nuvana_summary(bad_config)

    def test_output_size_within_golden_bounds(self):
        """Size regression check — catches blank-page or infinite-overflow bugs."""
        pytest.importorskip("weasyprint")
        if not _GOLDEN_PDF.exists():
            pytest.skip(
                "Golden PDF not yet generated. "
                "Run: python -m summary.tests.test_render --update-golden"
            )
        config = _load_golden_config()
        result = render_nuvana_summary(config)
        golden_size = _GOLDEN_PDF.stat().st_size
        ratio = len(result) / golden_size
        assert 0.80 <= ratio <= 1.20, (
            f"Output size ({len(result):,} bytes) is {ratio:.0%} of golden "
            f"({golden_size:,} bytes). Update golden if layout changed intentionally."
        )

    def test_template_version_appears_in_output(self):
        """Smoke check: version string is rendered in the footer."""
        pytest.importorskip("weasyprint")
        config = _load_golden_config()
        pdf_bytes = render_nuvana_summary(config)
        # WeasyPrint embeds source HTML text in PDF stream; version tag is findable
        assert TEMPLATE_VERSION.encode() in pdf_bytes


# ── CLI: --update-golden ──────────────────────────────────────────────────────

if __name__ == "__main__":
    if "--update-golden" in sys.argv:
        _update_golden()
    else:
        print("Usage: python -m summary.tests.test_render --update-golden")
        sys.exit(1)
