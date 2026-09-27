# Task

## ID
TASK-003

## Title
Custom User model, roles, JWT authentication & role permissions

## Feature
FEAT-001 — Backend Platform Foundation

## Description
Create `apps/users` with the custom User model and role, register it in Jazzmin admin, expose simplejwt token/refresh with the `auth` throttle scope, and provide role permission classes.

## Business Requirement
REQ-010, REQ-003; `00_core/02_roles_and_permissions.md`; ADR-003; DRF_SKILL.md §17–18, §66; FEAT-001 criterion 6

## Agent
Backend

## Scope (allowed paths)
- `backend/apps/users/**`, `AUTH_USER_MODEL` + JWT sections of settings, auth routes in `backend/config/urls.py`

## Dependencies
- TASK-002
- **BLK-001** (login identifier → `USERNAME_FIELD` and token request shape). If unresolved when TASK-002 is done: set BLOCKED, and the Backend agent proceeds with TASK-004/005/006.

## Acceptance Criteria

- [ ] `users.User(AbstractUser)` + `role` field with `Role` choices CUSTOMER, DRIVER, STORE, ADMIN; `AUTH_USER_MODEL = 'users.User'`; initial migration created.
- [ ] Login identifier implemented exactly as decided in BLK-001 (unique, normalized).
- [ ] Custom manager supports `create_user`/`create_superuser` (superuser gets role ADMIN).
- [ ] Admin registration under Jazzmin; admin requires staff.
- [ ] `POST /api/auth/token/` and `/api/auth/token/refresh/` return the standard envelope; token lifetimes from env; `auth` throttle scope applied.
- [ ] Role permission classes `IsCustomer`, `IsDriver`, `IsStoreUser`, `IsPlatformAdmin` in `apps/users/permissions.py`.
- [ ] A documented way to create a user of each role for QA (management command `create_role_user` or fixture) — dev/test only.
- [ ] api-contracts.md Identity rows updated to APPROVED/ACTIVE with the real request shape.

## Technical Notes

- No registration endpoint and no profile models (FEAT-002).
- Role is not user-editable through any API.
- Do not add business rules about which role can log in where — not defined yet.

## Testing Requirements

- Model/manager tests (normalization, uniqueness, superuser role).
- JWT: obtain, refresh, invalid credentials (401 envelope), inactive user.
- `test_auth_endpoint_uses_stricter_throttle`.
- Permission class tests for each role (allow + deny).
- Admin: non-staff redirected/denied.

## Plan Review Required
Yes — authentication architecture; irreversible after first migration

## Status

TODO

## Activity Log
- 2026-09-27 | team-lead | — → TODO | created from sprint-01 technical plan

## Implementation Plan
(assignee: required before coding — wait for TL APPROVED)

## Completion Report
(assignee, when moving to READY_FOR_REVIEW)
- Files changed:
- Tests added:
- Validation commands run + results:
- Contract/OpenAPI changes:
- Known limitations / remaining problems:

## Review Log

## QA Log

## Sign-off
- TL final review: ☐
- QA verdict: ☐
- PM acceptance: ☐
