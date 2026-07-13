# ZOS-SOP-0001 — ZOS Fast Correction Protocol

## 1) Document Metadata
- **Document ID:** ZOS-SOP-0001
- **Title:** ZOS Fast Correction Protocol
- **Version:** 1.0.0
- **Status:** Active
- **Approval Status:** Approved
- **Owner:** Founder
- **Approver:** Founder
- **Effective Date:** 2026-07-13
- **Supersedes:** None
- **Dependencies:** ZOS-CON-0001; ZOS-STD-0001
- **Planned Normative References:** None
- **Related Authority:** ZOS-CON-0001 v1.0.0; ZOS-STD-0001 v1.0.0
- **Change Log:** 1.0.0 — Initial Fast Correction Protocol approved by Founder.
- **Compatibility:** All ZOS governance-document workflows

## 2) Constitutional Compliance Statement
“This document shall not redefine governance established by ZOS-CON-0001. Where conflict exists, ZOS-CON-0001 prevails.”

## 3) Purpose
This procedure reduces correction cycles by enforcing complete onboarding, preflight validation, one-pass correction bundles, bounded correction rounds, and diff-only reporting.

## 4) Mandatory Agent Start Pack
Before any edits, every agent must receive and confirm review of:
1. ZOS-CON-0001
2. ZOS-STD-0001
3. ZOS-GOV-INDEX
4. Approved governance document template
5. Approved governance metadata template
6. Current project status
7. Founder command

The agent must explicitly confirm these artifacts were read before editing files.

## 5) Governance Preflight (Blocking)
Before creating or changing any governance artifact, the agent must verify:
- Document class is valid.
- Document ID is valid and unique.
- Lifecycle status value is valid.
- Dependencies list includes only active dependencies.
- Planned references are separated from dependencies.
- Constitutional deference sentence is present.
- Public/private data classification is correct.
- Existing artifact, issue, or PR does not already cover the same work.
- Founder approval requirements are identified.

If any item fails, the agent must stop before editing and report the exact failing requirement.

## 6) Fixed Metadata and Document Templates
Agents must start from approved templates:
- `docs/governance/templates/ZOS-GOV-DOCUMENT-TEMPLATE.md`
- `docs/governance/templates/ZOS-GOV-METADATA-TEMPLATE.md`

Agents must not invent metadata fields, status values, document classes, or governance rules without explicit Founder approval.

## 7) Automated Governance Validator
Agents must run:
- `python3 validate_zos_governance.py`

Validator checks must include:
- Valid document prefix and ID format
- Unique document ID
- Required metadata fields
- Valid lifecycle status
- Active dependencies only
- Planned-reference separation from dependencies
- Constitutional sentence presence
- Secret detection patterns
- Public access-registry safety constraints
- Governance-index status synchronization
- Version and change-log consistency

## 8) One Correction Bundle Rule
Review feedback must be returned as one package containing:
- Critical corrections
- Required-before-merge corrections
- Recommended backlog improvements
- Explicitly rejected changes
- Exact files and sections affected
- Acceptance criteria
- Validation commands

## 9) PR Scope Separation
Do not combine unrelated governance layers in one PR unless explicitly approved as one work package.

Preferred sequencing:
1. Constitution
2. Agent Operating Standard
3. Governance Index
4. Access Registry Specification

## 10) Maximum Correction Cycles
Maximum correction rounds per task:
1. Full review
2. One correction pass
3. One verification pass

If the same failure remains after round two verification, stop and escalate for reassignment.

## 11) Diff-Only Reporting After Baseline
After the first complete report, subsequent updates must return only:
- What changed
- What remains
- Validation result
- Decision required

Do not repeat full project history unless explicitly requested.

## 12) Merge/Activation Restriction
Agents must not merge, activate, publish, or deploy governance changes without explicit Founder approval.
