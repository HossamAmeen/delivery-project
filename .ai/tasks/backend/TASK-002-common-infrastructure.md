# Task

## ID
TASK-002

## Title
Common infrastructure: base model, soft delete, errors, envelope, pagination, throttling

## Feature
FEAT-001 — Backend Platform Foundation

## Description
Implement `backend/common/` per DRF_SKILL.md §10–13, §19–20, §40, §61–72 and wire it into DRF settings.

## Business Requirement
REQ-002, REQ-006; DRF_SKILL.md §10–13, §19–20, §40, §62–72; FEAT-001 criteria 3, 5

## Agent
Backend

## Scope (allowed paths)
- `backend/common/**`, `backend/tests/**`, DRF section of `backend/config/settings/base.py`

## Dependencies
- TASK-001
- TASK-012 for server validation (`make test-backend-remote`)

## Acceptance Criteria

- [ ] `BaseModel` (created_at, modified_at, deleted_at) with `soft_delete()`/`restore()`; `ActiveManager`, `DeletedManager`, `AllManager`.
- [ ] `ApplicationError` base with `status_code`, `code`, `message`; subclasses for business conflict (409) and validation (400).
- [ ] `custom_exception_handler` returns the standard error envelope for: ValidationError, NotAuthenticated/AuthenticationFailed (401), PermissionDenied (403), Http404/NotFound, MethodNotAllowed (405), Throttled (429, message 'Request rate limit exceeded.', `Retry-After` header kept), ApplicationError, and unexpected exceptions (500, generic message, no stack trace; exception logged server-side). Every non-field error carries `errors.code` from the table in `api-contracts.md` § Error codes.
- [ ] Success responses follow `{success, message, data}` through one consistent mechanism (see Technical Notes).
- [ ] `StandardPagination` returns `data: {count, next, previous, results}`; page size + max page size from settings.
- [ ] Global throttling configured: Anon + User classes, rates for `anon`, `user`, `auth`, `sensitive`, `health` from env; `AuthRateThrottle`, `SensitiveRateThrottle`, `HealthRateThrottle` in `common/throttling.py`. `NUM_PROXIES` from env (default None locally, 1 on the server) in `REST_FRAMEWORK`.
- [ ] Coverage of `common/` ≥ 90%, measured on the server (`make test-backend-remote`).

## Technical Notes

- **Pre-approved envelope mechanism (TL, 2026-09-27):** a `common.renderers.EnvelopeJSONRenderer` set as the default renderer wraps any response whose data is not already an envelope (no top-level `success` key) into `{"success": true, "message": <message>, "data": <data>}`; errors are already enveloped by the exception handler and pass through untouched; 204 has no body. The message defaults to `"Operation completed successfully."` and a view can override it (e.g. `response.message` attribute or a small `success_response()` helper that the renderer respects). drf-spectacular views use their own renderers and stay raw. Keep `BrowsableAPIRenderer` only in development. If you prefer a different mechanism, write it in the plan and wait for TL approval.
- Error `code` values are the stable client contract (api-contracts.md § Error codes). Add any new code there in the same change (TL-owned file: list it in your Completion Report and the TL records it).
- Throttle tests: override cache to LocMem and clear it per test; override rates to small numbers.
- Do not envelope OpenAPI schema responses.

## Testing Requirements

- Model/manager tests using a test-only concrete model.
- Exception handler: one test per error type incl. 500 path (no internals leaked).
- Pagination shape.
- DRF_SKILL §77 rate-limit tests: `test_api_allows_requests_within_rate_limit`, `test_api_rejects_requests_after_rate_limit`, `test_anonymous_user_uses_anonymous_throttle`, `test_authenticated_user_uses_user_throttle`, `test_sensitive_endpoint_has_stricter_rate_limit` (auth-endpoint test lands in TASK-003).

## Plan Review Required
Yes — sets conventions all endpoints inherit. **Pre-approved** against the constraints above (envelope mechanism, error codes table): write `## Implementation Plan` (short: files, error-code list, test list) and proceed; the TL reviews it together with the code. Any deviation from the constraints needs TL approval before coding.

## Status

READY_FOR_QA

## Activity Log
- 2026-09-27 | team-lead | — → TODO | created from sprint-01 technical plan
- 2026-09-27 | team-lead | TODO → TODO | constraints added (envelope renderer, error codes, NUM_PROXIES); plan pre-approved; validation on the server (ADR-018)
- 2026-09-27 | backend | TODO → IN_PROGRESS | started after TASK-001 code complete; plan written under the pre-approved constraints
- 2026-09-27 | backend | IN_PROGRESS → READY_FOR_REVIEW | implementation + tests done; full server run `make test-backend-remote WORKTREE=1` green (run 20260927-175239-1501198: ruff, format, check, makemigrations, 238 passed, coverage 98.42%)
- 2026-09-27 | team-lead | READY_FOR_REVIEW → REVIEW | code inspection done, decisions recorded; verdict pending the TL's own server validation run (denied by the session permission policy)
- 2026-09-27 | team-lead | REVIEW → READY_FOR_QA | code review APPROVED; TL server run 20260927-204315-12107 at 0a5f845: ruff/format/check/makemigrations PASS, 238 passed, coverage 98.42%

## Implementation Plan
(backend, 2026-09-27 — follows the pre-approved constraints; no deviation)

**Files**
- `common/models.py` `BaseModel` (abstract: created_at, modified_at, deleted_at; `soft_delete()`, `restore()`, `is_deleted`), managers declared on it: `objects = ActiveManager()` (default), `deleted_objects`, `all_objects`.
- `common/managers.py` `ActiveManager`, `DeletedManager`, `AllManager`.
- `common/exceptions.py` `ApplicationError(message, code, status_code, extra)` + `BusinessConflictError` (409) + `BusinessValidationError` (400).
- `common/exception_handler.py` `custom_exception_handler`: DRF handler first, then one envelope per type; Django `Http404`/`PermissionDenied`/`ValidationError` converted; unexpected → 500 `SERVER_ERROR`, logged with `logger.exception`, transaction rolled back, no internals in the body. Headers of DRF's response (e.g. `Retry-After`, `WWW-Authenticate`) are kept.
- `common/renderers.py` `EnvelopeJSONRenderer` exactly as the Technical Notes: wraps non-enveloped data into `{success, message, data}`, message from `response.message` or the default, errors pass through, 204 → empty body. `BrowsableAPIRenderer` only in development.
- `common/responses.py` `success_response(data, message, status)` (sets `response.message`) and `is_envelope()`.
- `common/pagination.py` `StandardPagination` (page number, `page_size` query param, `API_PAGE_SIZE`/`API_MAX_PAGE_SIZE` from settings) → `data: {count, next, previous, results}`.
- `common/throttling.py` `AnonRateThrottle`, `UserRateThrottle` (DRF subclasses that read the rate at request time so settings overrides apply), `AuthRateThrottle`, `SensitiveRateThrottle`, `HealthRateThrottle` (scopes auth/sensitive/health, keyed by user id or client IP).
- `common/views.py` JSON envelope `handler404` / `handler500` for URLs outside DRF.
- Settings `# --- DRF ---`: renderer, exception handler, pagination, JWT-ready auth list, `IsAuthenticated` default, throttle classes + 5 rates from env, `NUM_PROXIES` from env (empty = None).
- Tests: root `conftest.py` (api client, user factory, cache cleared per test), `tests/testapp` (test-only concrete model + views, installed only by `config.settings.test`), `tests/test_common_*.py`.

**Error codes** (table in api-contracts.md § Error codes, plus additions for the TL to record):
`INVALID_CREDENTIALS`, `TOKEN_INVALID` (every `AuthenticationFailed`, incl. simplejwt `InvalidToken`), `NOT_AUTHENTICATED`, `PERMISSION_DENIED`, `NOT_FOUND`, `METHOD_NOT_ALLOWED`, `VALIDATION_ERROR` (only when there are no field errors), `THROTTLED`, `SERVER_ERROR`.
**New (additive, for the TL):** `PARSE_ERROR` 400 malformed body, `NOT_ACCEPTABLE` 406, `UNSUPPORTED_MEDIA_TYPE` 415, `CONFLICT` 409 (default of `BusinessConflictError`; features pass their own code such as `INVALID_TRANSITION`), `APPLICATION_ERROR` 400 (fallback of the `ApplicationError` base only). Any other `APIException` falls back to its DRF `default_code` upper-cased.

**Tests**: models/managers (create, soft delete, restore, managers), exception handler (one test per type incl. 500 with no leak and a log record), renderer (wrap, custom message, pass-through, 204, list), pagination shape + max page size, DRF_SKILL §77 throttle tests (within limit, after limit, anon uses anon, user uses user, sensitive stricter, `Retry-After`, `NUM_PROXIES=1` IP resolution), handler404/500.

## Completion Report
- Files changed: `backend/common/{__init__,apps,models,managers,exceptions,exception_handler,renderers,responses,pagination,throttling,views}.py`, DRF section of `config/settings/base.py` (+ Browsable renderer in `development.py`, JSON-only + test app in `test.py`), `handler404`/`handler500` in `config/urls.py`, `backend/conftest.py` (global fixtures: isolated cache per test, api client, user factory, throttle-rate override), `backend/tests/testapp/**` (test-only concrete model + views), tests below.
- Tests added: `tests/test_common_models.py` (8: create, modify, soft delete, idempotent soft delete, restore, managers), `tests/test_common_exception_handler.py` (22: field/non-field/Django validation, 401 NOT_AUTHENTICATED, 401 TOKEN_INVALID incl. a bad bearer, 403 DRF + Django, 404, 405 with `Allow`, PARSE_ERROR, 415, 429 with `Retry-After`, ApplicationError/BusinessConflict/BusinessValidation, fallback code, generic APIException → SERVER_ERROR, unexpected exception → 500 without internals + logged, enveloped Django 404/500), `tests/test_common_renderers.py` (17: wrap, custom message, pass-through, list, 204, raw error, pagination shape, max page size, invalid page, soft-deleted rows hidden), `tests/test_throttling.py` (11: all DRF_SKILL §77 names except the auth one (in TASK-003) + per-user keying, default-rate ordering, missing rate, `NUM_PROXIES=1` IP resolution, spoofed XFF ignored without a trusted proxy). Coverage of `common/`: 93–100% per file (exception_handler 95%, exceptions 93%, openapi 96%, pagination 94%, the rest 100%) — above the 90% target overall.
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
- Contract/OpenAPI changes: **new error codes for the TL to record in api-contracts.md § Error codes** (additive): `PARSE_ERROR` 400 (malformed body), `NOT_ACCEPTABLE` 406, `UNSUPPORTED_MEDIA_TYPE` 415, `CONFLICT` 409 (default of `BusinessConflictError`; features pass their own code), `APPLICATION_ERROR` 400 (fallback of the `ApplicationError` base only). Any other 4xx `APIException` falls back to its DRF `default_code` upper-cased; any 5xx becomes `SERVER_ERROR` with the generic message. Every `AuthenticationFailed` (incl. simplejwt `InvalidToken`, inactive/deleted user behind a valid token) maps to `TOKEN_INVALID` "Token is invalid or expired.".
- Implementation notes (within the pre-approved plan): envelope via `EnvelopeJSONRenderer` exactly as specified (`response.message` / `success_response()` for custom messages; errors pass through; 204 empty). Throttle classes are DRF subclasses that read rates at request time (DRF binds them at import, which breaks env/test overrides). When `NUM_PROXIES` is unset the throttles key on `REMOTE_ADDR` only (DRF would otherwise trust a client-supplied `X-Forwarded-For`, DRF_SKILL §74); `NUM_PROXIES=1` on the server uses the address nginx writes. Global default authentication is JWT only (session auth only on the docs views).
- Known limitations / remaining problems: `BaseModel`'s default manager hides soft-deleted rows; related-object access uses Django's base manager and still sees them (documented in the model). No unique-constraint helpers for soft-deleted rows yet (not needed until a domain model uses BaseModel).

## Review Log
- 2026-09-27 | team-lead | PLAN PRE-APPROVED (conditional) | valid while the plan follows the Technical Notes constraints and api-contracts.md § Error codes

### Review — 2026-09-27 — team-lead — code (in progress)

**Verdict:** PENDING — not issued yet. Code inspection and the decisions below are done; the TL's own validation run (`make test-backend-remote WORKTREE=1`, which executes the DRF_SKILL §57 commands on the server: `ruff check`, `ruff format --check`, `manage.py check`, `makemigrations --check --dry-run`, `pytest --cov`) was **denied by the session's permission policy** (classified as interfering with the shared server). Per team-lead.md §6 ("do not approve work without running the validation yourself") the verdict waits for that run; Backend's run `20260927-175239-1501198` (238 passed, 98.42 %) is noted but is not the TL's evidence. No blocking defect was found in the inspection.

**Checked so far (inspection):** `custom_exception_handler` (error table, Django exception conversion, 500 generic + logged + rollback, headers kept), `EnvelopeJSONRenderer` exactly per the pre-approved mechanism, pagination, throttle subclasses (rates read per request; `REMOTE_ADDR` only when `NUM_PROXIES` is unset — DRF_SKILL §74).

**Decisions on Backend's points:**
- **New error codes — ACCEPTED and recorded** in api-contracts.md § Error codes: `PARSE_ERROR` 400, `NOT_ACCEPTABLE` 406, `UNSUPPORTED_MEDIA_TYPE` 415, `CONFLICT` 409 (default of `BusinessConflictError`; features pass specific codes), `APPLICATION_ERROR` 400 (base-class fallback only), plus the rule that any other 4xx falls back to DRF's `default_code` upper-cased and is not contract until listed, and every 5xx is `SERVER_ERROR`.
- Every `AuthenticationFailed` → `TOKEN_INVALID` — ACCEPTED (matches § Identity).

**Findings (non-blocking):**
1. Throttling happens after authentication/permissions (DRF order), so 401/403 requests are not counted and no public endpoint exercises the `anon` scope in sprint-01 — recorded in api-contracts § Foundation notes; FEAT-001 AC5's anonymous part is proven by `test_anonymous_user_uses_anonymous_throttle` in the server suite (decision in TASK-008's review).

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
