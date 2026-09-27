# Task

## ID
TASK-004

## Title
OpenAPI documentation, Jazzmin & Health API

## Feature
FEAT-001 — Backend Platform Foundation

## Description
Configure drf-spectacular (schema/docs/redoc, envelope + 429 documented, staff-only in production per ADR-019), Jazzmin settings, and implement `/api/health/`, `/api/health/ready/` (env-configured token) and the public `/api/status/` (ADR-019).

## Business Requirement
REQ-002, REQ-006; DRF_SKILL.md §21–27, §75–76; api-contracts.md § Foundation (revised 2026-09-27); ADR-019; FEAT-001 criteria 4, 7, 8; FEAT-003 status page needs `/api/status/`

## Agent
Backend

## Scope (allowed paths)
- `backend/apps/health/**` (TL decision: a small `apps/health` app, no models), OpenAPI + Jazzmin + Health sections of settings, their routes in `config/urls.py`

## Dependencies
- TASK-002, TASK-005 (readiness checks the configured cache/Celery)
- TASK-012 for server validation

## Acceptance Criteria

- [ ] `/api/schema/`, `/api/docs/`, `/api/redoc/` available; when `API_DOCS_PUBLIC=False` (production default) they require a staff user (JWT bearer or session), else public (ADR-019). Non-staff: enveloped 401/403.
- [ ] OpenAPI documents the standard envelope and a 429 response for API endpoints; bearer auth scheme declared; `manage.py spectacular --validate --fail-on-warn` passes (or warnings listed and justified).
- [ ] Jazzmin before `django.contrib.admin`, generic settings with site brand 'Flash' (no business coupling).
- [ ] `GET /api/health/` accepts `X-Health-Check-Token` header or `?password=`; constant-time comparison; 200 `{status: healthy}` / 401 'Invalid health check password.' when missing or wrong; `health` throttle scope.
- [ ] `GET /api/health/ready/` checks database (a `SELECT 1`) and cache (set/get/delete of a namespaced key — works with FileBasedCache); Celery/broker only when `CELERY_ENABLED=True`, else `"skipped"`; 503 with check names but no internals on failure (contract shape).
- [ ] `GET /api/status/`: public, `health` throttle scope, `{"status":"ok"}` in the success envelope, nothing else.
- [ ] Password never appears in responses or logs.
- [ ] Tests pass on the server with `make test-backend-remote`.

## Technical Notes

- HEALTH_CHECK_PASSWORD has no default in production settings (fail fast if missing).
- Health endpoints do not require JWT.

## Testing Requirements

- DRF_SKILL §27: `test_health_endpoint_returns_success_with_valid_password`, `test_health_endpoint_rejects_invalid_password`, `test_health_endpoint_requires_password`, `test_health_endpoint_does_not_expose_secret`; header variant.
- Readiness: DB failure → 503; Celery disabled → not checked.
- Schema generation test (`spectacular --validate` or equivalent) and 429 presence.
- Health throttle scope test.

## Plan Review Required
No — contract fixed in api-contracts.md § Foundation and ADR-019

## Status

READY_FOR_QA

## Activity Log
- 2026-09-27 | team-lead | — → TODO | created from sprint-01 technical plan
- 2026-09-27 | team-lead | TODO → TODO | added public `/api/status/` and staff-only production docs (ADR-019); health module location decided (`apps/health`); readiness must work with FileBasedCache
- 2026-09-27 | backend | TODO → IN_PROGRESS | started after TASK-005 code complete (readiness uses its cache/Celery config)
- 2026-09-27 | backend | IN_PROGRESS → READY_FOR_REVIEW | implementation + tests done; full server run `make test-backend-remote WORKTREE=1` green (run 20260927-175239-1501198: ruff, format, check, makemigrations, 238 passed, coverage 98.42%)
- 2026-09-27 | team-lead | READY_FOR_REVIEW → REVIEW | code inspection done, decisions recorded; verdict pending the TL's own server validation run (denied by the session permission policy)
- 2026-09-27 | team-lead | REVIEW → READY_FOR_QA | code review APPROVED; TL server run 20260927-204315-12107 at 0a5f845: ruff/format/check/makemigrations PASS, 238 passed, coverage 98.42%

## Implementation Plan
(not required)

## Completion Report
- Files changed: `backend/apps/health/{__init__,apps,services,serializers,views,urls}.py`, `backend/apps/health/tests/{__init__,conftest,test_views}.py`, `backend/common/openapi.py` (envelope/429 postprocessing hook, `ErrorEnvelopeSerializer`, staff-only docs views — placed in `common/` because it is shared OpenAPI infrastructure, noted for the TL), OpenAPI + Jazzmin + Health sections of `config/settings/base.py` (`jazzmin` before `django.contrib.admin`, `drf_spectacular`, `apps.health`), `HEALTH_CHECK_PASSWORD` required in `production.py`, routes in `config/urls.py`, `tests/test_openapi.py`.
- Tests added: `apps/health/tests/test_views.py` (26): the four DRF_SKILL §27 tests + header variant + invalid header, empty configured password rejects all, stale bearer ignored, constant-time `hmac.compare_digest` used, health throttle scope (and not limited by `anon`), readiness ok with `celery: skipped`, token required, DB failure → 503 with names only (no path leak, logged by exception type), cache failure → 503, value-not-read-back, FileBasedCache readiness, Celery skipped/ok/broker error/not installed, 503 when Celery enabled and down; `/api/status/` public + minimal, ignores bad bearer, health scope throttle, 405. `tests/test_openapi.py` (21): `spectacular --validate --fail-on-warn` passes, expected paths present and docs views excluded, **every operation documents 429**, every 2xx documented with the envelope, bearer scheme declared, ErrorEnvelope component, docs public with `API_DOCS_PUBLIC=True` (schema raw, not enveloped), with `False`: anonymous → enveloped JSON 401, non-staff bearer → 403, staff bearer → 200, staff admin session → 200 for schema/docs/redoc. Jazzmin branding checked in `apps/users/tests/test_admin.py`.
- Validation commands run + results (server, `make test-backend-remote WORKTREE=1`, run `20260927-175239-1501198`, Python 3.13.15, HEAD 8b5dc17 + uncommitted worktree; output in `backend/.remote-results/20260927-175239-1501198/`):
  ```
  ruff-check      PASS   (All checks passed!)
  ruff-format     PASS
  check           PASS   (System check identified no issues)
  makemigrations  PASS   (makemigrations --check --dry-run: No changes detected)
  pytest          PASS   238 passed in 4.67s
  coverage        TOTAL 771 stmts, 7 miss -> 98.42% (gate 80%: reached)
  == exit code: 0
  ```
  Previous run `20260927-175219-1500937` failed 1 test (whitespace-only secret accepted by `require_non_placeholder`); fixed, then the run above passed. Locally (Python 3.12, throwaway venv, static only, no pytest per REQ-009): `ruff check .`, `ruff format --check .`, `manage.py check`, `makemigrations --check --dry-run`, `spectacular --validate --fail-on-warn` all clean.
  `manage.py spectacular --validate --fail-on-warn` (local and in the server suite): 0 warnings, 0 errors (health check-result enums named via `ENUM_NAME_OVERRIDES`).
- Contract/OpenAPI changes (for the TL to record; additive only):
  - `/api/health/` and `/api/health/ready/` 401 bodies carry `errors.code = "HEALTH_TOKEN_INVALID"` (the contract row only gave the message; TASK-002 requires a code on every non-field error).
  - `/api/health/ready/` 503 is `{"success":false,"message":"Service not ready.","errors":{"code":"SERVICE_NOT_READY","checks":{...}}}` — the contract's `checks` object plus a `code`.
  - Health responses send `Cache-Control: no-store`.
  - Docs 401/403 are the JSON error envelope (`NOT_AUTHENTICATED` / `PERMISSION_DENIED`) even though the views render YAML/HTML on success.
- Known limitations / remaining problems: Swagger UI/Redoc load their JS from the drf-spectacular default CDN (jsdelivr); fine for staff-only docs, can switch to the sidecar package later if the CSP requires it.

## Review Log
### Review — 2026-09-27 — team-lead — code (in progress)

**Verdict:** PENDING — not issued yet. Code inspection and the decisions below are done; the TL's own validation run (`make test-backend-remote WORKTREE=1`, which executes the DRF_SKILL §57 commands on the server: `ruff check`, `ruff format --check`, `manage.py check`, `makemigrations --check --dry-run`, `pytest --cov`) was **denied by the session's permission policy** (classified as interfering with the shared server). Per team-lead.md §6 ("do not approve work without running the validation yourself") the verdict waits for that run; Backend's run `20260927-175239-1501198` (238 passed, 98.42 %) is noted but is not the TL's evidence. No blocking defect was found in the inspection.

**Checked so far (inspection):** `/api/status/` (public, `health` scope, no auth classes, returns only `ok`), health token (`hmac.compare_digest`, empty never matches, header or `?password=`), readiness names-only 503, `Cache-Control: no-store`, docs permission (`API_DOCS_PUBLIC` or staff; JWT + session auth), JSON error envelope for docs 401/403.

**Decisions on Backend's points:**
- **`HEALTH_TOKEN_INVALID` (401) and `SERVICE_NOT_READY` (503, with `errors.checks`) — ACCEPTED** and written into api-contracts § Foundation rows and § Error codes; `Cache-Control: no-store` and the docs 401/403 envelope codes recorded too.
- **Docs views in `common/openapi.py` — ACCEPTED** (shared OpenAPI infrastructure next to the envelope/429 hook; `common/` is the same agent's area and the work was sequential). Recorded in ADR-019.
- **Swagger UI / Redoc JS from the jsdelivr CDN — ACCEPTED** for staff-only docs; switch to `drf-spectacular-sidecar` when a CSP is introduced (ADR-019).

### Review — 2026-09-27 — team-lead — code (final)

**Verdict:** APPROVED

**Checked:** the inspection and decisions of the in-progress review above, plus the TL's own validation run below.
- [x] Scope limited to the task; no business rules invented; authorization order respected where applicable
- [x] API contract matches `api-contracts.md` (Foundation/Identity rows and error codes updated in this review)
- [x] Tests meaningful; validation commands pass on the server; `makemigrations --check` clean (only `users/0001_initial`, non-destructive)
- [x] No hardcoded secrets/domains/ports/paths; complies with `DRF_SKILL.md` and ADR-015/017/019

**Commands run:** `make test-backend-remote REF=0a5f845` (DRF_SKILL §57 on the server, ADR-018), run `20260927-204315-12107`, ref `0a5f845` (`0a5f845768c0`), Python 3.13.15, explicit test env (`shared/.env` not read); results in `backend/.remote-results/20260927-204315-12107/`:
```
ruff-check      PASS
ruff-format     PASS
check           PASS   (manage.py check)
makemigrations  PASS   (makemigrations --check --dry-run)
pytest          PASS   238 passed in 4.94s; junit tests=238 failures=0 errors=0 skipped=0
coverage        TOTAL 771 stmts, 7 miss, 98.42% (gate 80%: reached)
== exit code: 0   (remote)
```
The local wrapper then exited 1 with `deploy/scripts/remote-test.sh: line 1: tmp: unbound variable`. That is a runner defect in the `--ref` path (EXIT trap references a `local` variable; TASK-012 sent back), **not** a test failure: every step reported PASS and the remote exit code was 0.

## QA Log

## Sign-off
- TL final review: ☐
- QA verdict: ☐
- PM acceptance: ☐
