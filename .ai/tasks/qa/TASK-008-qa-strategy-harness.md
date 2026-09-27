# Task

## ID
TASK-008

## Title
QA test strategy, Sprint-1 test plan & black-box harness

## Feature
FEAT-001 — Backend Platform Foundation

## Description
Create the QA foundation: overall strategy, the sprint-01 test plans with traceability (FEAT-001, FEAT-003, FEAT-004), and the `qa/` pytest + httpx harness (plus Playwright scaffold) that runs **on the server** against the deployed instance through `make qa-remote` (ADR-007, ADR-018, REQ-009).

## Business Requirement
REQ-002, REQ-006, REQ-008, REQ-009; `05_cross_app_flows/06_qa_contract.md`; FEAT-001 criteria 1–10; FEAT-003 criteria 1–6; FEAT-004 criteria 1–13; ADR-018

## Agent
QA

## Scope (allowed paths)
- `qa/**`

## Dependencies
- none to start (plan from contracts and ADRs) — runs **in parallel** from day 1
- TASK-012 (`make qa-remote`) for the on-server collection check

## Acceptance Criteria

- [ ] `qa/plans/test-strategy.md`: levels, locations, **environment = the deployed server only** (ADR-018; no local runs), data strategy (QA users from `make seed-qa-users`), regression policy, severity rules, evidence rules (JUnit + logs from `qa/.results/` quoted in reports), rate-limit test policy (run last, `make throttle-reset` before/after), dental non-interference checks, cross-client consistency approach for the 15 QA-contract scenarios.
- [ ] `qa/plans/FEAT-001-test-plan.md`, `qa/plans/FEAT-003-test-plan.md`, `qa/plans/FEAT-004-test-plan.md`: test cases traced to each criterion (ID, preconditions, steps, expected, level, priority).
- [ ] Harness: `qa/requirements.txt` (pinned: pytest, httpx, pytest-playwright or playwright), `qa/pytest.ini`, `conftest.py` with `QA_BASE_URL`, `QA_WEB_URL`, `QA_HEALTH_TOKEN`, and QA user credentials (`QA_CUSTOMER_USERNAME/PASSWORD`, … for DRIVER, STORE, ADMIN) from env only; envelope assertion helpers; a redaction helper so tokens/passwords never appear in assertion messages or logs; markers `smoke`, `regression`, `security`, `ratelimit`, `deploy`, `e2e`.
- [ ] `qa/api/` smoke tests for `/api/status/`, `/api/health/`, `/api/health/ready/`; `qa/smoke/` deployment checks (HTTPS, redirect, cert, SPA deep link, dental sites reachable); `qa/e2e/` Playwright config (Chromium, 360 px + 1280 px viewports, `--workers=1`).
- [ ] `qa/README.md`: how to run on the server (`make seed-qa-users`, `make qa-remote ARGS=…`, `make throttle-reset`), what each variable means, and that QA is never run locally.
- [ ] `make qa-remote ARGS="--collect-only -q"` succeeds on the server (proves the harness installs and imports on Python 3.13). Live execution happens in TASK-009/010/015.

## Technical Notes

- Never import backend code; HTTP only.
- Rate-limit tests use the configured server limits (e.g. `RATELIMIT_AUTH=10/minute`): send limit+1 requests, assert 429 envelope + `Retry-After`; run them last.
- Never print `QA_HEALTH_TOKEN` or passwords; never use `?password=` for health (it is supported by the API but banned for tooling, ADR-015) — test the query variant once, with a **wrong** value, to prove it is rejected, and the valid variant only if the plan justifies it.
- Never edit `deploy/` or the Makefile; missing tooling is a bug for Infrastructure.

## Testing Requirements

- The collection check above. The live health smoke test is executed in TASK-015 after the first deployment.

## Plan Review Required
No

## Status

READY_FOR_QA

## Activity Log
- 2026-09-27 | team-lead | — → TODO | created from sprint-01 technical plan
- 2026-09-27 | team-lead | TODO → TODO | re-scoped for REQ-009/ADR-018: harness runs on the server via `make qa-remote`; plans for FEAT-001/003/004; no local runs
- 2026-09-27 | qa | TODO → IN_PROGRESS | started strategy, plans and harness from contracts/ADRs
- 2026-09-27 | qa | IN_PROGRESS → READY_FOR_REVIEW | strategy, 3 plans, harness (139 tests: 67 api + 5 ratelimit, 39 smoke/deploy, 28 e2e) delivered; on-server `--collect-only` by QA was denied by the session's permission policy — see Completion Report (open item 1)
- 2026-09-27 | team-lead | READY_FOR_REVIEW → REVIEW | inspection done, QA's three questions decided; verdict pending the on-server `make qa-remote ARGS='--collect-only -q'` (waiting for the user's permission decision)
- 2026-09-27 | team-lead | REVIEW → READY_FOR_QA | code review APPROVED; AC6 on-server collection by the TL: 134/139 collected (5 deselected), exit 0 (run 20260927-204352-12423)

## Implementation Plan
(not required)

## Completion Report
- **Files changed (all new, `qa/` only):**
  - Docs: `qa/README.md`, `qa/plans/test-strategy.md`, `qa/plans/FEAT-001-test-plan.md`, `qa/plans/FEAT-003-test-plan.md`, `qa/plans/FEAT-004-test-plan.md`.
  - Harness config: `qa/requirements.txt` (pytest 9.1.1, httpx 0.28.1, playwright 1.63.0, pytest-playwright 0.9.0), `qa/pytest.ini`, `qa/.gitignore`, `qa/conftest.py`.
  - Harness library: `qa/harness/{__init__,config,secrets,envelope,http,pwa}.py`.
  - API tests: `qa/api/test_{status,health,envelope,auth_jwt,users_me,openapi_docs,admin,cors_security,ratelimit}.py`.
  - Smoke/deploy tests: `qa/smoke/test_{tls_https,web_serving,dental_non_interference,server_runtime}.py`.
  - E2E: `qa/e2e/conftest.py`, `qa/e2e/test_{pwa_install,login_routing,status_page,api_client_behaviour,responsive}.py`.
- **Harness features (AC3):**
  - Configuration comes from the environment only: `QA_BASE_URL`, `QA_WEB_URL`, `QA_HEALTH_TOKEN`, `QA_<ROLE>_USERNAME/PASSWORD`, thresholds.
  - A server-only guard refuses to run unless `/srv/flash/qa` exists, and rejects non-HTTPS or local URLs.
  - Envelope assertion helpers.
  - Secret handling:
    - a `Secret` wrapper and `redact()`
    - every test report is scrubbed
    - the session fails if a secret reaches `.results/`
    - httpx loggers are held at WARNING
    - Playwright tracing and video are off
  - Markers: `smoke`, `regression`, `security`, `ratelimit`, `deploy`, `e2e` (`--strict-markers`). `e2e` is added automatically under `qa/e2e/`.
  - `ratelimit` tests are deselected unless `-m` names them, and run last when selected.
  - `AuthPacer` keeps functional runs under `RATELIMIT_AUTH`. It never retries a 429.
  - Playwright: Chromium headless, one worker (no xdist), 360 px and 1280 px viewports, a screenshot on failure only.
- **Tests added:** 139 collected, traced to test-case IDs in the plans.
  - `qa/api/`: 72, including the 5 `ratelimit` tests.
  - `qa/smoke/`: 39.
  - `qa/e2e/`: 28.
  - By marker: smoke 53, deploy 39, security 78, e2e 28, regression 134 (+ 5 ratelimit).
- **Validation commands run + results:**
  - `pytest --collect-only -q` in a scratch venv (Python 3.12, scratchpad copy of `qa/`): `134/139 tests collected (5 deselected)`. The 5 deselected are exactly `api/test_ratelimit.py::{test_auth_scope_is_throttled, test_auth_scope_is_stricter_than_user_scope, test_user_scope_is_throttled, test_health_scope_is_throttled, test_anon_scope_is_throttled}`. `-m ratelimit` collects those 5. Per directory: api 67/72, smoke 39, e2e 28. `pyflakes .` is clean.
  - **Infrastructure's earlier on-server run (106/111 collected, 5 deselected):** 111 = 139 − the 28 e2e tests. That run used a snapshot taken before `qa/e2e/` was written. Its 5 deselected tests are the same ratelimit tests, deselected on purpose (strategy §7).
  - **Guard self-check** (unroutable `*.qa.invalid` URLs, so no real server could be contacted): with `QA_DEPLOY_PATH=/nonexistent` the run exits with "the QA suite runs on the server only (REQ-009, ADR-018)". With `QA_BASE_URL=http://localhost:8000` it exits with "must be the deployed public HTTPS URL". No test executed in either case.
  - **Redaction check:** `Secret` repr is `Secret([REDACTED])`. Registered values, `?password=` values and bearer JWTs are all redacted.
  - **NOT done by QA:** `make qa-remote ARGS='--collect-only -q'` on the server. The session's permission policy denied the command (it was classified as a remote shell write). This AC stays open until someone with permission runs it: the TL, Infrastructure, or QA once permission is granted. Expected result: `134/139 tests collected (5 deselected)`, exit 0, under Python 3.13 in `/srv/flash/qa/venv`.
- **Contract/OpenAPI changes:** none (QA does not edit contracts). Questions for the TL are in strategy §12.
- **Known limitations / remaining problems** (strategy §12):
  1. The on-server collection check still needs to be run (see above).
  2. No inactive QA user. TC-001-JWT-07 is skipped with a reason. Request to Infrastructure/TL: `make seed-qa-users` should also create `qa_inactive` (inactive) and export `QA_INACTIVE_USERNAME/PASSWORD`.
  3. No endpoint exercises the `anon` throttle scope (DRF runs authentication and permissions before throttling). TC-001-RL-05 is skipped. The TL must name a public anon-scoped endpoint (`QA_ANON_THROTTLE_PATH`), or FEAT-001 AC5's "anonymous" part cannot be demonstrated.
  4. The health 401 `errors.code` value is not in `api-contracts.md`. QA asserts only that a code is present. The TL should fix the value.
  5. An expired, validly signed JWT (30-minute wait) and the 500 path are manual/audit cases (TC-001-JWT-16b, TC-001-MAN-04).
  6. E2E selectors follow TASK-007's wording and are confirmed against the built PWA at the start of TASK-010.
  7. Live execution (health smoke self-test etc.) happens after deployment in TASK-009/010/015.

## Review Log

### Review — 2026-09-27 — team-lead — code (in progress)

**Verdict:** PENDING — not issued yet. The only open item is AC6, the on-server collection check `make qa-remote ARGS='--collect-only -q'` (expected `134/139 collected, 5 deselected`, exit 0, Python 3.13). QA's attempt was denied by the session's permission policy and the orchestrator is waiting for the user's decision; the TL did **not** run it either (as instructed). When it has been run with permission and its output is added to the Completion Report, the TL issues the verdict. Nothing found in the inspection blocks approval.

**Checked (inspection):**
- [x] Scope `qa/**` only; no backend imports (HTTP only, ADR-007); `deploy/`/Makefile untouched
- [x] Business rules: none invented; test cases trace to FEAT-001/003/004 criteria and the contracts
- [x] Secrets: token/passwords from env only, `Secret` wrapper + scrubbing, tracing/video off, health token only in the header; `?password=` sent only with a wrong value
- [x] Server-only guard (`/srv/flash/qa` + HTTPS URLs); markers; `ratelimit` deselected unless selected and run last
- [x] Requirements pinned (pytest 9.1.1, httpx 0.28.1, playwright 1.63.0, pytest-playwright 0.9.0)
- [ ] AC6 on-server collection — pending (see above)

**Decisions on QA's questions (strategy §12):**
1. **Inactive QA user — ACCEPTED.** `make seed-qa-users` will also create `qa_inactive` (role CUSTOMER, inactive) and export `QA_INACTIVE_USERNAME` / `QA_INACTIVE_PASSWORD` to `/srv/flash/qa/credentials.env`. Needs Backend **TASK-016** (`create_role_user --inactive`, new) and is written into TASK-013 (`seed-qa-users.sh` AC) and TASK-014 (execution). TC-001-JWT-07 stays skip-with-reason until then.
2. **`anon` throttle scope — no public anon-scoped endpoint is added; FEAT-001 AC5's "anonymous" part is covered another way.** DRF runs authentication and permissions before throttles, and every sprint-01 public endpoint has its own scope (`/api/status/` and health → `health`, login/refresh → `auth`; ADR-019 keeps `/api/status/` on `health`). Coverage: (a) live on the server, QA proves throttling + the 429 envelope + `Retry-After` on the `auth` and `health` scopes and the `user` scope; (b) the `anon` scope binding is proven by the backend suite run on the server (`test_anonymous_user_uses_anonymous_throttle`, `test_api_rejects_requests_after_rate_limit`), which QA cites from the JUnit of the TL's `make test-backend-remote` run in TASK-009. Keep TC-001-RL-05 as skip-with-reason (`QA_ANON_THROTTLE_PATH` unset) and trace AC5-anon to that evidence in the FEAT-001 plan. The first feature that adds a public anonymous endpoint gets a live anon test. Recorded in api-contracts § Foundation notes.
3. **Health 401 code — `HEALTH_TOKEN_INVALID`** (and 503 readiness → `SERVICE_NOT_READY` with `errors.checks`), now in api-contracts.md § Foundation and § Error codes. QA should assert the exact code.

**Findings:**
1. [non-blocking] `qa/api/test_health.py` asserts only that a code is present — tighten to `HEALTH_TOKEN_INVALID` (and `SERVICE_NOT_READY` where readiness fails) now that the contract fixes them. May be done in TASK-008 before the collection run or at the start of TASK-009.
2. [non-blocking] Update `qa/plans/FEAT-001-test-plan.md` / strategy §12 with decisions 1–3 (TASK-016 dependency for TC-001-JWT-07; AC5-anon traced to the backend suite evidence).
3. [non-blocking] The local `pytest --collect-only` in a scratch venv imports but executes no test, so it stays within REQ-009; it is not a substitute for AC6.

**Commands run:** none on the server (by instruction). Local read-only inspection of `qa/` (file layout, `requirements.txt`, `pytest.ini`, greps for backend imports, `password=` usage, `QA_INACTIVE_*`, `QA_ANON_THROTTLE_PATH`).

### Review — 2026-09-27 — team-lead — code (final)

**Verdict:** APPROVED

AC6 is now met (run by the TL, with the user's permission): the harness installs and imports on the server's Python 3.13 QA venv and collects exactly as expected. The inspection, decisions and non-blocking findings of the in-progress review above stand. Findings 1–2 (assert `HEALTH_TOKEN_INVALID`/`SERVICE_NOT_READY`; update the FEAT-001 plan for `qa_inactive` via TASK-016 and AC5-anon evidence) are to be done at the start of TASK-009.

**Commands run:** `make qa-remote ARGS='--collect-only -q'` → run `20260927-204352-12423` (ref: working tree at `0a5f845`), results in `qa/.results/20260927-204352-12423/`:
```
134/139 tests collected (5 deselected) in 0.09s     (the 5 deselected = api/test_ratelimit.py, by design)
== exit code: 0        make EXIT 0
```
Only collection ran; no test was executed and no request reached the Flash or dental sites.

## QA Log

## Sign-off
- TL final review: ☐
- QA verdict: ☐
- PM acceptance: ☐
