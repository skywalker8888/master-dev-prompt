# ZOS-SPEC-0001 — ZOS Access Registry Specification

## 1) Document Metadata
- **Document ID:** ZOS-SPEC-0001
- **Title:** ZOS Access Registry Specification
- **Version:** 1.0.0
- **Status:** Draft
- **Approval Status:** Pending Founder Approval
- **Owner:** Founder
- **Effective Date:** Pending Founder Approval
- **Supersedes:** ZOS-ACCESS-REGISTRY v1.0.0
- **Dependencies:** ZOS-CON-0001; ZOS-STD-0009 (planned)
- **Change Log:** 1.0.0 — Reclassified as SPEC and constrained to public-safe structure/template only.

## 2) Purpose
This document defines the canonical structure and empty template for the ZOS Access Registry.

It does not authorize or include live account records. It is a specification artifact only.

## 3) Constitutional Compliance Statement
This document shall not redefine governance established by ZOS-CON-0001. Where conflict exists, ZOS-CON-0001 prevails.

## 4) Public Repository Storage Rule
The public repository may contain only this specification and an empty registry template.

A populated ZOS Access Registry must be stored only in an approved private, access-controlled system.

Live access metadata must never be committed to a public repository.

## 5) Prohibited Public Populated Fields
Populated values for the following fields must never be published in a public repository:
- Login Email
- People With Access
- Vault
- Authentication Method
- Recovery Status
- API Key Present
- Permission Level
- Rotation Dates
- Expiry Dates

## 6) Registry Template (Structure Only)
| Application | Business/Project | Account Owner | Login Email | Vault | Access Type (Human / Agent / Service Account) | People With Access | Authentication Method (Passkey / Security Key / Authenticator / SMS) | Recovery Status | API Key Present | Permission Level | Last Rotated | Expiry Date | Status (Active / Review / Revoke / Archived) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |  |  |  |  |  | Draft |

## 7) Security Authority Reference
Detailed credential, password, authentication, recovery, rotation, and secrets-management controls are governed by **ZOS-STD-0009 — Security Standard** when active.
