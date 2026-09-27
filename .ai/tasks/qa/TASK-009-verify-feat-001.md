# Task

## ID
TASK-009

## Title
Independent verification of FEAT-001

## Feature
FEAT-001 — Backend Platform Foundation

## Description
Verify FEAT-001 against its acceptance criteria, DRF_SKILL.md health/rate-limit requirements and security expectations; produce the QA report and bugs.

## Business Requirement
FEAT-001 criteria 1–10; DRF_SKILL.md §23–27, §61–83

## Agent
QA

## Scope (allowed paths)
- `qa/**`, `.ai/reports/qa/**`

## Dependencies
- TASK-001…TASK-006 in READY_FOR_QA (TASK-006 is Infrastructure); TASK-011 if unblocked; TASK-008

## Acceptance Criteria

- [ ] Each FEAT-001 criterion has at least one executed case with evidence.
- [ ] Envelope verified for 400/401/403/404/405/429/500-equivalent paths.
- [ ] Health: valid/invalid/missing token (header and query), no secret in body/headers; readiness behavior.
- [ ] Rate limits: anon, user, auth (stricter) and health scopes return 429 envelope after the configured limit.
- [ ] JWT: obtain/refresh/invalid/expired; each role can authenticate.
- [ ] Admin inaccessible to non-staff; OpenAPI reachable and documents 429.
- [ ] App starts with CELERY_ENABLED=False and no Redis.
- [ ] Local Docker environment (`make up`) works from a clean checkout following `deploy/README.md` only.
- [ ] If TASK-011 was delivered: CI run is green and a deliberately failing change is blocked.
- [ ] Developer test suite audited: `pytest --cov` ≥ 80% reproduced by QA; gaps noted.
- [ ] `.ai/reports/qa/FEAT-001-qa-report.md` with PASS/FAIL verdict; bugs filed per template.

## Technical Notes

- Also check that no secrets are hardcoded (grep settings/scripts) and `.env` is not committed.

## Testing Requirements

- Automated black-box tests in `qa/api/` tagged `regression` become the baseline suite.

## Plan Review Required
No

## Status

TODO

## Activity Log
- 2026-09-27 | team-lead | — → TODO | created from sprint-01 technical plan

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
