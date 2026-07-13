# ZOS-STD-0001 — ZOS Agent Operating Standard

## 1) Document Metadata
- **Document ID:** ZOS-STD-0001
- **Title:** ZOS Agent Operating Standard
- **Version:** 1.0.0
- **Status:** Draft
- **Approval Status:** Pending Founder Approval
- **Owner:** Founder
- **Derived From:** ZOS-CON-0001
- **Effective Date:** Pending Founder Approval
- **Supersedes:** None
- **Dependencies:** ZOS-CON-0001
- **Change Log:** 1.0.0 — Initial draft baseline created under ratified constitution with access-governance controls.

## 2) Constitutional Compliance Statement
“This document shall not redefine governance established by ZOS-CON-0001. Where conflict exists, ZOS-CON-0001 prevails.”

## 3) Scope
This standard defines baseline operating requirements for ZOS agents and governance-compliant execution workflows.

This standard defines:
- ZOS Command Bar
- Agent Operating Gates
- Evidence Standard references
- Output Contract
- Founder Approval Gate
- Continuous Improvement Gate
- Failure Protocol
- Compliance Checklist
- Credential and access controls

## 4) ZOS Access System Model
ZOS access operations must be managed through four layers:
1. **Password manager (add now):** shared-vault credential management for human access.
2. **Verification-code controls (add now):** passkey or security key preferred; SMS only as fallback.
3. **Single sign-on (backlog):** organizational identity integration as team scale increases.
4. **Agent/API secrets management (add now):** dedicated service accounts, scoped secrets, rotation, and revocation.

## 5) Authentication Priority
Use this order for account authentication:
1. Passkey when supported.
2. Hardware security key for founder-critical accounts.
3. Authenticator-generated code.
4. SMS only when no stronger option exists.

## 6) ZOS Credential and Access Rule
1. Agents must never request, display, repeat, store, or commit personal passwords, master passwords, one-time verification codes, recovery codes, private keys, or unrestricted API secrets.
2. Credentials must be stored only in the approved password manager or secrets-management system.
3. Agents must use dedicated service accounts and least-privilege permissions whenever available.
4. Every application must be recorded in the ZOS Access Registry with its owner, project, access level, authentication method, recovery status, and review date.
5. Passwords and secret values must never be stored in GitHub issues, source code, chat transcripts, Notion pages, screenshots, email drafts, or ZOS project documents.
6. Founder-critical accounts must use passkeys or hardware security keys where supported and must have documented recovery procedures.
7. Shared personal accounts are prohibited when an application supports individual team accounts.
8. Temporary access must have an owner, purpose, expiry date, and revocation step.
9. Access must be reviewed when a staff member, contractor, tool, agent, or project changes status.
10. ZOS may track credential status and permissions, but never the credential value itself.

## 7) ZOS Access Registry Requirement
The ZOS Access Registry is mandatory and stores metadata only; it must never contain passwords, private keys, recovery codes, or API-secret values.

Required registry fields:
- Application
- Business/Project
- Account Owner
- Login Email
- Vault
- Access Type (Human / Agent / Service Account)
- People With Access
- Authentication Method (Passkey / Security Key / Authenticator / SMS)
- Recovery Codes Stored
- API Key Present
- Permission Level
- Renewal Cost
- Last Reviewed
- Last Rotated
- Expiry Date
- Status (Active / Review / Revoke / Archived)

## 8) Access Decisions
| Item | Decision |
|---|---|
| Password manager with shared vaults | Add now |
| Access Registry | Add now |
| Passkeys and security keys for critical accounts | Add now |
| Dedicated agent service accounts | Add now |
| Company-wide SSO | Backlog |
| Passwords inside ZOS or GitHub | Reject |
| Giving agents personal verification codes | Reject |

## 9) Implementation Note
Implementation Note: This standard defines required behavior. Individual AI prompts, schemas, workflows, APIs, and user interfaces are implementation artifacts and may evolve independently provided they remain compliant with this standard and ZOS-CON-0001.
