# QA Report — FEAT-003 Frontend Foundation (Vue PWA)

QA task: TASK-010 · Task verified: TASK-007 · Plan: `qa/plans/FEAT-003-test-plan.md` · Date: 2026-09-28 (runs are timestamped in UTC on 2026-09-27)

## Verdict: **PASS**

All FEAT-003 acceptance criteria 1–6 have executed evidence on the deployed web domain, and every P1 case passed. No bug was found in the PWA. Two P2 manual checks were not executed; they are listed as gaps below and do not block.

## Scope and environment

| Item | Value |
|---|---|
| Target | `https://delivery.hossam-ameen.online` (nginx static `dist/`), API `https://api.delivery.hossam-ameen.online` |
| Release | `20260927-205803`, commit `f85848b`, `REVISION vite_api_base_url=https://api.delivery.hossam-ameen.online` |
| Runner | `make qa-remote ARGS="-m e2e"` on the server. Playwright 1.63 / pytest-playwright 0.9, Chromium headless from `/srv/flash/qa/browsers`, one worker, viewports 360×780 and 1280×800, no tracing/video |
| Users | the seeded `qa_*` users |

**Selectors confirmed against the built PWA** (`frontend/src/i18n/en.ts`, the views, and the `data-testid` hooks of the state components). Before the first run:
- the loading state is matched through `data-testid="state-loading"`, because its text is "Checking the API…"
- the login 429 text is "Too many sign-in attempts…"
- the role is shown as "Store", read from the `session-user` block

Two tests were added for behaviour in the contract refinement of 2026-09-27:
- TC-003-E2E-19: a refresh that is not answered keeps the session
- TC-003-E2E-20: the empty-state component is used

**Interception disclosure:** TC-003-E2E-12..17 and -19 use Playwright `page.route` with contract-shaped envelopes, with the service worker blocked. Expired tokens, a 429 or a network failure cannot be triggered live on demand without locking out the suite. All other E2E cases run against the real server.

## Commands and evidence

| # | Command | Run ID (`qa/.results/<id>/`) | Result |
|---|---|---|---|
| 1 | `make qa-remote ARGS="-m e2e"` | 20260927-224953-99845 | 27 passed, 3 failed. All 3 were **harness**: `Too many sign-in attempts…` (HTTP 429 on the auth scope). The previous API session's logins were still in the server's 60 s window, and the pacer did not know about them |
| 2 | Fix: `AuthPacer` persists its window on the server (`/srv/flash/qa/.auth-pacer.json`); re-run `-m e2e` | 20260927-225129-104522 | 29 passed, 1 failed (`logged_in_shows_username_and_role`: "Could not load your account." — the page-load refresh was throttled; the state file was still empty on that first run after the fix) |
| 3 | `make qa-remote ARGS="e2e/test_status_page.py -k logged_in"` (with browser API-call evidence added to the test) | 20260927-225301-107392 | 1 passed |
| 4 | `make qa-remote ARGS="-m e2e"` (**final**) | 20260927-225312-107600 | **30 passed**, 0 failed, 0 skipped |
| 5 | HTTP serving checks in `make qa-remote ARGS="-m 'regression and not e2e'"` | 20260927-225552-109762 | `smoke/test_web_serving.py` all passed (TC-003-WEB-01..06); TLS/HSTS/redirect for the web domain passed |

The behaviour in run 2 is itself correct per the contract: a refresh answered with 429 keeps the session and shows the error state instead of logging out. The failure was the test's throttle budget, not the app.

## Results per acceptance criterion

| AC | Result | Evidence |
|---|---|---|
| AC1: builds, installs, runs at mobile/desktop widths | **PASS** | TC-003-WEB-03: the manifest is valid (Flash, `start_url /`, `standalone`, icons 192/512/maskable, each 200 `image/*`, `no-cache`). WEB-04: `sw.js` is JavaScript with `no-cache`. E2E-01 ×2: the service worker becomes active at 360 and 1280. E2E-02: the icons load in the browser. E2E-18 ×6: no horizontal overflow on `/login`, `/status` and an unknown route at both widths; labelled inputs |
| AC2: one API client: envelope, 401 refresh once then logout, 403/404/429 | **PASS** | E2E-14: 401 `TOKEN_INVALID` → exactly **1** refresh → retry with the new bearer → lands on `/customer`. E2E-15: refresh 401 → exactly 1 attempt, `/login`, refresh token removed from localStorage. E2E-19: refresh 503 → session **kept** (token still stored). E2E-16: login 429 → rate-limit message. E2E-17: status 429 → "Rate-limited". E2E-04: `INVALID_CREDENTIALS` message from the live API. 403/404 mapping: see gaps (covered by TASK-007 unit tests) |
| AC3: loading, empty, error, unavailable components | **PASS** | E2E-12: loading (`state-loading`) → error (`state-error`, "API unreachable") → Try again → reachable. E2E-13: 500 → error state + retry. E2E-17: unavailable state (429). E2E-20: empty state (anonymous session card) |
| AC4: role-area routing | **PASS** | E2E-03 ×4: each role lands in its own area. E2E-07: a customer sent to `/admin`, `/driver`, `/store` ends in `/customer`. E2E-06: logout → `/login`, and `/driver` is guarded afterwards |
| AC5: lint, type-check, unit tests, build | **PASS (evidence review)** | TASK-007 Completion Report, local build gates per ADR-018: `npm run lint` EXIT 0; `type-check` EXIT 0; `test:unit` 9 files / 67 tests passed (3 consecutive runs); production build with `VITE_API_BASE_URL` succeeded. The TL code review approved it. QA did not run them locally (REQ-009) and saw no reason to request a re-run |
| AC6: HTTPS web domain; API URL from config; deep links | **PASS** | TC-003-WEB-02 ×7 and E2E-08/09: deep links and an unknown route return 200 from nginx and are handled by the SPA (redirect to `/login` / NotFound view). E2E-10 ×2: *API reachable* via `<API>/api/status/`, **no** `/api/health` request, the configured base URL is displayed. WEB-05: the JS bundle contains the API base URL, no health token, no `/api/health`, no localhost URL. `REVISION` shows `vite_api_base_url` from config. Valid TLS, HSTS without `includeSubDomains`, HTTP → 301. The CORS preflight from the web origin is allowed (TC-001-SEC-01) |
| Permissions (#15) | **PASS** | E2E-06, -07, -11 (status page shows the signed-in username + "Store" role) |

## Gaps (not executed, P2/P3)

| Case | Reason | Mitigation |
|---|---|---|
| TC-003-MAN-01 (reference screenshots at 360/1280) | Not captured in this session; screenshots are only taken on failure | E2E-18 layout checks passed at both widths |
| TC-003-MAN-02 (403/404 mapping in the UI) | No sprint-01 screen calls an endpoint that returns 403/404 | TASK-007 unit tests: `client.spec.ts` "403/404/500 codes" |
| TC-003-MAN-05 (no cookies; password not in the URL) | Verified by inspection instead of network capture: `frontend/src/api/client.ts:82` `credentials: 'omit'`; login is a JSON POST body | TASK-007 unit test "base URL + `credentials: 'omit'`" |

## Bugs

None against FEAT-003.

Harness finding (fixed in `qa/`, not a product bug): back-to-back QA sessions share the server's auth-throttle window. `AuthPacer` now persists its window, and `qa/README.md`'s run order stays valid.
