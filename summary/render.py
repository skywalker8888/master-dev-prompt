"""
render_nuvana_summary — single entrypoint for Nuvana branded PDF generation.

Usage:
    from summary.render import render_nuvana_summary
    from summary.schema import SummaryConfig

    config = SummaryConfig(
        title="Sprint 14 Summary",
        subtitle="March 2026 · Nuvana Platform",
        modules=["design", "pm_summary", "actions"],
        summary_bullets=[
            "Architecture decision finalised for async job queue.",
            "Three high-priority actions identified; owners assigned.",
            "Next milestone: v1.3.0 adapter integration by EOW.",
        ],
        optional_system_note="Confidential — Nuvana internal use only.",
    )
    pdf_bytes: bytes = render_nuvana_summary(config)
"""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from summary.schema import SummaryConfig

# Pinned to the versioned template file.  When the template is bumped
# (e.g. summary_v1.2.1.html), update this constant to match.
TEMPLATE_VERSION = "1.2.0"
_TEMPLATE_FILE = f"summary_v{TEMPLATE_VERSION}.html"
_TEMPLATES_DIR = Path(__file__).parent / "templates"

_jinja_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
    keep_trailing_newline=True,
)


def render_nuvana_summary(config: SummaryConfig) -> bytes:
    """Validate *config*, render the versioned HTML template, and return PDF bytes.

    Raises:
        RuntimeError: if the template version in *config* does not match
            TEMPLATE_VERSION (catches accidental version drift).
        weasyprint.html.HTMLParseError / similar: on template rendering failure.
    """
    if config.template_version != TEMPLATE_VERSION:
        raise RuntimeError(
            f"Config requests template v{config.template_version} but "
            f"render.py is pinned to v{TEMPLATE_VERSION}. "
            "Update TEMPLATE_VERSION or regenerate the config."
        )

    # Render HTML
    template = _jinja_env.get_template(_TEMPLATE_FILE)
    html_str = template.render(
        title=config.title,
        subtitle=config.subtitle,
        modules=config.modules,
        summary_bullets=config.summary_bullets,
        optional_system_note=config.optional_system_note,
        template_version=config.template_version,
    )

    # Emit PDF via WeasyPrint
    try:
        from weasyprint import HTML  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ImportError(
            "WeasyPrint is required for PDF rendering. "
            "Install it with: pip install weasyprint"
        ) from exc

    return HTML(string=html_str, base_url=str(_TEMPLATES_DIR)).write_pdf()
