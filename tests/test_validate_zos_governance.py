from pathlib import Path

from validate_zos_governance import validate_governance


def _write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _base_doc(doc_id: str, title: str, status: str, deps: str = "None", planned: str = "None") -> str:
    return f"""# {doc_id} — {title}

## 1) Document Metadata
- **Document ID:** {doc_id}
- **Title:** {title}
- **Version:** 1.0.0
- **Status:** {status}
- **Approval Status:** Approved
- **Owner:** Founder
- **Approver:** Founder
- **Effective Date:** 2026-07-13
- **Supersedes:** None
- **Dependencies:** {deps}
- **Planned Normative References:** {planned}
- **Related Authority:** ZOS-CON-0001 v1.0.0
- **Change Log:** 1.0.0 — Initial version.
- **Compatibility:** Test

## 2) Constitutional Compliance Statement
This document shall not redefine governance established by ZOS-CON-0001. Where conflict exists, ZOS-CON-0001 prevails.
"""


def test_validate_governance_passes_for_valid_minimal_set(tmp_path: Path) -> None:
    governance_dir = tmp_path / "docs" / "governance"
    governance_dir.mkdir(parents=True)

    _write(governance_dir / "ZOS-CON-0001.md", _base_doc("ZOS-CON-0001", "ZOS Constitution", "Active"))
    _write(
        governance_dir / "ZOS-STD-0001.md",
        _base_doc("ZOS-STD-0001", "ZOS Agent Operating Standard", "Active", deps="ZOS-CON-0001"),
    )
    _write(
        governance_dir / "ZOS-GOV-INDEX.md",
        """# ZOS-GOV-INDEX
| ID | Title | Status | Owner | Version | Constitution Reference | Dependency | Reference |
|---|---|---|---|---|---|---|---|
| ZOS-CON-0001 | Constitution | Active | Founder | 1.0.0 | — | — | — |
| ZOS-STD-0001 | Agent Operating Standard | Active | Founder | 1.0.0 | ZOS-CON-0001 | ZOS-CON-0001 | — |
""",
    )

    assert validate_governance(governance_dir) == []


def test_validate_governance_fails_when_dependency_is_planned(tmp_path: Path) -> None:
    governance_dir = tmp_path / "docs" / "governance"
    governance_dir.mkdir(parents=True)

    _write(governance_dir / "ZOS-CON-0001.md", _base_doc("ZOS-CON-0001", "ZOS Constitution", "Active"))
    _write(
        governance_dir / "ZOS-SPEC-0001.md",
        _base_doc(
            "ZOS-SPEC-0001",
            "ZOS Access Registry Specification",
            "Draft",
            deps="ZOS-CON-0001; ZOS-STD-0009 (planned)",
        ),
    )

    errors = validate_governance(governance_dir)
    assert any("planned item found in Dependencies" in error for error in errors)


def test_validate_governance_fails_when_index_status_mismatches(tmp_path: Path) -> None:
    governance_dir = tmp_path / "docs" / "governance"
    governance_dir.mkdir(parents=True)

    _write(governance_dir / "ZOS-CON-0001.md", _base_doc("ZOS-CON-0001", "ZOS Constitution", "Active"))
    _write(
        governance_dir / "ZOS-STD-0001.md",
        _base_doc("ZOS-STD-0001", "ZOS Agent Operating Standard", "Draft", deps="ZOS-CON-0001"),
    )
    _write(
        governance_dir / "ZOS-GOV-INDEX.md",
        """# ZOS-GOV-INDEX
| ID | Title | Status | Owner | Version | Constitution Reference | Dependency | Reference |
|---|---|---|---|---|---|---|---|
| ZOS-CON-0001 | Constitution | Active | Founder | 1.0.0 | — | — | — |
| ZOS-STD-0001 | Agent Operating Standard | Active | Founder | 1.0.0 | ZOS-CON-0001 | ZOS-CON-0001 | — |
""",
    )

    errors = validate_governance(governance_dir)
    assert any("status mismatch for ZOS-STD-0001" in error for error in errors)
