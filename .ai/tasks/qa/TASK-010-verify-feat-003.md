# Task

## ID
TASK-010

## Title
Independent verification of FEAT-003

## Feature
FEAT-003 — Frontend Foundation (Vue PWA)

## Description
Verify the Vue PWA foundation against FEAT-003 criteria 1–6 **on the deployed web domain** `https://delivery.hossam-ameen.online` (REQ-009), with Playwright in `qa/e2e/` executed on the server via `make qa-remote`.

## Business Requirement
FEAT-003 criteria 1–6; ADR-008, ADR-011, ADR-019

## Agent
QA

## Scope (allowed paths)
- `qa/**`, `.ai/reports/qa/**`

## Dependencies
- TASK-007 READY_FOR_QA; TASK-008; TASK-014 (PWA deployed, READY_FOR_QA); QA users seeded

## Acceptance Criteria

- [ ] Playwright (Chromium, headless, `--workers=1`) in `qa/e2e/` at 360 px and 1280 px, run on the server via `make qa-remote ARGS="-m e2e"`.
- [ ] Installability: manifest served and valid, service worker registers, icons resolve (FEAT-003 AC1).
- [ ] Login with username + password for each QA role routes to the right role area; wrong password shows the error; logout works; deep link `https://delivery.hossam-ameen.online/driver` (and an unknown route) loads the app, not an nginx 404 (AC4, AC6).
- [ ] Status page shows *API reachable* using `/api/status/`; the built JS contains no health token and calls `https://api.delivery.hossam-ameen.online` (AC6, ADR-019).
- [ ] API client behavior: expired/invalid access token → one refresh then continue; invalid refresh → logout; 429 message shown (AC2) — use request interception where a live trigger is impractical, and say so in the report.
- [ ] State components visible in the relevant states (AC3).
- [ ] Frontend build-gate evidence (lint, type-check, unit tests, build) from TASK-007's Completion Report reviewed; any doubt re-run is requested from the TL, not run locally by QA (AC5).
- [ ] `.ai/reports/qa/FEAT-003-qa-report.md` with verdict.

## Technical Notes

- Unblocked 2026-09-27 (BLK-002 RESOLVED).
- Playwright's browser deps on the server need apt packages; `setup-server.sh --with-e2e` (TASK-012/014) installs Chromium deps once. If it is missing, file a bug for Infrastructure.

## Testing Requirements

- E2E smoke tests tagged `regression`.

## Plan Review Required
No

## Status

TODO

## Activity Log
- 2026-09-27 | team-lead | — → BACKLOG | created from sprint-01 technical plan
- 2026-09-27 | team-lead | BACKLOG → TODO | BLK-002 RESOLVED; verify on the deployed web domain via `make qa-remote` (REQ-009/ADR-018); depends on TASK-014

## Implementation Plan
(not required)

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
