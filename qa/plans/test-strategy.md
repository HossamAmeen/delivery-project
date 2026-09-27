# Flash — QA Test Strategy

Owner: QA · Task: TASK-008 · Version: 1.0 (2026-09-27)
Sources: `.ai/agents/qa.md`, ADR-007, ADR-015–ADR-019, `api-contracts.md`, `backlog.md` (FEAT-001/003/004),
`business-logic.md`, `flash_business_logic/05_cross_app_flows/06_qa_contract.md`, REQ-009.

## 1. Principles

1. **Independent and black-box.** QA verifies the deployed system over HTTP and through a real browser. The harness never imports backend or frontend code (ADR-007). Developer tests are audited, not counted as QA evidence.
2. **Business rules, not screens.** Every case traces to an acceptance criterion, a contract row or a `06_qa_contract.md` scenario. When a rule is missing or conflicting, QA raises a blocker and does not invent the expected result.
3. **Expected results come from the contract.** When the implementation differs from `api-contracts.md`, `business-logic.md` or the ADRs, that is a bug (or a blocker when the rule itself is unclear). QA never weakens a test to match the implementation.
4. **Evidence or it did not happen.** A PASS needs output QA produced itself (§8).

## 2. Environment: the deployed server only

| Item | Value |
|---|---|
| Where suites execute | On the server, `/srv/flash/qa/suite/`, venv `/srv/flash/qa/venv` (uv, Python 3.13), via **`make qa-remote`** (ADR-018) |
| API under test | `QA_BASE_URL=https://api.delivery.hossam-ameen.online` (public HTTPS, through nginx) |
| PWA under test | `QA_WEB_URL=https://delivery.hossam-ameen.online` |
| Backend suite audit | `make test-backend-remote REF=<deployed sha>` (Infrastructure runner) |
| Local machine | **Never runs QA** (REQ-009, PO rule). Allowed locally: editing `qa/`, and `pytest --collect-only` in a scratch venv to check syntax |

The harness enforces this. It refuses to execute unless `${QA_DEPLOY_PATH:-/srv/flash}/qa` exists, and it rejects non-HTTPS or local `QA_BASE_URL`/`QA_WEB_URL`. `--collect-only` works anywhere because it runs no fixture.

There is one environment (production-like staging, ADR-015). QA therefore:
- uses only the seeded QA users (§4) and never touches other data
- does not run the rate-limit suite (§7) or the rollback exercise while a deploy is in progress
- announces the rollback window in the FEAT-004 report (TASK-015)
- never touches the co-hosted dental-clinic app except through read-only GETs and `systemctl is-active` (§9)

## 3. Test levels and locations

| Level | Location | Tool | Markers | Runs in |
|---|---|---|---|---|
| API black-box contract (envelope, auth, permissions, health, docs, CORS) | `qa/api/` | pytest + httpx | `regression`, `smoke`, `security` | TASK-009 and every release |
| Rate limits (429) | `qa/api/test_ratelimit.py` | pytest + httpx | `ratelimit` (+ `regression`, `security`) | its own session, last (§7) |
| Multi-actor integration flows (customer → store → system → driver) | `qa/api/flows/` | pytest + httpx | `regression` | from FEAT-008 onward (no flows exist in sprint-01) |
| Deployment smoke / runtime (TLS, redirects, HSTS, SPA serving, systemd, layout, retention, secrets hygiene, dental) | `qa/smoke/` | pytest + httpx + stdlib (`ssl`, `socket`, `subprocess` read-only) | `deploy`, `smoke`, `regression` | TASK-015, after every deploy |
| Frontend E2E | `qa/e2e/` | Playwright (pytest-playwright, Chromium headless, one worker, 360 px + 1280 px) | `e2e` (auto), `regression`, `smoke` | TASK-010 and every release |
| Developer unit/API tests | `backend/`, `frontend/` | owned by developers | — | audited by QA via the server runner and Completion Reports |
| Plans, traceability | `qa/plans/` | Markdown | — | — |
| Reports and bugs | `.ai/reports/qa/`, `.ai/reports/qa/bugs/` | Markdown | — | — |

Marker meanings are defined in `qa/pytest.ini` (`--strict-markers`). The `e2e` marker is added automatically to everything under `qa/e2e/`.

## 4. Test data strategy

- **QA users:** `make seed-qa-users` (Infrastructure, TASK-013) runs TASK-003's `create_role_user` on the server and creates or updates `qa_customer`, `qa_driver`, `qa_store` and `qa_admin` (staff + superuser). It generates random passwords on the server into `/srv/flash/qa/credentials.env` (0600) as `QA_<ROLE>_USERNAME` / `QA_<ROLE>_PASSWORD`. `make qa-remote` loads them into the pytest process only.
- **Credentials come from the environment only.** Nothing has a default, and nothing is committed. A missing variable fails the test with a message that names the make target to run.
- **One login per role per session.** A session cache (`tokens` fixture) keeps the auth throttle budget small.
- **Read-only against shared state in sprint-01.** Foundation tests create no domain data. From FEAT-002 onward, tests that create data use a `qa_`-prefixed namespace and clean up through the API where the contract allows it. Otherwise QA asks the TL for a seed/cleanup command (ADR-007: a `seed_demo` command reviewed by QA).
- **Missing data needed by a planned case** is requested, not faked:
  - an inactive QA user for TC-001-JWT-07 (§12)
  - an anon-scope endpoint for TC-001-RL-05 (§12)
  Until then the case is **skipped with a stated reason** and listed as a coverage gap in the report. It is never counted as a pass.

## 5. Regression policy

- Every automated test is tagged `regression` unless it is exploratory or one-off. The regression baseline grows with each feature.
- **When it runs:**
  - on every release deployed to the server, and before any feature is signed off
  - after every bug fix (the re-test plus the full regression)
  - after infrastructure changes (nginx, systemd, TLS)
- **Standard run order (one release):**
  1. `make qa-remote ARGS="-m 'smoke or deploy'"`: fast gate. Stop and file bugs if it fails.
  2. `make qa-remote ARGS="-m 'regression and not e2e'"`: the API + smoke baseline.
  3. `make qa-remote ARGS="-m e2e"`: browser tests.
  4. `make throttle-reset && make qa-remote ARGS="-m ratelimit"; make throttle-reset`: last (§7).
  5. `make test-backend-remote REF=<deployed sha>`: developer suite audit.
- A regression failure on a previously passing case is at least **High** until triaged (§6).
- Flaky tests are not retried silently. There is no rerun plugin. A flake is investigated and either fixed in the harness (with the change recorded in the report) or filed as a bug.

## 6. Severity rules (bug reports)

| Severity | Meaning in Flash | Examples |
|---|---|---|
| **Critical** | Security or data exposure, data loss, the site down, the dental app affected, or a money-rule violation (later sprints) | a secret in a response, log or bundle; auth bypass; a non-staff user reaches the admin or OpenAPI; a dental site changes status after a Flash deploy; rollback loses the DB; the backend bound to a public interface |
| **High** | An acceptance criterion fails with no workaround, a contract is broken for clients, or a regression | wrong envelope or `errors.code`; the 429 missing or not enveloped; the refresh flow broken; deep links 404; the health check not green; a certificate invalid or near expiry |
| **Medium** | A criterion partly met, or a workaround exists | HSTS present but with the wrong max-age; a missing cache header; an OpenAPI operation without a 429; a validation message not in the envelope on one path |
| **Low** | Cosmetic, docs, or non-blocking hygiene | wording, a `deploy/README.md` gap, a 1-px overflow |

Open Critical/High bugs block the feature (Definition of Done). Deployment defects use Suggested Area `Infrastructure` (QA never edits `deploy/`, `.github/` or the Makefile).

## 7. Rate-limit test policy

- Limits are the configured server values, read from `QA_RATELIMIT_{ANON,USER,AUTH,HEALTH}`. The defaults are the documented ones: `60/minute`, `300/minute`, `10/minute`, `120/minute`.
- Each test sends exactly `limit` requests, which must not be throttled, then one more, which must return **429 in the envelope** with `errors.code = THROTTLED`, the message `Request rate limit exceeded.` and a positive integer `Retry-After`.
- Hitting 429 at exactly `limit + 1`, through nginx and two gunicorn workers, also proves the counters are shared across workers (FileBasedCache, ADR-017).
- **Isolation:**
  - `conftest.py` deselects `ratelimit` tests unless `-m` names `ratelimit`, and puts them last when selected
  - they run in their own session, with `make throttle-reset` before and after
  - no deploy may run during that session, because the deploy's health check shares the `health` scope from the same IP
- **Functional tests stay under the auth limit.** Every call to `/api/auth/*` (API or browser) first goes through `AuthPacer`, a sliding-window mirror of DRF's throttle that waits when the budget is nearly used. It never retries or hides a 429: an unexpected 429 in a functional test is still a failure.
- Bursts are capped at 1000 requests so a misconfigured limit cannot hammer the shared server.

## 8. Evidence rules

- `make qa-remote` copies `qa/.results/` back to the local machine (`qa/.results/latest/`):
  - `junit.xml`
  - `pytest.log`: one line per request with method, host, path and status. The query string is never logged.
  - `dental-<UTC>.json`
  - `resources.txt`
  - Playwright failure screenshots in `playwright/`
- Every QA report quotes the exact command, the pass/fail/skip summary line and the relevant JUnit/log excerpts. Each case in the report links to its test ID (TC-…) and its test node ID.
- Manual and exploratory steps are recorded as the command plus its output (redacted), for example `curl -sI …`, `systemctl is-active …`, `sha256sum …`.
- Skipped tests are listed with their reason and are never reported as PASS.
- The report records the deployed commit (`REVISION`), the date and time (UTC) and the harness version (the qa/ tree used).

### Secret hygiene (non-negotiable)
- `QA_HEALTH_TOKEN`, QA passwords and every JWT obtained are registered as secrets (`harness/secrets.py`). They are wrapped in `Secret`, whose `repr`/`str` never shows the value.
- Every test report (failure text, captured sections) is scrubbed by a `conftest.py` hook. Assertion helpers build redacted messages.
- At the end of each session the harness scans `.results/` for registered secrets and **fails the session** if any is found (counts only, never the value).
- httpx/httpcore loggers are held at WARNING. Playwright tracing and video are off, because traces record typed passwords.
- The health token is sent only in the `X-Health-Check-Token` header. `?password=` is sent **once, with a wrong value**, to prove it is rejected. A valid `?password=` is never sent, because tooling must not put the token in a URL (ADR-015), and the header variant already proves the valid path.

## 9. Dental-clinic non-interference checks (FEAT-004 AC9)

QA touches dental **read-only** and only through:
- HTTPS GETs of `https://dental.hossam-ameen.online/` and `https://api.dental.hossam-ameen.online/`
- `systemctl is-active dental-clinic-backend`
- `sha256sum` of non-Flash nginx files, a manual step with read-only sudo per TASK-015

| When | What |
|---|---|
| Baseline, before anything in TASK-015 | `make qa-remote ARGS="-m deploy -k dental"` records the status codes in `.results/dental-<UTC>.json`. The manual step records `systemctl is-active` and the nginx hashes. |
| After the rollback exercise, and at the end | Re-run with `--dental-expect="<url>=<code>,<url>=<code>"` using the baseline codes. The test fails on any difference. The hashes and service state are compared by hand. |
| Every Flash smoke run | `test_dental_sites_reachable` (no 5xx or connection error) and `test_dental_service_still_active` |

Any difference is a **Critical** bug with Suggested Area `Infrastructure`.

## 10. Cross-client consistency approach (the 15 QA-contract scenarios)

`06_qa_contract.md` requires the same scenario to give the same business result through the API, the Vue PWA, Flutter (after the MVP, BLK-002) and the Admin interface.

**Approach:**
1. **The API is the oracle.** Each scenario is first automated in `qa/api/flows/` against the contract. The backend is authoritative for state, prices, fees and permissions (business-logic §13).
2. **Clients are checked for equivalence, not re-implementation.** For each scenario, the E2E test in `qa/e2e/` drives the same scenario through the PWA role area. It then reads back the result **through the API** (status, amounts, `allowed_transitions`, history) and asserts it equals the API-only run: same final state, same amounts as strings, same error `code`.
3. **Admin interface.** The Admin role area of the PWA (ADR-011) and Jazzmin views are checked read-only against the same API resource (Jazzmin only for staff operations it actually exposes).
4. **Flutter.** Out of scope until FEAT-017. The same API oracle will be reused.
5. A shared scenario table (below) is kept in each feature plan. A client that shows a different result than the API is a High bug against that client.

| # | Scenario (06_qa_contract) | First feature | API | PWA | Admin |
|---|---|---|---|---|---|
| 1 | customer creates valid order | FEAT-008 | ✔ | ✔ customer area | read |
| 2 | invalid order rejected | FEAT-008 | ✔ | ✔ | — |
| 3 | price snapshot preserved | FEAT-008 | ✔ | ✔ display | read |
| 4 | store processes valid states | FEAT-008 | ✔ | ✔ store area | read |
| 5 | invalid state transition rejected (409 `INVALID_TRANSITION`) | FEAT-008 | ✔ | ✔ | — |
| 6 | system assigns driver | FEAT-009 | ✔ | ✔ driver area | read |
| 7 | driver has no Accept/Reject | FEAT-009 | ✔ (no endpoint) | ✔ (no control) | — |
| 8 | assigned order appears to driver | FEAT-009 | ✔ | ✔ | — |
| 9 | driver sees customer collection amount | FEAT-011 | ✔ | ✔ | read |
| 10 | driver sees store-related fee/amount | FEAT-011 | ✔ | ✔ | read |
| 11 | duplicate delivery completion prevented | FEAT-010 | ✔ (retry, `Idempotency-Key`) | ✔ (double tap) | — |
| 12 | duplicate financial transaction prevented | FEAT-011 | ✔ | — | read ledger |
| 13 | cancellation follows state rules | FEAT-012 (BLK-005) | ✔ | ✔ | ✔ |
| 14 | notifications correspond to business events | FEAT-013 (BLK-010) | ✔ | ✔ in-app | — |
| 15 | permissions prevent unauthorized actions | **FEAT-001** (foundation) onward | ✔ | ✔ guards | ✔ staff-only |

In sprint-01 only scenario 15 applies:
- API: 401/403 per role, docs staff-only, admin staff-only, role read-only
- PWA: the route guard sends each role to its own area; logout guards the areas

Scenarios 1–14 have no API yet. They are planned when their features are designed. Where a rule is UNDEFINED (for example BLK-003/004/005/006/010), QA writes the case as **blocked** and does not invent an expected value.

**Concurrency** (business-logic §11, §16) is verified from FEAT-008/009. It uses parallel httpx requests from the server (threads, bounded), for example two transitions or two completions on one order. Exactly one must win and the other must get a clean 409. SQLite is a known limitation (ADR-017): `select_for_update` is a no-op, so these tests are expected to expose races until the PostgreSQL ADR.

## 11. Permissions matrix policy

`qa.md` §6: every role in `02_roles_and_permissions.md` gets a positive and a negative check for every endpoint. For sprint-01:

| Endpoint | Anonymous | CUSTOMER | DRIVER | STORE | ADMIN (staff) |
|---|---|---|---|---|---|
| `GET /api/status/` | 200 | 200 | 200 | 200 | 200 |
| `GET /api/health/`, `/ready/` | 401 without token, 200 with header token | (token-based, role-independent) | | | |
| `POST /api/auth/token/`, `/refresh/` | 200/401 | 200 | 200 | 200 | 200 |
| `GET /api/users/me/` | 401 `NOT_AUTHENTICATED` | 200 role=CUSTOMER | 200 role=DRIVER | 200 role=STORE | 200 role=ADMIN, is_staff |
| `GET /api/schema/`, `/api/docs/`, `/api/redoc/` | 401 | 403 | 403 | 403 | 200 (bearer or session) |
| `/admin/` | 302 → login | login refused | login refused | login refused | 200 |
| PWA role areas | → `/login` | `/customer` only | `/driver` only | `/store` only | `/admin` only |

## 12. Open items (tracked in reports; raised to the TL/Infrastructure by the orchestrator)

**TL decisions (TASK-008 review, 2026-09-27):**
- item 1 accepted: `qa_inactive` is seeded through TASK-016/013/014
- item 2: the anon scope is proven by the backend suite on the server (FEAT-001 plan TC-001-MAN-05), and TC-001-RL-05 stays skip-with-reason
- item 5: the codes are `HEALTH_TOKEN_INVALID` and `SERVICE_NOT_READY`, and they are now asserted exactly

The items below are kept for history.

1. **No inactive QA user.** The contract requires an inactive user to get the same 401 as a wrong password. `make seed-qa-users` creates only active users. **Request:** add `qa_inactive` (active=False) and export `QA_INACTIVE_USERNAME/PASSWORD` into `credentials.env` (TASK-013 scope). Until then TC-001-JWT-07 is skipped, and it is an explicit gap in the FEAT-001 report.
2. **No endpoint exercises the `anon` throttle scope.**
   - `/api/status/` and `/api/health/` use `health`
   - `/api/auth/*` uses `auth`
   - anonymous calls to protected views fail authentication or permission before throttling (DRF order: authenticate → permissions → throttles)

   FEAT-001 AC5 requires anon limiting to be demonstrated. **Question to the TL:** which public endpoint carries the anon scope? Set `QA_ANON_THROTTLE_PATH` accordingly. Until then TC-001-RL-05 is skipped, and it is a gap.
3. **An expired, validly signed JWT** needs a 30-minute wait (the access lifetime). It is a manual step in TASK-009 (TC-001-JWT-16b). The automated test covers a forged `exp`.
4. **500 path.** A 500 cannot be triggered safely from outside. It is covered by the developer-suite audit (TASK-002's handler tests) and by the no-internals checks on the 4xx paths.
5. **Health 401 `errors.code`.** The Foundation contract gives the message (`Invalid health check password.`) but no code. §1.2 requires a code on every non-field error. The harness asserts that *a* code is present, not its value. **Question to the TL:** fix the value in `api-contracts.md` (e.g. `NOT_AUTHENTICATED`).
6. **Playwright selectors.** They follow TASK-007's acceptance-criteria wording (accessible names). They are confirmed against the built PWA at the start of TASK-010. Only selectors may be adjusted, never expected behaviour.
7. **`make qa-remote` details.** The contract assumed from ADR-018/TASK-012 is:
   - pytest runs from the `qa/` root
   - `ARGS` are passed through
   - `.results/` is copied back to `qa/.results/latest/`

   The on-server collection check (`make qa-remote ARGS='--collect-only -q'`) confirms this. A mismatch is an Infrastructure bug.
