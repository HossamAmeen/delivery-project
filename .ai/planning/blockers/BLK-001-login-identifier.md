# Blocker

## ID

BLK-001

## Title

Login identifier and authentication method per role

## Raised By / Date

project-manager (initial discovery) — 2026-09-27

## Affects

FEAT-002 Identity & Accounts; TASK-003 (USERNAME_FIELD / JWT token request shape)

## Description

The business docs say Customers can register/login and other roles login, but not with what: email, phone number, username, or phone + OTP.

## Why It Blocks Development

The custom User model's USERNAME_FIELD, the JWT token request contract, registration validation, and uniqueness constraints all depend on it. OTP would add an SMS provider and sensitive-endpoint throttling.

## Options Considered (for the decision owner; agents must not pick one)

- A: Email + password for all roles
- B: Phone + password for all roles
- C: Phone + OTP for customers/drivers, email + password for store/admin
- D: Other

## Required Decision

Choose the identifier (and whether it is unique across roles), whether OTP is required in MVP, and whether email/phone verification is required.

## Owner

Product Owner (via PM)

## Status

RESOLVED

## Resolution

- **Decision (quoted):** "BLK-001 login identifier → RESOLVED: username + password (Django default `USERNAME_FIELD = "username"`)."
- **Decided by:** Product Owner, via orchestrator. **Date:** 2026-09-27. Recorded by PM.
- **Interpretation recorded by PM (no new rule):**
  - Every role (Customer, Driver, Store, Admin) logs in with username + password. There is one `USERNAME_FIELD`, so a username is unique across all users regardless of role.
  - OTP is not part of the MVP login (not selected).
- **Still open (not decided here, not to be invented):** whether email and/or phone are collected and verified at registration, and account onboarding/approval. These stay with **BLK-007** / FEAT-002.
- **Documents updated:** `.ai/business/business-logic.md` §2, `.ai/business/requirements.md` (REQ-011, Change Log), `.ai/planning/backlog.md` (FEAT-001, FEAT-002), `.ai/planning/sprints/sprint-01.md`.
- **Pending (not PM-writable in this session):** mirror into `flash_business_logic/00_core/02_roles_and_permissions.md` (PO-approved; orchestrator to schedule). TASK-003 Activity Log notification is carried in the sprint-01 handoff to the TL.
