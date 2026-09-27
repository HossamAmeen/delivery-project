# QA Report — FEAT-001 Backend Platform Foundation

QA task: TASK-009 · Tasks verified: TASK-001, TASK-002, TASK-003, TASK-004, TASK-005, TASK-016 · Plan: `qa/plans/FEAT-001-test-plan.md` · Date: 2026-09-28 (runs are timestamped in UTC on 2026-09-27)

## Verdict: **FAIL**, one Low contract deviation (BUG-001)

The only failing case is TC-001-HLT-10 (P2): the 401 responses of the health endpoints lack `Cache-Control: no-store`, which the contract requires for every response (BUG-001, Low, Backend, TASK-004). Everything else passed:
- all 10 FEAT-001 acceptance criteria have executed evidence
- every P1 case passed
- the developer suite passed on the server with 98.43% coverage

Under `qa.md` §6 there is no PASS while a case fails. The verdict turns to PASS when either:
- BUG-001 is fixed and re-tested, or
- the TL and PM accept it as a known Low deviation (DoD: no open Critical/High bugs)

BUG-002 (Low, Infrastructure) is a hygiene finding on the nginx API site. It does not affect FEAT-001's criteria and is tracked for FEAT-004.

## Scope and environment

| Item | Value |
|---|---|
| Target | `https://api.delivery.hossam-ameen.online` (live, through nginx) |
| Release | `20260927-205803`, commit `f85848b9bbdb`, `REVISION dirty=false` (from `make status`) |
| Runner | `make qa-remote` (ADR-018), suite on the server `/srv/flash/qa/suite`, Python 3.13.15, pytest 9.1.1, httpx 0.28.1 |
| Users | `qa_customer`, `qa_driver`, `qa_store`, `qa_admin`, `qa_inactive` (credentials.env, 10 variables) |
| Health token | from `shared/.env`, exported only into pytest, sent only in the header |
| Backend audit | `make test-backend-remote REF=f85848b` (server sandbox, Python 3.13.15) |

Harness changes made during this verification. They are harness corrections, and no expected business result was weakened:
- `test_health.py`: asserts the exact `HEALTH_TOKEN_INVALID` code (TL decision) and adds TC-001-HLT-10.
- `test_envelope.py`: malformed JSON must give `PARSE_ERROR` (contract table).
- `test_users_me.py`: dropped the `"Bearer "` header case. httpx/h11 refuse to send a value with trailing whitespace, so it can never reach the server. `"Bearer"` still covers the case.
- `test_openapi_docs.py`: the docs UIs are requested with a browser `Accept` header. With `Accept: application/json`, DRF negotiates content before authentication and answers `406 NOT_ACCEPTABLE` (enveloped, listed in the contract). That is correct behaviour, not a missing permission check.
- `test_cors_security.py`: `X-Content-Type-Options` is parsed as the Fetch spec does (first value). The duplicate header is BUG-002.
- `harness/http.py`: `AuthPacer` now persists its window on the server, so back-to-back sessions stay under the auth throttle (see FEAT-003 report).
- `smoke/test_server_runtime.py`: new TC-004-RUN-13, the release venv Python version (FEAT-001 AC1).

## Commands and evidence

| # | Command | Run ID (`qa/.results/<id>/`) | Result |
|---|---|---|---|
| 1 | `make qa-remote ARGS='--collect-only -q'` | 20260927-210402-33053 | `137/142 collected (5 deselected)`, exit 0 |
| 2 | `make qa-remote ARGS="-m smoke -p no:randomly"` | 20260927-210423-33520 | 52 passed, 1 failed (HLT-10 → BUG-001), 1 skipped (dental baseline compare) |
| 3 | `make qa-remote ARGS="-m 'regression and not e2e'"` (first) | 20260927-224701-94472 | 98 passed, 8 failed: 1 = BUG-001; 7 = harness defects fixed above; the duplicate nosniff header = BUG-002 |
| 4 | `make qa-remote ARGS="api/test_openapi_docs.py api/test_users_me.py api/test_cors_security.py"` | 20260927-224943-99609 | 24 passed (after the harness fixes) |
| 5 | `make throttle-reset` → `make qa-remote ARGS="-m ratelimit -v"` → `make throttle-reset` | 20260927-225436-108557 | 4 passed, 1 skipped (RL-05 anon, TL decision). Resets removed 8 and 3 cache files |
| 6 | `make qa-remote ARGS="-m 'regression and not e2e'"` (**final**) | 20260927-225552-109762 | **104 passed, 1 failed (BUG-001), 1 skipped** (dental baseline compare). No secret found in `.results/` by the end-of-session scan |
| 7 | `make qa-remote ARGS="smoke/test_server_runtime.py -v"` | 20260927-225943-112312 | 13 passed (`release-python.txt`: `Python 3.13.15`) |
| 8 | `make test-backend-remote REF=f85848b` | `backend/.remote-results/20260927-225853-111545/` | ruff-check, ruff-format, check, makemigrations PASS; **246 passed**; coverage **98.43%** (≥ 80%); exit 0 |
| 9 | `make status` | (terminal) | `flash-backend` active + enabled, current `20260927-205803`, sha `f85848b`, cert valid 89 days |

Excerpt, final regression (run 6):
```
FAILED api/test_health.py::test_health_responses_are_not_cacheable - Assertio...
===== 1 failed, 104 passed, 1 skipped, 35 deselected in 171.27s (0:02:51) ======
```
Excerpt, rate limits (run 5):
```
api/test_ratelimit.py::test_auth_scope_is_throttled PASSED
api/test_ratelimit.py::test_auth_scope_is_stricter_than_user_scope PASSED
api/test_ratelimit.py::test_user_scope_is_throttled PASSED
api/test_ratelimit.py::test_health_scope_is_throttled PASSED
api/test_ratelimit.py::test_anon_scope_is_throttled SKIPPED (no anon-scope endpoint …)
```

## Results per acceptance criterion

| AC | Result | Evidence |
|---|---|---|
| AC1: Python 3.13, one start command, server = reference runtime | **PASS** | TC-004-RUN-13: release venv `Python 3.13.15`, ExecStart runs gunicorn from `current/venv` (run 7); TC-004-RUN-01: `flash-backend` active/enabled/`Restart=always` |
| AC2: config from env only; `.env.example` documents every variable | **PASS** | TC-001-MAN-02: all 41 `env(...)` reads in `backend/config/settings/*` appear in `backend/.env.example`, and none is undocumented. Production settings refuse placeholder `SECRET_KEY`/`HEALTH_CHECK_PASSWORD` (`require_non_placeholder`). TC-001-MAN-03: only `.env.example` files are tracked; the only secret-like values in tracked files are the `__GENERATE__` placeholders in `deploy/env/shared.env.template`; no private key is tracked |
| AC3: every API error in the envelope | **PASS** | TC-001-ENV-01..08 all passed: 400 fields, 400 `PARSE_ERROR`, 401 `NOT_AUTHENTICATED`, 403 `PERMISSION_DENIED`, 404 `NOT_FOUND` on an unknown `/api/` path, 405 `METHOD_NOT_ALLOWED`, no internals leaked. 429 `THROTTLED` + `Retry-After` in run 5. 406 `NOT_ACCEPTABLE` enveloped (observed). 500: backend audit `test_unexpected_exception_returns_generic_500_and_is_logged` passed (run 8) |
| AC4: health valid/invalid/missing; token never exposed | **PASS** except BUG-001 | TC-001-HLT-01..09 passed (exact `HEALTH_TOKEN_INVALID`; wrong `?password=` rejected and not echoed; token in no body or header). Readiness `database ok, cache ok, celery skipped`. Token also absent from the PWA bundle (TC-003-WEB-05), the `flash-backend` journal and the Flash nginx logs (TC-004-RUN-10/11, count-only). **HLT-10 FAILED → BUG-001** (no `no-store` on 401) |
| AC5: anon/user/auth/health limits; 429 envelope | **PASS** | Live: auth (10/min, request 11 → 429, refresh also 429), user (300/min), health (120/min, then `/api/health/` also 429). Each 429 arrived at exactly limit + 1 through 2 gunicorn workers, so the counters are shared (FileBasedCache, ADR-017). **Anon:** TL decision; the backend suite on the server (run 8 JUnit) shows `test_anonymous_user_uses_anonymous_throttle` and `test_api_rejects_requests_after_rate_limit` passed (TC-001-MAN-05). TC-001-RL-05 is skipped by design |
| AC6: JWT, username + password, 4 roles, indistinguishable failures | **PASS** | TC-001-JWT-01..16 and ME-01..04 passed. Each role gets the right `role`, and `is_staff` only for ADMIN. Unknown user, wrong password and **inactive user (`qa_inactive`, TASK-016)** give identical 401 bodies. Case-sensitive. Tampered, forged, `alg:none`, refresh-as-access and access-as-refresh tokens are all rejected with `TOKEN_INVALID`. No rotation. Lifetimes 30 min / 7 d. Role is read-only |
| AC7: OpenAPI + docs available, document 429 | **PASS** | TC-001-DOC-01..08: staff reads raw OpenAPI 3; anonymous → 401, non-staff → 403 (schema, docs, redoc); all contract paths are present; every operation documents 429; bearer scheme declared. Admin session opens the schema (ADM-04) |
| AC8: admin staff-only | **PASS** | TC-001-ADM-01..03: anonymous → 302 login; customer/driver/store cannot log in to `/admin/`; `qa_admin` can, and the session/CSRF cookies are `Secure` |
| AC9: suite ≥ 80%, check, makemigrations, on the server | **PASS** | Run 8: 246 passed, 98.43%, all steps PASS on Python 3.13.15 at the deployed commit |
| AC10: `CELERY_ENABLED=False`, no Redis | **PASS** | Readiness `celery: skipped` (HLT-07); TC-004-RUN-09: no Flash Celery unit, nothing on 6379 |
| QA contract #15: permissions | **PASS** | ME-01/04, DOC-02..05, ADM-01..04, SEC-01..02 (CORS allows only the PWA origin) |

## Cases not executed / gaps

| Case | Reason | Covered by |
|---|---|---|
| TC-001-RL-05 (anon scope, live) | No public anon-scoped endpoint in sprint-01 (TL decision) | Backend suite on the server (run 8), cited above |
| TC-001-JWT-16b (genuinely expired, validly signed access token) | Needs a 30-minute wait; not run in this session | Forged-`exp` variant JWT-16 passed. The simplejwt expiry path is covered by the developer suite. **P2 gap**, to run in a later regression |
| TC-001-DOC-09 (field-by-field schema vs contract) | Partially done: paths, 429 and the bearer scheme are automated; request/response bodies were compared against live responses by the API tests | P2 gap for a full manual diff |
| Readiness 503 (`SERVICE_NOT_READY`) | Cannot be caused safely on the shared server | Backend suite: `test_readiness_reports_database_failure_as_503`, `…cache_failure_as_503`, `…broker_down_is_503` passed (run 8) |

## Bugs

| ID | Severity | Area | Summary | Status |
|---|---|---|---|---|
| [BUG-001](bugs/BUG-001-health-401-missing-no-store.md) | Low | Backend (TASK-004) | `/api/health/*` 401 (and by code, 503) responses lack `Cache-Control: no-store` | OPEN |
| [BUG-002](bugs/BUG-002-api-duplicate-nosniff-header.md) | Low | Infrastructure (TASK-013) | `X-Content-Type-Options: nosniff, nosniff` on proxied API responses | OPEN |

## Task outcomes

| Task | Outcome |
|---|---|
| TASK-001 (skeleton/settings/env) | QA PASS (AC1, AC2, AC9) |
| TASK-002 (common: envelope, pagination, throttling) | QA PASS (AC3, AC5) |
| TASK-003 (users, roles, JWT) | QA PASS (AC6, AC8, #15) |
| TASK-004 (OpenAPI, Jazzmin, health) | **QA_FAILED**: BUG-001 (Low). Everything else in AC4/AC7 passed |
| TASK-005 (cache/Celery config) | QA PASS (AC10, shared throttle cache) |
| TASK-016 (`create_role_user --inactive`) | QA PASS (`qa_inactive` seeded; TC-001-JWT-07 passed) |

Re-test after the fix: `make qa-remote ARGS="api/test_health.py"`, then the full regression (`-m 'regression and not e2e'`).
