# Task

## ID
TASK-005

## Title
Cache configuration & optional Celery

## Feature
FEAT-001 — Backend Platform Foundation

## Description
Configure the cache used for throttling (LocMem default, Redis via RATELIMIT_CACHE_URL) and optional Celery per DRF_SKILL.md §28–33, §70–71, §79.

## Business Requirement
REQ-002, REQ-006; DRF_SKILL.md §28–33, §70–71, §79; FEAT-001 criterion 10

## Agent
Backend

## Scope (allowed paths)
- `backend/config/celery.py`, `backend/config/__init__.py`, Cache + Celery sections of settings

## Dependencies
- TASK-001

## Acceptance Criteria

- [ ] With `CELERY_ENABLED=False` and no Redis running: Django starts, `check` passes, tests pass.
- [ ] With `CELERY_ENABLED=True`: Celery app configured from `CELERY_*` settings and autodiscovers tasks.
- [ ] Cache backend: LocMem unless `RATELIMIT_CACHE_URL` is set; production settings require a shared cache when `RATELIMIT_CACHE_URL` present.
- [ ] All Celery/cache variables in `.env.example`.

## Technical Notes

- Celery import must not fail if the `celery` package is installed but broker unreachable.
- Keep Redis DB separation: 0 broker, 1 results, 2 throttle cache.
- Trusted proxy settings (`SECURE_PROXY_SSL_HEADER`, and client IP resolution for throttling behind Nginx) configured from env and documented for the Infrastructure agent (DRF_SKILL §74).

## Testing Requirements

- Settings tests for both toggle states and both cache modes.
- A trivial eager-mode task test proving the wiring (can live in `backend/tests/`).

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
