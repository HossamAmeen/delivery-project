# FEAT-001 — Backend Platform Foundation — Test Plan

Owner: QA · Planned in: TASK-008 · Executed in: TASK-009 · Strategy: `qa/plans/test-strategy.md`
Sources: backlog FEAT-001 AC1–AC10 (AC11 moved to FEAT-004's deferred criteria); `api-contracts.md` § Foundation, § Identity, § Error codes; ADR-015, ADR-017, ADR-018, ADR-019; DRF_SKILL §23–27, §61–83; `06_qa_contract.md` scenario 15.

**Environment:** the deployed server only (`https://api.delivery.hossam-ameen.online`), via `make qa-remote` (REQ-009). **Roles:** anonymous, `qa_customer` (CUSTOMER), `qa_driver` (DRIVER), `qa_store` (STORE), `qa_admin` (ADMIN, staff + superuser), all from `make seed-qa-users`. **Secrets:** `QA_HEALTH_TOKEN` (header only), QA passwords from `credentials.env`.

**Data setup:**
1. The deployed release is healthy: `make health` passes.
2. `make seed-qa-users` has been run.
3. `make throttle-reset` has been run before the ratelimit session.

No domain data is created.

## 1. Traceability

| AC | Criterion (short) | Test cases |
|---|---|---|
| AC1 | Python 3.13, one documented start command; server is the reference runtime | TC-001-MAN-01; TC-004-RUN-01 (service up) |
| AC2 | Config from env only; `.env.example` documents every variable | TC-001-MAN-02, TC-001-MAN-03 |
| AC3 | Every API error in the standard envelope | TC-001-ENV-01..08, TC-001-HLT-02..05/08/09, TC-001-JWT-04..16, TC-001-ME-02/03, TC-001-DOC-02..04, TC-001-RL-01..05 (429) |
| AC4 | Health with valid token; rejected without/wrong; token never exposed | TC-001-HLT-01..09, TC-001-STAT-01..03, TC-003-WEB-05 (bundle), TC-004-RUN-10/11 (logs) |
| AC5 | anon / user / auth / health rate-limited, env-configurable, 429 envelope | TC-001-RL-01..05 |
| AC6 | JWT access/refresh with username + password for the four roles; wrong username or password indistinguishable | TC-001-JWT-01..16, TC-001-ME-01..04 |
| AC7 | OpenAPI schema/docs available and document 429 | TC-001-DOC-01..08, TC-001-ADM-04 |
| AC8 | Django Admin (Jazzmin) staff-only | TC-001-ADM-01..03 |
| AC9 | Suite ≥ 80% coverage, `check`, `makemigrations --check`, run on the server (Python 3.13) | TC-001-MAN-04 |
| AC10 | Runs with `CELERY_ENABLED=False` and no Redis | TC-001-HLT-07 (celery skipped), TC-004-RUN-09 (no Celery unit, no Redis port) |
| 06_qa_contract #15 | Permissions prevent unauthorized actions | TC-001-ME-01/04, TC-001-DOC-02..05, TC-001-ADM-01..04, TC-001-SEC-01..02 |

## 2. Test cases

Level: **API** = pytest + httpx in `qa/api/`; **RUN** = `qa/smoke/` server-runtime; **MAN** = manual/exploratory on the server (command + output in the report).
Priority: **P1** = must pass for sign-off; **P2** = important, a failure is a bug but the case is not a gate by itself; **P3** = hygiene.

### 2.1 Status endpoint — `qa/api/test_status.py`
| ID | Preconditions | Steps | Expected | Level | Priority |
|---|---|---|---|---|---|
| TC-001-STAT-01 | — | `GET /api/status/` with no auth | 200. Success envelope. `data == {"status":"ok"}` | API | P1 |
| TC-001-STAT-02 | — | Same; inspect keys and text | Top-level keys are only `success`, `message`, `data`. No version, hostname, DB, sqlite, redis, celery, debug or path text | API | P1 |
| TC-001-STAT-03 | — | `GET /api/status/` with `Authorization: Bearer not-a-jwt` | 200 (or 401 `TOKEN_INVALID`). Never 5xx | API | P3 |

### 2.2 Health / readiness — `qa/api/test_health.py`
| ID | Preconditions | Steps | Expected | Level | Priority |
|---|---|---|---|---|---|
| TC-001-HLT-01 | `QA_HEALTH_TOKEN` | `GET /api/health/` with header `X-Health-Check-Token: <token>` | 200. `data == {"status":"healthy"}` | API | P1 |
| TC-001-HLT-02 | — | `GET /api/health/` with no token | 401 envelope. Message `Invalid health check password.` `errors.code` present | API | P1 |
| TC-001-HLT-03 | — | Header with a wrong token | 401, same as HLT-02 | API | P1 |
| TC-001-HLT-04 | — | `GET /api/health/?password=<wrong>` (the only use of the query variant) | 401, same as HLT-02. The wrong value is not echoed | API | P1 |
| TC-001-HLT-05 | — | Header present but empty | 401 | API | P2 |
| TC-001-HLT-06 | token | Valid and invalid calls to `/health/`, `/health/ready/`, `/status/` | The token appears in no response body or header | API | P1 |
| TC-001-HLT-07 | token | `GET /api/health/ready/` with the header token | 200. `data == {"status":"ready","checks":{"database":"ok","cache":"ok","celery":"skipped"}}` | API | P1 |
| TC-001-HLT-08 | — | `/ready/` without a token | 401 | API | P1 |
| TC-001-HLT-09 | — | `/ready/` with a wrong token | 401 | API | P1 |

Not automated: the readiness 503 shape. A DB or cache failure cannot be caused safely on the shared server. The developer-suite audit (TC-001-MAN-04) must show TASK-004's `DB failure → 503` test passing.

### 2.3 Error envelope — `qa/api/test_envelope.py`
| ID | Preconditions | Steps | Expected | Level | Priority |
|---|---|---|---|---|---|
| TC-001-ENV-01 | — | `POST /api/auth/token/` with `{}` | 400. `success:false`. `errors.username` and `errors.password` are non-empty lists | API | P1 |
| TC-001-ENV-02 | — | POST a truncated JSON body | 400 envelope with an `errors.code`. Not a 500 | API | P1 |
| TC-001-ENV-03 | — | `GET /api/users/me/` anonymous | 401. `errors.code = NOT_AUTHENTICATED`, message `Authentication credentials were not provided.` | API | P1 |
| TC-001-ENV-04 | customer token | `GET /api/schema/` as customer | 403. `errors.code = PERMISSION_DENIED` | API | P1 |
| TC-001-ENV-05 | — | `GET /api/qa-does-not-exist-404/` | 404 envelope. `errors.code = NOT_FOUND` (JSON, not an HTML page) | API | P1 |
| TC-001-ENV-06 | — | `POST /api/status/` | 405. `errors.code = METHOD_NOT_ALLOWED` | API | P1 |
| TC-001-ENV-07 | — | `GET /api/auth/token/` | 405. `METHOD_NOT_ALLOWED` | API | P2 |
| TC-001-ENV-08 | — | 404/405 paths inside and outside `/api/` | No traceback, file path, `site-packages`, `/srv/flash` or Django debug page (DEBUG off) | API | P1 |
| (429) | | see §2.8 | 429 envelope, `THROTTLED`, `Retry-After` | API | P1 |
| (500) | | cannot be triggered from outside | Covered by TC-001-MAN-04 (TASK-002 handler tests) and ENV-08 | MAN | P2 |

### 2.4 JWT — `qa/api/test_auth_jwt.py`
| ID | Preconditions | Steps | Expected | Level | Priority |
|---|---|---|---|---|---|
| TC-001-JWT-01 | QA users seeded | `POST /api/auth/token/` with valid username + password | 200. `data` keys are exactly `access` and `refresh`. Both are JWS compact tokens | API | P1 |
| TC-001-JWT-02 | token | Decode claims (no verification) | `exp−iat` = 30 min (access) and 7 d (refresh) ± 5 s. `token_type` is correct. Values are configurable through `QA_JWT_*` | API | P2 |
| TC-001-JWT-03 | token | Inspect the payload | No password, hash, email or phone claims | API | P2 |
| TC-001-JWT-04 | — | Valid username, wrong password | 401. `INVALID_CREDENTIALS`, `Invalid username or password.` | API | P1 |
| TC-001-JWT-05 | — | Unknown username vs wrong password | Identical status **and** identical JSON body | API | P1 |
| TC-001-JWT-06 | — | Username with swapped case, correct password | 401 `INVALID_CREDENTIALS` (case-sensitive login) | API | P2 |
| TC-001-JWT-07 | **inactive QA user (not seeded yet, strategy §12.1)** | Log in as the inactive user | 401. Body identical to a wrong password. **Skipped with reason until seeded** | API | P1 |
| TC-001-JWT-08 | refresh token | `POST /api/auth/token/refresh/` | 200. `data` keys = `{access}` only (no rotation). Access-type token | API | P1 |
| TC-001-JWT-09 | — | Refresh with a tampered signature | 401 `TOKEN_INVALID`, `Token is invalid or expired.` | API | P1 |
| TC-001-JWT-10 | — | Refresh using an **access** token | 401 `TOKEN_INVALID` | API | P1 |
| TC-001-JWT-11 | — | Refresh with `not.a.jwt` | 401 `TOKEN_INVALID` | API | P2 |
| TC-001-JWT-12 | — | Refresh with `{}` | 400. `errors.refresh` | API | P2 |
| TC-001-JWT-13 | token | `/api/users/me/` with a tampered-signature access token | 401 `TOKEN_INVALID` | API | P1 |
| TC-001-JWT-14 | token | Forged claims (`exp` extended, `user_id` changed) with the original signature; `alg: none` | 401 `TOKEN_INVALID` for each | API | P1 |
| TC-001-JWT-15 | token | `/me` with a **refresh** token as bearer | 401 `TOKEN_INVALID` | API | P1 |
| TC-001-JWT-16 | token | `/me` with `exp` in the past (forged) | 401 `TOKEN_INVALID` | API | P2 |
| TC-001-JWT-16b | access token saved | Wait more than 30 min, then `/me` with that genuinely expired access token (curl on the server; the token comes from a file, never argv/echo) | 401 `TOKEN_INVALID` | MAN | P2 |

### 2.5 Identity read — `qa/api/test_users_me.py`
| ID | Preconditions | Steps | Expected | Level | Priority |
|---|---|---|---|---|---|
| TC-001-ME-01 ×4 | each role | Log in and `GET /api/users/me/` | 200. `id` is an int, `username` is the seeded name, `role` is the right one of CUSTOMER/DRIVER/STORE/ADMIN, `is_staff` is true only for ADMIN. No password fields | API | P1 |
| TC-001-ME-02 | — | Anonymous `/me` | 401 `NOT_AUTHENTICATED` | API | P1 |
| TC-001-ME-03 ×4 | — | `Authorization`: `Bearer`, `Bearer `, `Token abc`, `Basic …` | 401 envelope with a code. Never 500 | API | P2 |
| TC-001-ME-04 | customer | `PATCH`/`PUT /me` with `{"role":"ADMIN","is_staff":true}`, then `GET` | Any of 200/400/403/405, but the role stays CUSTOMER and `is_staff` false (role read-only) | API | P1 |

### 2.6 OpenAPI / docs — `qa/api/test_openapi_docs.py`
| ID | Preconditions | Steps | Expected | Level | Priority |
|---|---|---|---|---|---|
| TC-001-DOC-01 | admin token | `GET /api/schema/?format=json` as `qa_admin` | 200. OpenAPI 3.x JSON, **not** enveloped | API | P1 |
| TC-001-DOC-02 | — | Anonymous schema | 401 `NOT_AUTHENTICATED` | API | P1 |
| TC-001-DOC-03 ×3 | non-staff tokens | Schema, docs and redoc as customer/driver/store | 403 `PERMISSION_DENIED` | API | P1 |
| TC-001-DOC-04 ×2 | — | Anonymous `/api/docs/`, `/api/redoc/` | 401 envelope | API | P1 |
| TC-001-DOC-05 ×2 | admin token | Docs/redoc as staff | 200 HTML | API | P2 |
| TC-001-DOC-06 | schema | Contract paths present | `/api/status/`, `/api/health/`, `/api/health/ready/`, `/api/auth/token/`, `/api/auth/token/refresh/`, `/api/users/me/` are all in `paths` | API | P1 |
| TC-001-DOC-07 | schema | Every operation's responses | Each includes `429` | API | P1 |
| TC-001-DOC-08 | schema | `components.securitySchemes` | An HTTP bearer scheme is declared | API | P2 |
| TC-001-DOC-09 | schema | Compare each contract row's request/response shape with the schema (manual reading) | Matches `api-contracts.md`. A difference is a bug (contract rule) | MAN | P2 |

### 2.7 Admin — `qa/api/test_admin.py`
| ID | Preconditions | Steps | Expected | Level | Priority |
|---|---|---|---|---|---|
| TC-001-ADM-01 | — | Anonymous `GET /admin/` | 302 to `/admin/login/` | API | P1 |
| TC-001-ADM-02 ×3 | non-staff users | Admin form login (CSRF) as customer/driver/store, then `GET /admin/` | The login form is re-rendered (200). `/admin/` still redirects to login | API | P1 |
| TC-001-ADM-03 | qa_admin | Form login as staff | 302 to `/admin/`. The index is 200 HTML. Session/CSRF cookies have `Secure` | API | P1 |
| TC-001-ADM-04 | qa_admin session | `GET /api/schema/?format=json` with the session cookie only | 200 (ADR-019: session access) | API | P2 |

### 2.8 Rate limits — `qa/api/test_ratelimit.py` (own session, last; `make throttle-reset` before and after)
| ID | Preconditions | Steps | Expected | Level | Priority |
|---|---|---|---|---|---|
| TC-001-RL-01 | throttle reset; customer token obtained; auth window empty | `RATELIMIT_AUTH` (10) wrong-credential POSTs to `/api/auth/token/`, then one more; then one refresh POST | Requests 1..10 are 401 (none 429). Request 11 is **429** `THROTTLED`, `Request rate limit exceeded.`, `Retry-After` > 0. Refresh is also 429 (same scope) | API | P1 |
| TC-001-RL-02 | — | Compare the configured rates | auth rate < user rate (stricter) | API | P3 |
| TC-001-RL-03 | customer token | `RATELIMIT_USER` (300) `GET /me`, then one more | 1..300 are 200. 301 is 429 envelope | API | P1 |
| TC-001-RL-04 | health token | `RATELIMIT_HEALTH` (120) `GET /api/status/`, then one more, then `/api/health/` with a valid token | 1..120 are 200. 121 is 429. `/api/health/` is 429 too (shared scope) | API | P1 |
| TC-001-RL-05 | **anon-scoped public endpoint (strategy §12.2)** | `RATELIMIT_ANON` (60) requests, then one more | 429 envelope. **Skipped with reason until the TL names an endpoint** | API | P1 |
| TC-001-RL-06 | — | Cross-worker consistency | Implied by RL-01/03/04: the 429 arrives at exactly limit+1 through 2 gunicorn workers (FileBasedCache). A later 429 (≈2× the limit) = bug (ADR-017) | API | P1 |

### 2.9 Transport / CORS — `qa/api/test_cors_security.py`
| ID | Preconditions | Steps | Expected | Level | Priority |
|---|---|---|---|---|---|
| TC-001-SEC-01 | — | CORS preflight `OPTIONS /api/auth/token/` from `https://delivery.hossam-ameen.online` | 200/204. `Access-Control-Allow-Origin` equals the web origin | API | P1 |
| TC-001-SEC-02 | — | Preflight from `https://evil.example`, the dental origin and a lookalike | No ACAO for that origin and no `*` | API | P1 |
| TC-001-SEC-03 | — | `GET /api/status/` headers | `X-Content-Type-Options: nosniff`. HSTS present | API | P2 |

### 2.10 Manual / audit cases (TASK-009)
| ID | Preconditions | Steps | Expected | Level | Priority |
|---|---|---|---|---|---|
| TC-001-MAN-01 | deployed | On the server: `/srv/flash/current/venv/bin/python --version`; `systemctl show flash-backend -p ExecStart --value`; read `deploy/README.md`'s start command | Python 3.13.x. gunicorn started by the unit. One documented command (AC1) | MAN | P1 |
| TC-001-MAN-02 | repo | Compare every `env(...)` read in `backend/config/settings/*` with `backend/.env.example` (read-only review) | Every variable is documented. No hardcoded secret default in production settings (`HEALTH_CHECK_PASSWORD` and `SECRET_KEY` have no production default) | MAN | P1 |
| TC-001-MAN-03 | repo | `git ls-files` shows no `.env`; grep the repo for secret-looking values (`SECRET_KEY=`, `PASSWORD=` with values, private keys) | None found (AC2, FEAT-004 AC11) | MAN | P1 |
| TC-001-MAN-04 | deployed sha | `make test-backend-remote REF=<deployed sha>` | `ruff`, `check`, `makemigrations --check --dry-run` green. `pytest --cov` ≥ 80%. JUnit shows TASK-002/003/004 tests (envelope incl. 500, readiness 503, throttles) passing. Gaps listed | MAN | P1 |

## 3. Execution order (TASK-009)
1. `make qa-remote ARGS="-m smoke"`
2. `make qa-remote ARGS="api -m 'regression and not ratelimit'"`
3. The manual cases in §2.10, plus TC-001-JWT-16b (in parallel with the 30-minute wait).
4. `make throttle-reset && make qa-remote ARGS="-m ratelimit"; make throttle-reset`

## 4. Exit criteria
- All P1 cases PASS.
- No open Critical/High bug.
- Every skipped case is listed as a gap with its owner (strategy §12).
- The report `.ai/reports/qa/FEAT-001-qa-report.md` quotes the evidence.
