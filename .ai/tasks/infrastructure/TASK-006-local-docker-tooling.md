# Task

## ID
TASK-006

## Title
Local Docker environment & root ops tooling

## Feature
FEAT-001 — Backend Platform Foundation

## Description
Provide the containerized local environment under the ADR-012 layout:
- the backend Dockerfile and its entrypoint scripts
- the local compose file
- the first version of the root `Makefile` and the root `.env.example`

With these, `make up` brings up a working backend on Python 3.13.

## Business Requirement
REQ-002; DRF_SKILL.md §41–42, §52, §57; ADR-009, ADR-012; FEAT-001 criterion 1

## Agent
Infrastructure

## Scope (allowed paths)
- `deploy/docker/backend/**`, `deploy/docker/compose/local.yml`
- root `Makefile` (local targets only: `up`, `down`, `logs`, `ps`, `backend-shell`, `backend-test`)
- root `.env.example` (local and deployment basics: `APP_NAME`, `APP_ENV`, `DEPLOYMENT_MODE`, `BACKEND_PORT`, `DOCKER_COMPOSE_FILE`, `BACKEND_SERVICE`, `HEALTH_CHECK_PASSWORD`)
- `deploy/README.md` (the "Local development" section only)

## Dependencies
- TASK-001 (requirements files, settings), TASK-005 (cache/Celery toggles)
- TASK-003 before final verification (`migrate` needs the custom user model, ADR-003)
- TASK-004 for the container health check (uses `/api/health/`)

## Acceptance Criteria

- [ ] `deploy/docker/backend/Dockerfile`: `python:3.13-slim`, multi-stage, non-root user, production-capable (gunicorn), and `requirements/development.txt` only in the dev target.
- [ ] `deploy/docker/backend/entrypoint.sh` + `wait_for_db.sh`: wait for the DB when `DATABASE_URL` is Postgres, run migrations only when `RUN_MIGRATIONS=true` (local default), then exec the command. `set -euo pipefail`.
- [ ] `docker compose -f deploy/docker/compose/local.yml config` validates. The backend is reachable on `${BACKEND_PORT}`. Redis and Postgres sit behind compose profiles (`redis`, `postgres`) and are not started by default.
- [ ] The container healthcheck calls `/api/health/` with the `X-Health-Check-Token` header from the env, without printing it.
- [ ] `make up` / `make down` / `make backend-test` work. `make backend-test` runs pytest inside the container on Python 3.13.
- [ ] No secrets in the Dockerfile, compose file or Makefile. `.env` is git-ignored.
- [ ] `deploy/README.md` documents the local workflow.

## Technical Notes

- The build context is the repo root, so the image can copy `backend/`.
- Staging/production compose files, Nginx, systemd, the SSH deploy scripts and rollback are **FEAT-004** (sprint-02). Do not create them now, but use names and variables that stay compatible with ADR-012 and ADR-013.
- `backend/Makefile` belongs to Backend (TASK-001). Coordinate with the TL so its `docker-local` target delegates to `make -C .. up`.

## Testing Requirements

- `docker compose … config`, image build, `make up`, the health check green, and `make backend-test` passing. Record the commands and their output in the Completion Report.
- `bash -n` / `shellcheck` on the scripts.

## Plan Review Required
Yes — first infrastructure design (ADR-012 layout in practice)

## Status

TODO

## Activity Log
- 2026-09-27 | team-lead | — → TODO | created from sprint-01 technical plan (as Backend task)
- 2026-09-27 | team-lead | TODO → TODO | reassigned Backend → Infrastructure, scope moved to `deploy/` (ADR-012)

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
