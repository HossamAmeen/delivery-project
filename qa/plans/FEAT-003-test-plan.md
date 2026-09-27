# FEAT-003 — Frontend Foundation (Vue PWA) — Test Plan

Owner: QA · Planned in: TASK-008 · Executed in: TASK-010 · Strategy: `qa/plans/test-strategy.md`
Sources: backlog FEAT-003 AC1–AC6; TASK-007 acceptance criteria; `api-contracts.md` § Foundation, § Identity (client rules); ADR-008, ADR-011, ADR-015 (web nginx/cache headers), ADR-019.

**Environment:** the deployed web domain `https://delivery.hossam-ameen.online` and the API `https://api.delivery.hossam-ameen.online`, on the server via `make qa-remote` (REQ-009).

**Browser:**
- Playwright Chromium, headless
- one worker: serial, no xdist
- viewports 360×780 and 1280×800
- no tracing and no video (traces record passwords); a screenshot on failure only

**Roles:** anonymous, `qa_customer`, `qa_driver`, `qa_store`, `qa_admin` (seeded).

**Data setup:**
1. The PWA is deployed (TASK-014).
2. `make seed-qa-users` has been run.
3. Chromium and its dependencies are installed on the server (`setup-server.sh --with-e2e`). If they are missing, that is an Infrastructure bug.

**Interception:** refresh/expiry/429 client behaviour is verified with Playwright `page.route` and contract-shaped envelopes (a live trigger is impractical). The service worker is blocked in those tests so interception is reliable. The report states this.

**Selectors:** accessible names from TASK-007's wording (`harness/pwa.py`). They are confirmed against the built PWA at the start of TASK-010. Only selectors may change, never expected behaviour.

## 1. Traceability

| AC | Criterion (short) | Test cases |
|---|---|---|
| AC1 | Builds, installs and runs on mobile and desktop widths | TC-003-WEB-01, -03, -04; TC-003-E2E-01, -02, -18; TC-003-MAN-01 |
| AC2 | One API client: envelope, 401 (refresh once, then logout), 403, 404, 429 | TC-003-E2E-04, -14..17; TC-003-MAN-02 |
| AC3 | Loading, empty, error and unavailable state components | TC-003-E2E-12, -13; TC-003-MAN-03 |
| AC4 | Role-area routing skeleton | TC-003-E2E-03, -06, -07 |
| AC5 | Lint, type-check, unit tests and build pass | TC-003-MAN-04 (evidence review) |
| AC6 | HTTPS at the web domain; API base from config; deep links load the app | TC-003-WEB-02, -05; TC-003-E2E-08, -09, -10; TC-001-SEC-01 (CORS); TC-004-TLS-* |
| 06_qa_contract #15 | Permissions: role guard, logout | TC-003-E2E-06, -07, -11 |

## 2. Test cases

Level: **HTTP** = `qa/smoke/test_web_serving.py` (httpx, no browser); **E2E** = `qa/e2e/` Playwright; **MAN** = manual/exploratory or evidence review.
Priority: P1 gate, P2 important, P3 hygiene.

### 2.1 Serving (HTTP level) — `qa/smoke/test_web_serving.py`
| ID | Preconditions | Steps | Expected | Level | Priority |
|---|---|---|---|---|---|
| TC-003-WEB-01 | deployed | `GET /` | 200 `text/html` containing `id="app"` | HTTP | P1 |
| TC-003-WEB-02 ×7 | — | `GET /driver`, `/customer`, `/store`, `/admin`, `/login`, `/status`, `/qa/unknown/deep/link` | 200 index.html (SPA fallback), not an nginx 404 | HTTP | P1 |
| TC-003-WEB-03 | — | `GET /manifest.webmanifest`, then each icon | 200 valid JSON. name/short_name `Flash`, `start_url /`, `display standalone`. Icons 192 and 512 plus a maskable one, each 200 `image/*`. `Cache-Control: no-cache` | HTTP | P1 |
| TC-003-WEB-04 | — | `GET /sw.js` | 200 JavaScript, `no-cache` | HTTP | P1 |
| TC-003-WEB-05 | health token | Fetch index.html's JS and its lazily imported chunks | No health token. No `/api/health` string. Contains `https://api.delivery.hossam-ameen.online`. No localhost URL | HTTP | P1 |
| TC-003-WEB-06 | — | `GET /.env`, `/.git/config`, `/package.json` | Not served as files (SPA shell or 404) | HTTP | P2 |

### 2.2 Browser — `qa/e2e/`
| ID | Preconditions | Steps | Expected | Level | Priority |
|---|---|---|---|---|---|
| TC-003-E2E-01 ×2 | — | Open `/` at 360 and 1280 | `#app` rendered. Exactly one manifest link. `navigator.serviceWorker.ready` gives an active worker within 15 s | E2E | P1 |
| TC-003-E2E-02 | — | Fetch the manifest and its icons in the browser | All icons load with an image content type | E2E | P2 |
| TC-003-E2E-03 ×4 | seeded users | `/login`: username + password → submit, as each role | Lands on `/customer`, `/driver`, `/store`, `/admin` respectively | E2E | P1 |
| TC-003-E2E-04 | — | Log in with a wrong password | `Invalid username or password.` shown. Stays on `/login` | E2E | P1 |
| TC-003-E2E-05 | — | Inspect the password input | `type="password"` | E2E | P2 |
| TC-003-E2E-06 | driver | Log in (360 px) → Logout → open `/driver` | After logout the app is on `/login`, and `/driver` redirects to `/login` | E2E | P1 |
| TC-003-E2E-07 | customer | Logged in, open `/admin`, `/driver`, `/store` | Each redirects to `/customer` (ADR-011 guard) | E2E | P1 |
| TC-003-E2E-08 | anonymous | Open `https://delivery…/driver` directly | HTTP 200 from nginx, the app redirects to `/login` | E2E | P1 |
| TC-003-E2E-09 | — | Open `/qa-no-such-route/deep` | HTTP 200. The client NotFound view is shown | E2E | P1 |
| TC-003-E2E-10 ×2 | — | Open `/status` at 360 and 1280, recording requests | *API reachable* shown. A request went to `<API>/api/status/`. None to `/api/health`. The configured API base URL is shown | E2E | P1 |
| TC-003-E2E-11 | store user | Log in, open `/status` | Also shows the username and `STORE` from `/api/users/me/` | E2E | P2 |
| TC-003-E2E-12 | SW blocked, `/api/status/` held | Open `/status`; while held → loading; abort (connection refused) → unavailable; unroute + Retry | Loading, then unreachable/unavailable with a Retry button, then *API reachable* | E2E | P1 |
| TC-003-E2E-13 | SW blocked | `/api/status/` mocked 500 `SERVER_ERROR` envelope | Error state with Retry. Not *API reachable*, not a blank page | E2E | P1 |
| TC-003-E2E-14 | fully mocked auth | Log in → the first `/me` returns 401 `TOKEN_INVALID` → refresh returns a new access token | Exactly **1** refresh. `/me` called twice, the retry with the new bearer. Lands on `/customer` | E2E | P1 |
| TC-003-E2E-15 | fully mocked | `/me` 401 and refresh 401 | Exactly 1 refresh (no loop). Redirect to `/login`. Refresh token removed from localStorage | E2E | P1 |
| TC-003-E2E-16 | mocked | Login returns 429 `THROTTLED`, `Retry-After: 42` | A rate-limit message (not a generic error) | E2E | P1 |
| TC-003-E2E-17 | mocked | `/api/status/` returns 429 | Status page shows *rate-limited* | E2E | P2 |
| TC-003-E2E-18 ×6 | — | `/login`, `/status`, unknown route at 360 and 1280 | No horizontal overflow. Login inputs have accessible labels | E2E | P2 |

### 2.3 Manual / evidence review (TASK-010)
| ID | Preconditions | Steps | Expected | Level | Priority |
|---|---|---|---|---|---|
| TC-003-MAN-01 | deployed | Headless Chromium on the server: check the install criteria with a Lighthouse-free manual check (manifest + SW + HTTPS already covered). Record a 360-px and a 1280-px screenshot of `/login` and `/status` as evidence | Screenshots attached. No broken layout | MAN | P2 |
| TC-003-MAN-02 | — | 403 / 404 mapping: mock `/me` 403 `PERMISSION_DENIED` and 404 `NOT_FOUND` (exploratory, Playwright interception) | A typed error is shown with no crash and no logout on 403 | MAN | P2 |
| TC-003-MAN-03 | — | Empty-state component: no Sprint-1 screen uses it. Review TASK-007's Vitest evidence for the component, and check it renders if a placeholder area uses it | The component exists and has unit-test evidence. A gap is noted if it is unused | MAN | P3 |
| TC-003-MAN-04 | TASK-007 Completion Report | Review the `npm ci`, `lint`, `type-check`, `test:unit`, `build` outputs recorded by Frontend (local build gates, ADR-018). If in doubt, **ask the TL** for a re-run; QA does not run them locally | All green, outputs quoted | MAN | P1 |
| TC-003-MAN-05 | — | Read the network requests in TC-003-E2E-03: `POST <API>/api/auth/token/` has no cookies (no credentials mode) and the password is not in the URL | Confirmed | MAN | P2 |

## 3. Execution order (TASK-010)
1. `make qa-remote ARGS="smoke/test_web_serving.py"`
2. `make qa-remote ARGS="-m e2e"`. Logins are paced by `AuthPacer` (10/minute), so expect roughly 2–3 minutes.
3. The manual cases in §2.3.

## 4. Exit criteria
- All P1 cases PASS.
- Interception-based cases are labelled as such in the report.
- No open Critical/High bug.
- `.ai/reports/qa/FEAT-003-qa-report.md` is written with the evidence.
