# Task

## ID
TASK-004

## Title
OpenAPI documentation, Jazzmin & Health API

## Feature
FEAT-001 — Backend Platform Foundation

## Description
Configure drf-spectacular (schema/docs/redoc, envelope + 429 documented), Jazzmin settings, and implement `/api/health/` and `/api/health/ready/` with env-configured token.

## Business Requirement
REQ-002, REQ-006; DRF_SKILL.md §21–27, §75–76; api-contracts.md § Foundation; FEAT-001 criteria 4, 7, 8

## Agent
Backend

## Scope (allowed paths)
- Health module (decide `apps/health/` vs `common/` in completion report), OpenAPI + Jazzmin + Health sections of settings, their routes in `config/urls.py`

## Dependencies
- TASK-002, TASK-005 (readiness checks the configured cache/Celery)

## Acceptance Criteria

- [ ] `/api/schema/`, `/api/docs/`, `/api/redoc/` available; production access policy decided and recorded in api-contracts.md.
- [ ] OpenAPI documents the standard envelope and a 429 response for API endpoints; bearer auth scheme declared.
- [ ] Jazzmin before `django.contrib.admin`, generic settings with site brand 'Flash' (no business coupling).
- [ ] `GET /api/health/` accepts `X-Health-Check-Token` header or `?password=`; constant-time comparison; 200 `{status: healthy}` / 401 'Invalid health check password.' when missing or wrong; `health` throttle scope.
- [ ] `GET /api/health/ready/` checks database and cache; Celery/broker only when `CELERY_ENABLED=True`; 503 with check names but no internals on failure.
- [ ] Password never appears in responses or logs.

## Technical Notes

- HEALTH_CHECK_PASSWORD has no default in production settings (fail fast if missing).
- Health endpoints do not require JWT.

## Testing Requirements

- DRF_SKILL §27: `test_health_endpoint_returns_success_with_valid_password`, `test_health_endpoint_rejects_invalid_password`, `test_health_endpoint_requires_password`, `test_health_endpoint_does_not_expose_secret`; header variant.
- Readiness: DB failure → 503; Celery disabled → not checked.
- Schema generation test (`spectacular --validate` or equivalent) and 429 presence.
- Health throttle scope test.

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
