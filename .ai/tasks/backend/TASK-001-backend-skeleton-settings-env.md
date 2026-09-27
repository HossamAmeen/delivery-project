# Task

## ID
TASK-001

## Title
Backend skeleton, split settings & environment configuration

## Feature
FEAT-001 — Backend Platform Foundation

## Description
Create `backend/` following DRF_SKILL.md §3, §7, §8, §9, §37, §45: project skeleton, split settings, django-environ configuration, DATABASE_URL, requirements files, pytest.ini, Makefile, ruff config, .gitignore, .env.example, README.

## Business Requirement
REQ-002; DRF_SKILL.md §3, §7–9, §37, §45, §78; ADR-012; FEAT-001 criteria 1, 2, 9

## Agent
Backend

## Scope (allowed paths)
- `backend/` (root files), `backend/config/**`, `backend/requirements/**`, `backend/apps/__init__.py`

## Dependencies
- none

## Acceptance Criteria

- [ ] `backend/` matches the DRF_SKILL.md §3 layout for the parts in scope (apps/ empty except `__init__.py`).
- [ ] `config/settings/{base,development,production}.py` exist; production has DEBUG off and secure defaults (secure cookies, HSTS, SSL redirect configurable by env).
- [ ] Every configurable value is read from env; `.env.example` lists all variables from DRF_SKILL §8 and §78 (incl. RATELIMIT_HEALTH, HEALTH_CHECK_PASSWORD) with safe placeholder values; `.env` is git-ignored.
- [ ] `DATABASE_URL` via dj-database-url, SQLite default.
- [ ] `requirements/{base,development,production}.txt` with pinned versions; Python 3.13 compatible.
- [ ] `pytest.ini`, `backend/Makefile` (DRF_SKILL §45 developer targets + `test-rate-limit`; `docker-*` / `deploy-*` targets delegate to the root Makefile per ADR-012), ruff configured.
- [ ] `python manage.py check` passes under Python 3.13.

## Technical Notes

- No domain apps. Do not run `migrate` before TASK-003 introduces AUTH_USER_MODEL (ADR-003) — `check` only.
- Leave clearly delimited sections in `base.py` (e.g. `# --- DRF ---`, `# --- Cache ---`, `# --- Celery ---`, `# --- OpenAPI ---`, `# --- Jazzmin ---`, `# --- Health ---`) for later tasks to fill.
- `TIME_ZONE`/`LANGUAGE_CODE` from env with neutral defaults (UTC/en) — final values pending BLK-009.

## Testing Requirements

- A settings smoke test: settings load with only `.env.example`-style values; production settings refuse to start without SECRET_KEY.

## Plan Review Required
No — standard work fully specified by DRF_SKILL.md

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
