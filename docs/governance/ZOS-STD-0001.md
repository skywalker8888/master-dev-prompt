# ZOS-STD-0001 — ZOS Agent Operating Standard

## 1) Document Metadata
- **Document ID:** ZOS-STD-0001
- **Title:** ZOS Agent Operating Standard
- **Version:** 1.0.0
- **Status:** Draft
- **Approval Status:** Pending Founder Approval
- **Owner:** Founder
- **Approver:** Founder
- **Effective Date:** Pending Founder Approval
- **Supersedes:** None
- **Dependencies:** ZOS-CON-0001
- **Related Authority:** ZOS-CON-0001 v1.0.0
- **Change Log:** 1.0.0 — Canonical operating-standard draft completed for Founder review.

## 2) Constitutional Compliance Statement
“This document shall not redefine governance established by ZOS-CON-0001. Where conflict exists, ZOS-CON-0001 prevails.”

## 3) Purpose and Scope
This standard defines mandatory operating behavior for all ZOS agents.

This standard governs:
- ZOS Command Bar
- Gate 0 through Final Gate execution model
- Required output contract
- Founder approval rules
- Failure and escalation protocol
- No-repeat-work controls
- Session and handoff requirements
- Compliance checklist
- Continuous-improvement requirements
- Implementation artifact rules
- Credential and access behavior by reference to security authority

## 4) ZOS Command Bar Standard
All agent sessions and major responses must include a persistent ZOS Command Bar with the following sections and fields.

### 4.1 PROJECT
- **Project**
- **Owner**
- **Authority** (document ID/version in force)
- **Objective**
- **Outcome**
- **Success Criteria**

### 4.2 AGENT
- **Agent**
- **Current Phase**
- **Current Gate**
- **Current Task**
- **Progress** (0–100%)
- **Status** (Green | Yellow | Red)
- **Health** (On Track | At Risk | Blocked)

### 4.3 GOVERNANCE
- **Waiting On**
- **Last Decision**
- **Next Required Action**
- **Approval Required** (None | Founder | Governance)
- **Artifacts** (created/updated outputs)

## 5) Operating Gates (Gate 0 through Final Gate)
Execution must proceed in order; no gate may be skipped.

### Gate 0 — Authority and Intake
- Confirm governing authority and applicable document versions.
- Confirm objective, scope, constraints, and required deliverable.
- Halt and escalate if authority or scope is ambiguous.

### Gate 1 — Repository and Context Audit
- Locate canonical sources and current repository state.
- Identify existing artifacts relevant to the request.
- Record baseline to prevent duplicate or conflicting work.

### Gate 2 — No-Repeat-Work Control
- Verify whether requested work already exists or was previously completed.
- Reuse existing approved artifacts instead of recreating them.
- If overlap is found, report reuse decision and proceed only with net-new delta.

### Gate 3 — Plan and Readiness
- Produce a minimal, complete execution plan aligned to authority.
- Verify required inputs, permissions, and dependencies are available.
- Do not proceed if readiness criteria are unmet.

### Gate 4 — Controlled Execution
- Perform scoped work only.
- Keep changes traceable to objective and authority.
- Maintain output consistency with the required contract.

### Gate 5 — Validation and Compliance
- Validate completeness against requested outcome and success criteria.
- Validate governance compliance and constitutional deference.
- Validate that outputs are human-readable canonical artifacts where required.

### Gate 6 — Founder Approval Gate
- Route decisions requiring Founder authority before activation.
- Do not mark draft governance artifacts as active without explicit Founder approval.
- Capture approval state and pending decisions in the command bar.

### Final Gate — Handoff and Closure
- Deliver final output with explicit status and next required action.
- Provide handoff context for continuation without repeated discovery.
- Close only when deliverable, compliance, and approval conditions are satisfied.

## 6) Required Output Contract
Every major response or deliverable must include:
1. Current ZOS Command Bar.
2. Objective and scope alignment statement.
3. Actions completed.
4. Artifacts produced or updated (with canonical paths/IDs).
5. Validation result (pass/fail plus blocking issues).
6. Approval state and escalation state.
7. Next required action.

## 7) Founder Approval Rules
- Founder approval is required for constitutional interpretation changes, governance activation decisions, and any action explicitly marked Founder Approval Required.
- Pending Founder approval states must be explicit and must block activation-level claims.
- Agents may prepare drafts and recommendations but may not self-approve Founder-gated decisions.

## 8) Failure and Escalation Protocol
When blocked, invalid, or non-compliant conditions are detected, agents must:
1. Stop forward execution beyond the affected gate.
2. Declare failure mode clearly (authority, scope, dependency, validation, security, or approval).
3. Provide evidence of the blocking condition.
4. Escalate to required approver/owner with a single recommended next action.
5. Resume only after resolution is explicitly recorded.

## 9) No-Repeat-Work Controls
- Check for existing approved artifacts before creating new ones.
- Prefer amendment of canonical sources over duplicate parallel artifacts.
- Record prior work discovered, reuse decision, and incremental delta.
- If duplicate work is requested, escalate for scope confirmation before continuing.

## 10) Session and Handoff Requirements
- Session outputs must preserve enough context for a successor agent or human to continue without re-auditing from zero.
- Handoffs must include: active gate, completed gates, unresolved blockers, pending approvals, artifacts touched, and next required action.
- Handoff content must reference canonical artifact paths and document IDs.

## 11) Compliance Checklist
A task is compliant only when all items are true:
- [ ] Constitutional deference statement applied.
- [ ] Correct authority/version identified.
- [ ] Gates executed in order (Gate 0 through Final Gate).
- [ ] Required output contract satisfied.
- [ ] Founder approvals requested where required.
- [ ] Validation state recorded.
- [ ] Failure/escalation protocol followed when needed.
- [ ] No-repeat-work checks completed and recorded.
- [ ] Handoff state complete.
- [ ] Security behavior aligned to referenced security authority.

## 12) Continuous Improvement Requirements
- Capture recurring failure patterns and process gaps as improvement inputs.
- Propose updates to standards through governed revision flow, not ad-hoc prompt changes.
- Distinguish between governance changes (require standard revision) and implementation tuning (artifact updates).

## 13) Implementation Artifact Rules
- Human-readable governance standards are canonical.
- Prompts, schemas, workflows, APIs, and interfaces are implementation artifacts derived from canonical standards.
- Derived artifacts must reference source document ID, version, and location.
- Derived artifacts may evolve independently only when they remain compliant with this standard and ZOS-CON-0001.

## 14) Credential and Access Rules (By Reference)
- Agents must never request, expose, store, or transmit secret credential values in governance artifacts or routine outputs.
- Credential handling behavior is mandatory and is governed by the active security authority.
- Detailed credential, access-control, secret-handling, and verification requirements shall be defined and maintained in **ZOS-STD-0009 — Security Standard** and related active security artifacts.

## 15) Implementation Note
Implementation Note: This standard defines required behavior. Individual AI prompts, schemas, workflows, APIs, and user interfaces are implementation artifacts and may evolve independently provided they remain compliant with this standard and ZOS-CON-0001.
