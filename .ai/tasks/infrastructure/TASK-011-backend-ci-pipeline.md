# Task

## ID
TASK-011

## Title
Backend CI pipeline

## Feature
FEAT-001 — Backend Platform Foundation

## Description
Create the backend CI pipeline on the chosen git provider (ADR-014; GitHub Actions `backend.yml` if confirmed). It runs on every push and pull request that touches `backend/` or `deploy/docker/backend/`.

## Business Requirement
REQ-002; spec §37–38, §41; DRF_SKILL.md §57; ADR-014

## Agent
Infrastructure

## Scope (allowed paths)
- `.github/workflows/backend.yml` (or the provider's equivalent)
- CI notes in `deploy/README.md` (the CI/CD section)

## Dependencies
- The git repository is initialized and pushed to a remote (pre-sprint action, user approval)
- **BLK-012** (git provider) → ADR-014 ACCEPTED
- TASK-001 (requirements, ruff, pytest config), TASK-006 (backend Dockerfile)

## Acceptance Criteria

- [ ] Stages: install (Python 3.13, dependency cache) → `ruff check` → `ruff format --check` → `python manage.py check` → `makemigrations --check` → `pytest --cov` with an **80% coverage gate** → Docker image build (no push until a registry is decided) → security (`pip-audit`, secret scan).
- [ ] The coverage report is uploaded as an artifact. The job fails when any stage fails.
- [ ] Tests run with test-only env values. No secrets are needed for CI tests, and none appear in the workflow file.
- [ ] Path filters, so frontend-only changes skip it. The workflow is concurrency-safe (older runs on the same branch are cancelled).
- [ ] `actionlint` (or an equivalent) passes, and a real pipeline run on a branch is green (link in the Completion Report).

## Technical Notes

- `frontend.yml` is added with FEAT-003. `deploy.yml` is added with FEAT-004.
- Never lower the coverage gate or skip checks to get a green build (infrastructure.md §8).

## Testing Requirements

- One run that is intentionally red (for example a lint failure on a scratch branch) proves the gate blocks, plus one green run. Link both.

## Plan Review Required
No

## Status

BLOCKED

## Activity Log
- 2026-09-27 | team-lead | — → TODO | created (Infrastructure agent introduced)
- 2026-09-27 | team-lead | TODO → BLOCKED | waiting on BLK-012 (git provider) and on git init + remote

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
