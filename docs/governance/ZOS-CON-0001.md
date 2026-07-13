# ZOS-CON-0001 — ZOS Constitution

## 1) Document Metadata
- **Document ID:** ZOS-CON-0001
- **Title:** ZOS Constitution
- **Version:** 1.0.0
- **Status:** Active
- **Owner:** Founder
- **Approver:** Founder
- **Effective Date:** 2026-07-13
- **Supersedes:** None
- **Dependencies:** None
- **Related Standards:** ZOS-STD-0001 through ZOS-STD-0010 (as defined by this constitution)
- **Change Log:** 1.0.0 — Initial ratified constitution
- **Compatibility:** All ZOS agents, projects, and governance artifacts

## 2) Purpose
This constitution establishes the governance layer above all ZOS standards, policies, procedures, and project artifacts. It defines how ZOS documents are identified, approved, ordered by precedence, and maintained as source of truth. It applies to every ZOS-compliant agent, team member, workflow, repository, and project. It is mandatory whenever creating, modifying, approving, or applying any ZOS governance document.

## 3) Governance Hierarchy
The top-level governance hierarchy is:
1. **ZOS-CON** (Constitution)
2. **ZOS-STD** (Standards)
3. **ZOS-POL** (Policies)
4. **ZOS-SOP** (Procedures)
5. **ZOS-SPEC / ZOS-ARCH / ZOS-ADR / ZOS-PLAN / ZOS-TASK / ZOS-TEST / ZOS-REP** (implementation and execution artifacts)

Lower levels must not conflict with higher levels. If conflict occurs, the higher-level document governs.

## 4) Document Precedence Rules
When guidance conflicts, resolve in this order:
1. ZOS Constitution (ZOS-CON)
2. Applicable ZOS Standard (ZOS-STD)
3. Applicable Policy (ZOS-POL)
4. Applicable Procedure (ZOS-SOP)
5. Approved Decision Records (ZOS-ADR)
6. Project Specifications and Plans
7. Task-level instructions

If conflict cannot be resolved with available documents, escalate for Founder decision before execution.

## 5) Source-of-Truth Rules
1. The **human-readable canonical document** is the source of truth for each governance artifact.
2. Machine-readable formats, prompts, schemas, and configurations are **derived artifacts** and must reference the canonical source document ID and version.
3. A governance document is not active unless it has: **Document ID, Version, Owner, Approval Status, and Change Log**.
4. No document may claim authority outside its class or precedence level.

## 6) Mandatory Document Classification
Every ZOS document must belong to exactly one class:
- **STD** Standard
- **POL** Policy
- **SOP** Procedure
- **SPEC** Technical Specification
- **ARCH** Architecture
- **ADR** Architecture Decision Record
- **PLAN** Project Plan
- **TASK** Work Item
- **TEST** Test Specification
- **REP** Report

## 7) Constitutional Change Control
1. Constitutional changes require explicit Founder approval.
2. Each revision must increment version, update effective date, and record change rationale.
3. Superseded constitutional versions remain archived and referenceable for audit.
4. No subordinate document may modify constitutional requirements.

## 8) Ratification
This document is ratified as the constitutional foundation for all future ZOS standards and governance artifacts.

- **Ratified By:** Founder
- **Ratification Date:** 2026-07-13
- **Ratification Status:** Approved
