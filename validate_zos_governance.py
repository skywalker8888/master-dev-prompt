#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REQUIRED_METADATA_FIELDS = [
    "Document ID",
    "Title",
    "Version",
    "Status",
    "Approval Status",
    "Owner",
    "Approver",
    "Effective Date",
    "Supersedes",
    "Dependencies",
    "Planned Normative References",
    "Related Authority",
    "Change Log",
    "Compatibility",
]

VALID_STATUS_VALUES = {"Draft", "Under Review", "Approved", "Active", "Superseded", "Archived"}
VALID_DOC_CLASSES = {"CON", "STD", "POL", "SOP", "SPEC", "TEST", "ARCH", "ADR", "PLAN", "TASK", "REP"}
CONSTITUTIONAL_SENTENCE = (
    "This document shall not redefine governance established by ZOS-CON-0001. "
    "Where conflict exists, ZOS-CON-0001 prevails."
)
DOC_ID_RE = re.compile(r"^ZOS-([A-Z]+)-(\d{4})$")
METADATA_RE = re.compile(r"^- \*\*(.+?):\*\*\s*(.+?)\s*$", re.MULTILINE)
INDEX_ROW_RE = re.compile(
    r"^\|\s*(ZOS-[A-Z]+-\d{4})\s*\|\s*[^|]+?\s*\|\s*([^|]+?)\s*\|\s*[^|]+?\s*\|\s*([^|]+?)\s*\|",
    re.MULTILINE,
)
SEPARATOR_SPLIT_RE = re.compile(r"[;,]")
DOC_REF_RE = re.compile(r"(ZOS-[A-Z]+-\d{4})")

SECRET_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"ghp_[A-Za-z0-9]{36,}"),
    re.compile(r"-----BEGIN (?:RSA|EC|OPENSSH|PRIVATE) KEY-----"),
    re.compile(r"(?i)\bapi[_-]?key\b\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}"),
]


@dataclass
class GovernanceDoc:
    path: Path
    doc_id: str
    metadata: dict[str, str]
    content: str


def _split_field_values(value: str) -> list[str]:
    stripped = value.strip()
    if stripped in {"", "None", "—"}:
        return []
    return [item.strip() for item in SEPARATOR_SPLIT_RE.split(stripped) if item.strip()]


def _extract_doc_refs(value: str) -> list[str]:
    return DOC_REF_RE.findall(value)


def _parse_governance_docs(governance_dir: Path) -> list[GovernanceDoc]:
    docs: list[GovernanceDoc] = []
    for path in sorted(governance_dir.glob("ZOS-*.md")):
        if "templates" in path.parts:
            continue
        content = path.read_text(encoding="utf-8")
        metadata = {k.strip(): v.strip() for k, v in METADATA_RE.findall(content)}
        doc_id = metadata.get("Document ID", path.stem)
        docs.append(GovernanceDoc(path=path, doc_id=doc_id, metadata=metadata, content=content))
    return docs


def _validate_access_registry_template(doc: GovernanceDoc, errors: list[str]) -> None:
    if doc.doc_id != "ZOS-SPEC-0001":
        return
    if re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", doc.content):
        errors.append(f"{doc.path}: populated email-like value found in public access-registry specification.")

    lines = [line.strip() for line in doc.content.splitlines() if line.strip().startswith("|")]
    for line in lines:
        if line.startswith("|---") or "Application | Business/Project" in line:
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 14:
            continue
        protected = cells[:-1]
        if any(value.strip() for value in protected if value.strip()):
            errors.append(f"{doc.path}: populated access-registry row found in public specification.")
            break


def validate_governance(governance_dir: Path) -> list[str]:
    errors: list[str] = []
    docs = _parse_governance_docs(governance_dir)
    doc_by_id: dict[str, GovernanceDoc] = {}

    for doc in docs:
        match = DOC_ID_RE.match(doc.doc_id)
        if not match:
            if doc.doc_id == "ZOS-GOV-INDEX":
                doc_by_id[doc.doc_id] = doc
                continue
            errors.append(f"{doc.path}: invalid Document ID format '{doc.doc_id}'.")
            continue

        doc_class = match.group(1)
        if doc_class not in VALID_DOC_CLASSES:
            errors.append(f"{doc.path}: unsupported document class '{doc_class}'.")

        if doc.doc_id in doc_by_id:
            errors.append(f"Duplicate Document ID detected: {doc.doc_id}.")
        else:
            doc_by_id[doc.doc_id] = doc

    for doc in docs:
        if doc.doc_id == "ZOS-GOV-INDEX":
            continue
        missing_fields = [field for field in REQUIRED_METADATA_FIELDS if field not in doc.metadata]
        if missing_fields:
            errors.append(f"{doc.path}: missing metadata fields: {', '.join(missing_fields)}.")

        status = doc.metadata.get("Status")
        if status and status not in VALID_STATUS_VALUES:
            errors.append(f"{doc.path}: invalid lifecycle status '{status}'.")

        if CONSTITUTIONAL_SENTENCE not in doc.content:
            errors.append(f"{doc.path}: constitutional compliance sentence missing.")

        version = doc.metadata.get("Version", "")
        change_log = doc.metadata.get("Change Log", "")
        if version and change_log and not change_log.startswith(f"{version}"):
            errors.append(f"{doc.path}: Change Log does not start with Version '{version}'.")

        for pattern in SECRET_PATTERNS:
            match = pattern.search(doc.content)
            if match:
                preview = match.group(0).replace("\n", " ")[:32]
                errors.append(f"{doc.path}: potential secret detected ({pattern.pattern}) near '{preview}...'.")

        dependencies = _split_field_values(doc.metadata.get("Dependencies", ""))
        planned_refs = _split_field_values(doc.metadata.get("Planned Normative References", ""))
        dep_doc_refs: list[str] = []
        planned_doc_refs: list[str] = []
        for dep in dependencies:
            dep_doc_refs.extend(_extract_doc_refs(dep))
            if "planned" in dep.lower():
                errors.append(f"{doc.path}: planned item found in Dependencies: '{dep}'.")
        for ref in planned_refs:
            planned_doc_refs.extend(_extract_doc_refs(ref))

        overlap = sorted(set(dep_doc_refs) & set(planned_doc_refs))
        if overlap:
            errors.append(f"{doc.path}: document(s) listed in both Dependencies and Planned Normative References: {', '.join(overlap)}.")

        for dep_doc_id in sorted(set(dep_doc_refs)):
            target = doc_by_id.get(dep_doc_id)
            if not target:
                errors.append(f"{doc.path}: dependency '{dep_doc_id}' does not exist.")
                continue
            dep_status = target.metadata.get("Status")
            if dep_status != "Active":
                errors.append(f"{doc.path}: dependency '{dep_doc_id}' is not Active (found: {dep_status}).")

        _validate_access_registry_template(doc, errors)

    index_doc = doc_by_id.get("ZOS-GOV-INDEX")
    if index_doc:
        for doc_id, index_status, index_version in INDEX_ROW_RE.findall(index_doc.content):
            doc = doc_by_id.get(doc_id)
            if not doc:
                continue
            real_status = doc.metadata.get("Status")
            real_version = doc.metadata.get("Version")
            if real_status and index_status.strip() != real_status:
                errors.append(
                    f"{index_doc.path}: status mismatch for {doc_id} (index: {index_status.strip()}, document: {real_status})."
                )
            if index_version.strip() not in {"—", ""} and real_version and index_version.strip() != real_version:
                errors.append(
                    f"{index_doc.path}: version mismatch for {doc_id} (index: {index_version.strip()}, document: {real_version})."
                )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate ZOS governance documents.")
    default_governance_dir = Path(__file__).resolve().parent / "docs" / "governance"
    parser.add_argument(
        "--governance-dir",
        default=str(default_governance_dir),
        help="Path to governance docs directory.",
    )
    args = parser.parse_args()

    errors = validate_governance(Path(args.governance_dir))
    if errors:
        print("Governance validation failed:")
        for item in errors:
            print(f"- {item}")
        return 1

    print("Governance validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
