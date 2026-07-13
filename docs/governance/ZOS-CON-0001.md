# ZOS-CON-0001 — ZOS Constitution

## 1) Document Metadata
- **Document ID:** ZOS-CON-0001
- **Title:** ZOS Constitution
- **Version:** 1.0.0
- **Status:** Draft
- **Approval Status:** Pending Founder Approval
- **Owner:** Founder
- **Approver:** Founder
- **Effective Date:** Pending Founder Approval
- **Supersedes:** None
- **Dependencies:** None
- **Related Standards:** ZOS-STD-0001 through ZOS-STD-0010 (as defined by this constitution)
- **Change Log:** 1.0.0 — Initial draft submitted for founder review
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
2. Prompts, YAML schemas, JSON schemas, command-bar configurations, APIs, and agent configurations are implementation artifacts derived from canonical human-readable governance documents.
3. Derived artifacts must reference the canonical source document ID and version.
4. A governance document is not active unless it has: **Document ID, Version, Owner, Approval Status, and Change Log**.
5. Document IDs are unique, permanent, and must never be reused.
6. No document may claim authority outside its class or precedence level.

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
5. Amendment process: **Proposal → Review → Founder Approval → Version Increment → Effective Date → Change Log → Archive Previous Version**.

## 8) Lifecycle Statuses
- Draft
- Under Review
- Approved
- Active
- Superseded
- Archived

## 9) Normative References
The following subordinate standards are normative targets for governance rollout. Sequencing and timeline are defined by Founder-prioritized governance planning.
- ZOS-STD-0001 — Agent Operating Standard (planned)
- ZOS-STD-0002 — Evidence Standard (planned)
- ZOS-STD-0003 — Decision Standard (planned)
- ZOS-STD-0004 — Documentation Standard (planned)
- ZOS-STD-0005 — Repository Standard (planned)
- ZOS-STD-0006 — Agent Lifecycle Standard (planned)
- ZOS-STD-0007 — Project Lifecycle Standard (planned)
- ZOS-STD-0008 — Deployment Standard (planned)
- ZOS-STD-0009 — Security Standard (planned)
- ZOS-STD-0010 — Quality Assurance Standard (planned)

## 10) Ratification
This document remains in draft state until Founder approval is issued and status is updated according to lifecycle controls.

- **Ratified By:** Pending
- **Ratification Date:** Pending
- **Ratification Status:** Pending
