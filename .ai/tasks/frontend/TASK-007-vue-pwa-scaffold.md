# Task

## ID
TASK-007

## Title
Vue PWA scaffold, API client & UI state components

## Feature
FEAT-003 — Frontend Foundation (Vue PWA)

## Description
Scaffold `frontend/` per ADR-008 once accepted: project setup, PWA manifest with Flash brand, role-area routing skeleton, API client (envelope/JWT refresh/error codes), and reusable loading/empty/error/unavailable components.

## Business Requirement
REQ-001, REQ-037; `01_customer_app/user_flow.md` (UI states); `06_brand/`; FEAT-003 criteria 1–5

## Agent
Frontend

## Scope (allowed paths)
- `frontend/**`

## Dependencies
- **BLK-002** / ADR-008 ACCEPTED
- FEAT-001 contracts (APPROVED in api-contracts.md)

## Acceptance Criteria

- [ ] Project builds; lint, type-check, unit tests pass.
- [ ] PWA installable (manifest, service worker, icons from `06_brand/`).
- [ ] API client: unwraps envelope; 401 → single refresh → logout; maps 403/404/429/5xx to typed errors; exposes `errors.code`.
- [ ] State components: loading, empty, error (with retry), unavailable.
- [ ] Routing skeleton for the MVP role areas decided in BLK-002 (no business screens).
- [ ] Base URL from env (`VITE_API_BASE_URL`), nothing hardcoded.

## Technical Notes

- No business screens or business logic.
- i18n setup depends on BLK-009 — structure for it but only one locale.

## Testing Requirements

- Vitest unit tests for the API client (envelope, refresh flow, error mapping) and state components.

## Plan Review Required
Yes — first frontend architecture

## Status

BLOCKED

## Activity Log
- 2026-09-27 | team-lead | — → TODO | created from sprint-01 technical plan
- 2026-09-27 | team-lead | TODO → BLOCKED | waiting on BLK-002 (ADR-008 PROPOSED)

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
