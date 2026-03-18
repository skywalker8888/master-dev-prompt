"""
SummaryConfig — strict JSON contract for the Nuvana branded summary PDF.

All fields are validated before reaching the Jinja2 template or WeasyPrint.
Callers should build this model from the output of POST /process.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field, field_validator, model_validator

# Canonical module names accepted by the template layout.
CANONICAL_MODULES = frozenset(
    {
        "design",
        "pm_summary",
        "actions",
        "implementation_plan",
        "code_suggestions",
        "architecture",
        "risk_register",
        "roadmap",
    }
)


class SummaryConfig(BaseModel):
    """Validated configuration passed to render_nuvana_summary()."""

    # Visible title on the PDF cover strip
    title: Annotated[str, Field(min_length=1, max_length=80)]

    # Subtitle / session descriptor (e.g. "Sprint 14 · 2026-03-18")
    subtitle: Annotated[str, Field(min_length=1, max_length=120)]

    # Which artifact modules are present — drives the module-badge row
    modules: Annotated[list[str], Field(min_length=1)]

    # Exactly 3 executive-summary bullets shown in the body
    summary_bullets: Annotated[list[str], Field(min_length=3, max_length=3)]

    # Optional watermark / legal note at the footer; max 120 chars
    optional_system_note: Annotated[str | None, Field(max_length=120)] = None

    # Template version — pinned so the render function can assert a match
    template_version: str = "1.2.0"

    @field_validator("modules")
    @classmethod
    def modules_must_be_canonical(cls, v: list[str]) -> list[str]:
        unknown = sorted(set(v) - CANONICAL_MODULES)
        if unknown:
            raise ValueError(
                f"Unknown module(s): {unknown}. "
                f"Allowed: {sorted(CANONICAL_MODULES)}"
            )
        # Deduplicate while preserving order
        seen: set[str] = set()
        deduped = []
        for item in v:
            if item not in seen:
                seen.add(item)
                deduped.append(item)
        return deduped

    @field_validator("summary_bullets")
    @classmethod
    def bullets_must_be_non_empty(cls, v: list[str]) -> list[str]:
        for i, bullet in enumerate(v):
            if not bullet.strip():
                raise ValueError(f"summary_bullets[{i}] must not be blank")
        return v

    @model_validator(mode="after")
    def note_length_check(self) -> SummaryConfig:
        note = self.optional_system_note
        if note is not None and len(note) > 120:
            raise ValueError(
                f"optional_system_note is {len(note)} chars; max is 120"
            )
        return self
