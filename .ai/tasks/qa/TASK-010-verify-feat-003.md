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

READY_FOR_RELEASE

## Activity Log
- 2026-09-27 | team-lead | — → BACKLOG | created from sprint-01 technical plan
- 2026-09-27 | team-lead | BACKLOG → TODO | BLK-002 RESOLVED; verify on the deployed web domain via `make qa-remote` (REQ-009/ADR-018); depends on TASK-014
- 2026-09-28 | qa | TODO → IN_PROGRESS | started; E2E selectors confirmed against the built PWA
- 2026-09-28 | qa | IN_PROGRESS → READY_FOR_REVIEW | FEAT-003 verification done: verdict PASS (.ai/reports/qa/FEAT-003-qa-report.md)
- 2026-09-28 | team-lead | READY_FOR_REVIEW → READY_FOR_RELEASE | TL final review signed off (FEAT-003 PASS)

## Implementation Plan
(not required)

## Completion Report
- **Verdict: PASS.** FEAT-003 AC1–AC6 have executed evidence on `https://delivery.hossam-ameen.online` and every P1 case passed. TASK-007 has QA verdict PASS ticked. Report: `.ai/reports/qa/FEAT-003-qa-report.md`.
- **Files changed (`qa/`):**
  - `harness/pwa.py`: selectors confirmed against the built PWA; `data-testid` constants; 429 text.
  - `e2e/test_status_page.py`: testid-based state checks, browser API-call evidence, TC-003-E2E-20 (empty state).
  - `e2e/test_api_client_behaviour.py`: retry assertion refined, TC-003-E2E-19 (refresh not answered keeps the session).
  - `harness/http.py`: `AuthPacer` persisted on the server.
  - `plans/FEAT-003-test-plan.md`.
- **Tests added:** TC-003-E2E-19, TC-003-E2E-20. The E2E suite now has 30 tests.
- **Validation commands run + results** (on the server):
  - First run: `make qa-remote ARGS="-m e2e"`, run 20260927-224953-99845 → 27 passed / 3 failed. All 3 were harness auth-throttle carry-over between sessions; fixed.
  - Second run: 20260927-225129-104522 → 29 passed / 1 failed. Same cause, fixed.
  - Final run: 20260927-225312-107600 → **30 passed**.
  - Web serving and TLS checks passed in run 20260927-225552-109762.
  - AC5 is an evidence review of the TASK-007 Completion Report: lint, type-check, 67 unit tests and build all green. QA did not run them locally.
- **Contract/OpenAPI changes:** none.
- **Known limitations / remaining problems:**
  - Interception was used for the refresh, 429, network-failure and 5xx client behaviour (TC-003-E2E-12..17, -19), as the report states.
  - Three P2 manual items are gaps: reference screenshots (MAN-01), 403/404 UI mapping (MAN-02, covered by unit tests), and a network capture for MAN-05 (verified by code inspection instead).

## Review Log

### Review — 2026-09-28 — team-lead — final

**Verdict:** APPROVED — TL final sign-off.
- `.ai/reports/qa/FEAT-003-qa-report.md`: PASS, AC1–AC6 with executed evidence, E2E 30/30 at 360 and 1280 px, installability (covers decision (e) of the TASK-007 review).
- Live state checked read-only by the TL: `make status` → current `20260927-232246` (`d6669b6`, dirty=false), previous `20260927-205208` (from PREVIOUS), flash-backend active, NRestarts 0; `make health` ALL CHECKS PASSED; dental-clinic-backend active, MainPID 18284, NRestarts 0.

## QA Log
- 2026-09-28 | qa | PASS | FEAT-003-qa-report.md; E2E run 20260927-225312-107600

## Sign-off
- TL final review: ☑ (team-lead, 2026-09-28)
- QA verdict: n/a (QA's own task; its verdict is the report)
- PM acceptance: ☐
