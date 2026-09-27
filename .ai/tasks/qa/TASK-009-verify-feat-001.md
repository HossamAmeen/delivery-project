# Task

## ID
TASK-009

## Title
Independent verification of FEAT-001

## Feature
FEAT-001 — Backend Platform Foundation

## Description
Verify FEAT-001 **on the server** (REQ-009) against its acceptance criteria, DRF_SKILL.md health/rate-limit requirements and security expectations; audit the developer suite by running it on the server's Python 3.13; produce the QA report and bugs.

## Business Requirement
FEAT-001 criteria 1–10; DRF_SKILL.md §23–27, §61–83; api-contracts.md § Foundation + § Identity; ADR-017, ADR-018, ADR-019

## Agent
QA

## Scope (allowed paths)
- `qa/**`, `.ai/reports/qa/**`

## Dependencies
- TASK-001…TASK-005 READY_FOR_QA; TASK-008; TASK-014 (deployed instance, READY_FOR_QA); `make seed-qa-users` done
- Not TASK-006 (BACKLOG) and not TASK-011 (BLOCKED on BLK-012; FEAT-001 AC11 is deferred)

## Acceptance Criteria

- [ ] Each FEAT-001 criterion 1–10 has at least one executed case with evidence, all executed via `make qa-remote` against `https://api.delivery.hossam-ameen.online`.
- [ ] Envelope verified for 400/401/403/404/405/429/500-equivalent paths, including `errors.code` values from api-contracts.md.
- [ ] Health: valid/invalid/missing token (header), a wrong `?password=`, no secret in body/headers; readiness `database`/`cache` ok and `celery` skipped; `/api/status/` public and minimal.
- [ ] Rate limits: anon, user, auth (stricter) and health scopes return the 429 envelope after the configured limit, consistently across gunicorn workers (FileBasedCache, ADR-017).
- [ ] JWT with **username + password**: obtain/refresh/invalid/inactive (same 401 message)/expired or tampered; each role (`qa_customer`, `qa_driver`, `qa_store`, `qa_admin`) can authenticate and read `/api/users/me/` with the right role.
- [ ] Admin (`/admin/`) inaccessible to non-staff; OpenAPI reachable with the `qa_admin` token and denied to non-staff/anonymous (ADR-019), and documents 429.
- [ ] The deployed app runs with `CELERY_ENABLED=False` and no Redis (readiness + `systemctl` evidence from TASK-014 report re-checked).
- [ ] Developer suite audited: `make test-backend-remote REF=<deployed commit>` reproduces `pytest --cov` ≥ 80%, `check` and `makemigrations --check` green on Python 3.13 (FEAT-001 AC9); gaps noted.
- [ ] `.ai/reports/qa/FEAT-001-qa-report.md` with PASS/FAIL verdict; bugs filed per template.

## Technical Notes

- Also check that no secrets are hardcoded (grep settings/scripts) and `.env` is not committed.
- Run the ratelimit marker last with `make throttle-reset` before and after.

## Testing Requirements

- Automated black-box tests in `qa/api/` tagged `regression` become the baseline suite.

## Plan Review Required
No

## Status

READY_FOR_RELEASE

## Activity Log
- 2026-09-27 | team-lead | — → TODO | created from sprint-01 technical plan
- 2026-09-27 | team-lead | TODO → TODO | re-scoped: verification on the server (REQ-009/ADR-018), username login, `/api/status/`, docs access; depends on TASK-014; TASK-006/011 removed from the gate
- 2026-09-28 | qa | TODO → IN_PROGRESS | started; release 20260927-205803 (f85848b) deployed
- 2026-09-28 | qa | IN_PROGRESS → READY_FOR_REVIEW | FEAT-001 verification done: verdict FAIL on BUG-001 (Low) only; all ACs evidenced (.ai/reports/qa/FEAT-001-qa-report.md); re-test on fix
- 2026-09-28 | qa | READY_FOR_REVIEW → READY_FOR_REVIEW | final verdict PASS after the BUG-001 re-test on 20260927-232246 (d6669b6)
- 2026-09-28 | team-lead | READY_FOR_REVIEW → READY_FOR_RELEASE | TL final review signed off (FEAT-001 PASS)

## Implementation Plan
(not required)

## Completion Report
- **Final verdict: PASS** (re-test 2026-09-28 on release `20260927-232246` / `d6669b6`). BUG-001 is VERIFIED and TASK-004 has QA verdict PASS ticked.
  - Full regression run `20260927-233545-139616`: 110 passed, 0 failed.
  - Rate limits run `20260927-233920-141829`: 4 passed, 1 skipped (anon, TL decision).
  - Backend suite `make test-backend-remote REF=d6669b6`: 257 passed, 98.45%.
  - Report: `.ai/reports/qa/FEAT-001-qa-report.md` (see its Re-test section).
- *First run (release `20260927-205803`):* FAIL on BUG-001 (Low) only.
- **Files changed (`qa/`):**
  - `api/test_health.py`: exact `HEALTH_TOKEN_INVALID` code, plus TC-001-HLT-10 (no-store).
  - `api/test_envelope.py`: `PARSE_ERROR`.
  - `api/test_users_me.py`: dropped the unsendable `"Bearer "` case.
  - `api/test_openapi_docs.py`: browser `Accept` for the docs UIs.
  - `api/test_cors_security.py`: nosniff parsed per the Fetch spec.
  - `harness/http.py` and `conftest.py`: `AuthPacer` persisted on the server.
  - `smoke/test_server_runtime.py`: TC-004-RUN-13, release Python 3.13.
  - `plans/FEAT-001-test-plan.md` and `plans/test-strategy.md`: TL decisions (`qa_inactive`, AC5-anon traced to the backend suite, health codes).
- **Bugs filed:**
  - `.ai/reports/qa/bugs/BUG-001-health-401-missing-no-store.md` (Low, Backend)
  - `.ai/reports/qa/bugs/BUG-002-api-duplicate-nosniff-header.md` (Low, Infrastructure, tracked for FEAT-004)
- **Validation commands run + results** (all on the server; results in `qa/.results/<run>/`):
  - Collection: `make qa-remote ARGS='--collect-only -q'`, run 20260927-210402-33053 → 137/142, exit 0.
  - Smoke: `-m smoke`, run 20260927-210423-33520 → 52 passed / 1 failed (BUG-001) / 1 skipped.
  - Final API regression: `-m 'regression and not e2e'`, run 20260927-225552-109762 → 104 passed / 1 failed (BUG-001) / 1 skipped.
  - Rate limits: `make throttle-reset` → `-m ratelimit` → `make throttle-reset`, run 20260927-225436-108557 → 4 passed / 1 skipped (anon, TL decision).
  - Runtime: `smoke/test_server_runtime.py`, run 20260927-225943-112312 → 13 passed.
  - Backend audit: `make test-backend-remote REF=f85848b`, run 20260927-225853-111545 → ruff, format, check and makemigrations PASS; 246 passed; coverage 98.43%.
- **Contract/OpenAPI changes:** none.
- **Known limitations / remaining problems:**
  - TC-001-JWT-16b (genuinely expired token after 30 min) was not run. It is a P2 gap for a later regression.
  - TC-001-DOC-09 (full field-by-field schema diff) was only partly done (P2).
  - Readiness 503 is covered by the backend suite only.

## Review Log

### Review — 2026-09-28 — team-lead — final

**Verdict:** APPROVED — TL final sign-off.
- `.ai/reports/qa/FEAT-001-qa-report.md`: final PASS after the BUG-001 re-test; all 10 AC with executed evidence; the AC5 anonymous part is traced to the backend suite evidence as decided in TASK-008's review; P2 gap TC-001-DOC-09 (full schema field diff) recorded, non-blocking.
- Live state checked read-only by the TL: `make status` → current `20260927-232246` (`d6669b6`, dirty=false), previous `20260927-205208` (from PREVIOUS), flash-backend active, NRestarts 0; `make health` ALL CHECKS PASSED; dental-clinic-backend active, MainPID 18284, NRestarts 0.

## QA Log
- 2026-09-28 | qa | FAIL (Low only) | BUG-001 open (TASK-004 QA_FAILED); BUG-002 for FEAT-004; see FEAT-001-qa-report.md
- 2026-09-28 | qa | PASS (final) | BUG-001 VERIFIED; full regression 20260927-233545-139616 green; backend 257 passed 98.45%

## Sign-off
- TL final review: ☑ (team-lead, 2026-09-28)
- QA verdict: n/a (QA's own task; its verdict is the report)
- PM acceptance: ☐
