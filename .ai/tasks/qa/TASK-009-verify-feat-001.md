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

TODO

## Activity Log
- 2026-09-27 | team-lead | — → TODO | created from sprint-01 technical plan
- 2026-09-27 | team-lead | TODO → TODO | re-scoped: verification on the server (REQ-009/ADR-018), username login, `/api/status/`, docs access; depends on TASK-014; TASK-006/011 removed from the gate

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
