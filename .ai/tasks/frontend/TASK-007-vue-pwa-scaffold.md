# Task

## ID
TASK-007

## Title
Vue PWA scaffold: API client, login, status page, role-area shell, Flash branding

## Feature
FEAT-003 — Frontend Foundation (Vue PWA)

## Description
Scaffold `frontend/` per ADR-008/ADR-011 (both ACCEPTED): Vite + Vue 3 + TypeScript project, PWA manifest and icons from the Flash logo, one API client (envelope / JWT refresh / error codes), a **username + password login screen** using `POST /api/auth/token/`, a **status page** that calls the public `GET /api/status/` (ADR-019), the role-area routing shell, and reusable loading/empty/error/unavailable components. Produces a static `dist/` built on the local machine and served by nginx at `https://delivery.hossam-ameen.online`.

## Business Requirement
REQ-001, REQ-037, REQ-008; business-logic.md §2 (username + password, BLK-001); `01_customer_app/user_flow.md` (UI states); `06_brand/flash_initial_logo.png`; FEAT-003 criteria 1–6; api-contracts.md § Foundation + § Identity (APPROVED); ADR-008, ADR-011, ADR-019

## Agent
Frontend

## Scope (allowed paths)
- `frontend/**` (copy the logo into `frontend/public/` or `frontend/src/assets/`; do not modify `06_brand/`)

## Dependencies
- ADR-008 ACCEPTED, ADR-011 ACCEPTED (BLK-002 RESOLVED)
- FEAT-001 contracts APPROVED in api-contracts.md (done). No runtime dependency on the backend for building or unit tests (mock the HTTP layer).
- Runs **in parallel** with the backend chain and Infrastructure.

## Acceptance Criteria

- [ ] Project: Vite + Vue 3 + TS + Vue Router + Pinia + `vite-plugin-pwa` + Vitest + ESLint + Prettier + `vue-tsc`. `package.json` scripts with these exact names (Infrastructure calls them): `lint`, `type-check`, `test:unit` (Vitest, non-watch), `build` (type-check is allowed inside build). `package-lock.json` committed; `engines.node` set (≥ 20).
- [ ] **Build contract (for TASK-013):** `npm ci && npm run build` in `frontend/` with `VITE_API_BASE_URL` (and optional `VITE_APP_NAME`, default `Flash`) in the environment produces `frontend/dist/` with `base: '/'`. A production build without `VITE_API_BASE_URL` fails with a clear message. `frontend/.env.example` documents the variables; `.env*` (except the example) git-ignored. No URL hardcoded anywhere.
- [ ] PWA installable: manifest (`name`/`short_name` Flash, `start_url: /`, `display: standalone`, theme/background colors taken from the logo), service worker (`registerType: autoUpdate`; navigation fallback to `index.html`, API calls **not** cached), icons 192, 512 and a maskable 512 generated from `06_brand/flash_initial_logo.png`, plus favicon and apple-touch-icon.
- [ ] API client (one module): base URL from `VITE_API_BASE_URL`; unwraps the envelope; `Authorization: Bearer` from the auth store; on 401 from a Bearer call → one refresh (`/api/auth/token/refresh/`) and retry, concurrent 401s share one refresh, refresh failure → logout + redirect to `/login`; maps 400/403/404/429/5xx/network errors to typed errors exposing `errors.code`, field errors and `Retry-After` for 429.
- [ ] Auth store (Pinia): access token in memory, refresh token in `localStorage` (ADR-008), `login(username, password)`, `logout()`, `loadMe()` via `GET /api/users/me/`.
- [ ] `/login`: username + password form, client-side required-field validation, submit disabled while loading, shows the API message for `INVALID_CREDENTIALS` and a rate-limit message for 429, never logs the password; on success loads `me` and routes to the role area.
- [ ] `/status`: calls `GET /api/status/` and shows *API reachable* / *unreachable* / *rate-limited* with the configured API base URL and a retry; when logged in also shows username + role from `/api/users/me/`. It must **not** call `/api/health/` or contain any health token (ADR-019).
- [ ] Routing: `/` → role area if logged in, else `/login`; lazy-loaded placeholder areas `/customer`, `/driver`, `/store`, `/admin` (heading + logout only, no business screens); a guard redirects a user to their own role's area; unknown routes → a NotFound view (client-side). Deep links work with the nginx SPA fallback.
- [ ] State components: loading, empty, error (with retry), unavailable; used by the status page.
- [ ] Responsive at 360 px and 1280 px; basic a11y (labels, focus, contrast).
- [ ] On the local machine (build gates, ADR-018): `npm ci`, `npm run lint`, `npm run type-check`, `npm run test:unit`, `npm run build` all pass; outputs in the Completion Report.

## Technical Notes

- No business logic and no business screens (REQ-001, REQ-037). The login form is allowed by FEAT-003's scope note (username + password).
- i18n depends on BLK-009 — structure strings for it, one locale (English).
- Web and API are different origins; the backend allows `https://delivery.hossam-ameen.online` via CORS (ADR-008). Use no cookies/credentials mode.
- Keep the initial bundle small (the logo PNG is 1254 px: generate resized icons, do not ship the original in the app shell).
- You may not run QA suites; QA verifies on the server (TASK-010).

## Testing Requirements

- Vitest unit tests: API client (envelope unwrap, error mapping incl. 429 Retry-After, single refresh on concurrent 401s, logout on refresh failure), auth store, route guard (role redirect, anonymous → /login), login view (validation, error display), status view (ok / unreachable / 429), state components.

## Plan Review Required
Yes — first frontend architecture. **Pre-approved** against ADR-008/011/019 and the criteria above: write a short `## Implementation Plan` (structure, libraries + versions, icon generation approach) and proceed; the TL reviews it with the code. Any new dependency beyond the listed stack (e.g. a UI kit) or a different token storage needs TL approval before coding.

## Status

QA_IN_PROGRESS

## Activity Log
- 2026-09-27 | team-lead | — → TODO | created from sprint-01 technical plan
- 2026-09-27 | team-lead | TODO → BLOCKED | waiting on BLK-002 (ADR-008 PROPOSED)
- 2026-09-27 | team-lead | BLOCKED → TODO | BLK-002 RESOLVED, ADR-008 + ADR-011 ACCEPTED; scope: login (username + password), status page on `/api/status/` (ADR-019), Flash branding, env-driven API URL, build contract for TASK-013; plan pre-approved
- 2026-09-27 | frontend | TODO → IN_PROGRESS | started; Implementation Plan written (pre-approved, conditional)
- 2026-09-27 | frontend | IN_PROGRESS → READY_FOR_REVIEW | scaffold done; npm ci/lint/type-check/test:unit (67 passed)/build green locally; see Completion Report
- 2026-09-27 | team-lead | READY_FOR_REVIEW → REVIEW | code review started
- 2026-09-27 | team-lead | REVIEW → READY_FOR_QA | code review APPROVED (Review Log); build gates re-run green; browser/installability checks → QA TASK-010
- 2026-09-28 | qa | READY_FOR_QA → QA_IN_PROGRESS | FEAT-003 verification on the deployed web domain started (TASK-010)

## Implementation Plan
(frontend, 2026-09-27 — written under the TL's conditional pre-approval; no deviation from ADR-008/011/019)

**Libraries (exact stack of ADR-008, versions pinned by `package-lock.json`):** vue 3.5, vue-router 5.3, pinia 4.0, vite 8.x, @vitejs/plugin-vue 6, vite-plugin-pwa 1.3 (+ its peers workbox-build/workbox-window 7.4), vitest 4.1 + @vue/test-utils 2.5 + jsdom, typescript ~6.0 + vue-tsc 3.3, eslint 10 + eslint-plugin-vue + @vue/eslint-config-typescript + @vitest/eslint-plugin + eslint-config-prettier, prettier 3. Baseline from `create-vue` 3.24 (TS/router/pinia/vitest/eslint/prettier) **minus** oxlint, vue devtools plugin and npm-run-all2 (not in the listed stack; scripts use `&&`). No UI kit, no i18n library, no HTTP library (native `fetch`). `engines.node: ^20.19.0 || >=22.12.0` (Vite 8 minimum, ≥ 20).

**Structure (`frontend/`):**
- `src/config/env.ts` — reads `VITE_API_BASE_URL` / `VITE_APP_NAME` (default `Flash`); `vite.config.ts` fails a production build without `VITE_API_BASE_URL`.
- `src/api/` — `errors.ts` (typed `ApiError` with `status`, `kind`, `code`, `fieldErrors`, `retryAfter`), `client.ts` (single module: envelope unwrap, Bearer, single shared refresh on 401, logout hook, `credentials: 'omit'`), `auth.ts` / `status.ts` (only the contract endpoints: `/api/auth/token/`, `/api/auth/token/refresh/`, `/api/users/me/`, `/api/status/`).
- `src/stores/auth.ts` — access token in memory, refresh token in `localStorage` (ADR-008), `login`, `logout`, `loadMe`, `restore`.
- `src/router/` — `/login`, `/status`, lazy `/customer|/driver|/store|/admin` placeholders, `/` redirect, NotFound catch-all; guard: anonymous → `/login`, wrong role → own area (role → area map is routing only, no business rule).
- `src/components/state/` — `LoadingState`, `EmptyState`, `ErrorState` (retry), `UnavailableState`; `AppLogo`, `RoleAreaShell`.
- `src/i18n/en.ts` + tiny `t()` helper — all UI strings in one English catalog, keyed, ready for BLK-009 (no RTL/Arabic UI until BLK-009; the Arabic tagline appears only as part of the logo image).
- `src/styles/` — CSS custom properties from the logo colours (orange `#FE8015` → amber `#FEAE17`, blue `#066EF9`/`#0044C4`, navy `#0C214F`), mobile-first.
- Tests in `src/**/__tests__/` (Vitest, `fetch` mocked, no backend needed).

**Icons:** `frontend/scripts/generate_icons.py` (Python 3 + Pillow, already on the build machine; no npm dependency) crops the F-mark from `06_brand/flash_initial_logo.png` and writes `public/icons/{icon-192,icon-512,maskable-512,apple-touch-icon-180}.png`, `public/favicon.ico` (16/32/48) and a 480 px `src/assets/flash-logo.png` (full lockup incl. tagline, for the login page). The generated PNGs are committed; the 1254 px original is not shipped.

**PWA:** vite-plugin-pwa `registerType: 'autoUpdate'`, generateSW, `navigateFallback: '/index.html'` with a denylist for `/api/`, no runtime caching (API never cached; API is another origin anyway), manifest `name/short_name` from `VITE_APP_NAME`, `start_url /`, `display standalone`, `theme_color #0C214F`, `background_color #FFFFFF`.

## Completion Report
(frontend, 2026-09-27)

- **Files changed** (all new, only under `frontend/`; nothing committed):
  - Tooling: `package.json`, `package-lock.json`, `vite.config.ts`, `vitest.config.ts`, `eslint.config.ts`, `tsconfig.json`, `tsconfig.app.json`, `tsconfig.node.json`, `tsconfig.vitest.json`, `env.d.ts`, `index.html`, `.env.example`, `.gitignore`, `.prettierrc.json`, `.prettierignore`, `.editorconfig`, `.gitattributes`
  - Branding: `scripts/generate_icons.py` (Pillow, build machine only), generated `public/favicon.ico`, `public/icons/{icon-192,icon-512,maskable-512,apple-touch-icon-180}.png`, `src/assets/flash-logo.png` (480 px lockup incl. the Arabic tagline, 83 kB; the 1254 px original is not shipped)
  - Config / i18n: `src/config/env.ts`, `src/i18n/{en.ts,index.ts}`
  - API layer: `src/api/{client.ts,errors.ts,auth.ts,status.ts}`
  - State/app: `src/stores/auth.ts`, `src/app/{authBridge.ts,roles.ts}`, `src/router/{index.ts,guard.ts}`, `src/main.ts`, `src/App.vue`, `src/styles/main.css`
  - UI: `src/components/state/{LoadingState,EmptyState,ErrorState,UnavailableState}.vue`, `src/components/{AppLogo,RoleAreaShell}.vue`, `src/views/{LoginView,StatusView,NotFoundView}.vue`, `src/views/areas/{Customer,Driver,Store,Admin}AreaView.vue`
- **Tests added** (Vitest 5 + Vue Test Utils + jsdom, `fetch` mocked, no backend): 9 files / 67 tests
  - `src/api/__tests__/client.spec.ts` — envelope unwrap, base URL + `credentials: 'omit'`, Bearer header, success:false, 400 field errors, 403/404/500 codes, 429 + `Retry-After`, network error, non-JSON 502, 401 → one refresh + retry, **3 concurrent 401s share one refresh**, refresh rejected → `onAuthFailure`, retried call still 401 → `onAuthFailure`, refresh unreachable → no logout, public calls never refresh
  - `src/api/__tests__/errors.spec.ts` — `Retry-After` seconds/HTTP-date/invalid, `errors` split, status → kind table
  - `src/stores/__tests__/auth.spec.ts` — login (access in memory, refresh in localStorage, password never stored), INVALID_CREDENTIALS, logout, session restore from refresh token, rejected refresh → logout, unreachable API keeps refresh token, `loadMe` single refresh
  - `src/router/__tests__/guard.spec.ts` — anonymous → /login, /login & /status & NotFound reachable, each role → own area from `/` and `/login`, cross-role redirect, unknown role → /status
  - `src/app/__tests__/authBridge.spec.ts` — refresh rejected → logout + redirect `/login?expired=1`
  - `src/views/__tests__/LoginView.spec.ts` — labels, required validation (no API call), API message for INVALID_CREDENTIALS, 429 message with seconds, backend field errors, submit disabled while loading → role area, password not in console, network error
  - `src/views/__tests__/StatusView.spec.ts` — reachable + base URL + only `/api/status/` called (never `/api/health/`), unreachable + retry, 5xx, rate-limited + Retry-After, username + role from `/api/users/me/`
  - `src/components/state/__tests__/states.spec.ts`, `src/i18n/__tests__/i18n.spec.ts`
- **Validation commands run + results** (local build machine, Node v24.3.0 / npm 11.4.2, from a clean `rm -rf node_modules dist`; build gates per ADR-018 — no dev server, no QA suites):
  ```
  $ npm ci              → added 633 packages, found 0 vulnerabilities            EXIT 0
                          (warnings: EBADENGINE nopt@10/abbrev@5 via @vue/test-utils→js-beautify, dev-only;
                           deprecated glob@11 via workbox-build, dev-only)
  $ npm run lint        → eslint . --cache (no findings)                          EXIT 0
  $ npm run format:check→ prettier --check src/ (all files formatted)             EXIT 0
  $ npm run type-check  → vue-tsc --build (no errors)                             EXIT 0
  $ npm run test:unit   → vitest run: Test Files 9 passed (9), Tests 67 passed (67)  EXIT 0 (3 consecutive runs green)
  $ VITE_API_BASE_URL=https://api.delivery.hossam-ameen.online npm run build
                        → vue-tsc --build && vite build: 73 modules, built in 604ms;
                          PWA v1.3.0 generateSW, precache 32 entries (373.19 KiB); dist/ = 428 KB   EXIT 0
                          initial JS dist/assets/index-*.js 104.73 kB (gzip 40.85 kB); each role area a separate ~0.25 kB chunk
  $ env -u VITE_API_BASE_URL npm run build
                        → "Error: [flash] VITE_API_BASE_URL is not set. A production build needs the API origin …
                           See frontend/.env.example."                            EXIT 1 (no dist/ produced)
  ```
  dist checks: `manifest.webmanifest` = name/short_name `Flash`, `start_url /`, `scope /`, `display standalone`, `theme_color #0C214F`, `background_color #FFFFFF`, icons 192/512/maskable-512; `index.html` links favicon + apple-touch-icon + manifest + `registerSW.js`; `sw.js` has exactly one route: `NavigationRoute(createHandlerBoundToURL("/index.html"), denylist [/^\/api\//])`, no runtime caching; the bundle references only `/api/auth/token/`, `/api/auth/token/refresh/`, `/api/users/me/`, `/api/status/`; `grep` finds no `api/health`, `HEALTH` or `X-Health` in `dist/`; no URL hardcoded in `src/` (API origin only via `VITE_API_BASE_URL`).
- **Build output:** `frontend/dist/` (`base: '/'`), git-ignored; built with `VITE_API_BASE_URL=https://api.delivery.hossam-ameen.online`. TASK-013 contract: `cd frontend && npm ci && VITE_API_BASE_URL=… npm run build`.
- **Screens and states covered:** `/login` (form, required validation, loading/disabled, API message, 429, field errors, network, session-expired notice), `/status` (loading, reachable, unexpected answer, unreachable/5xx with retry, rate-limited with retry; session: loading, signed-in user, error with retry, empty "Not signed in"), `/customer|/driver|/store|/admin` placeholders (heading + signed-in user + logout, no business screens), NotFound. Mobile-first CSS (single column, 44 px touch targets, `.page` max 960 px, wider padding ≥ 768 px), labels on all inputs, `aria-invalid`/`aria-describedby`, `role=alert|status`, visible focus ring, skip link, `prefers-reduced-motion`, text colours ≥ 6.5:1 on white.
- **Contract/OpenAPI changes:** none. Only APPROVED Foundation + Identity endpoints are called. Env variables: only `VITE_API_BASE_URL` (required for production builds) and `VITE_APP_NAME` (optional, default `Flash`), both already in ADR-008 — nothing new for Infrastructure.
- **Deviations from the Implementation Plan (same libraries, versions only):** Vitest 5.0.2 instead of 4.1 (npm's peer resolution through `@vitest/eslint-plugin`'s `vitest: *` peer crashed with vitest 4 — `Cannot read properties of null (reading 'edgesOut')`); jsdom 29.1 instead of 30 (jsdom 30 needs Node ≥ 24.15, the build machine has 24.3). Final pinned versions are in `package-lock.json`: vue 3.5.x, vue-router 5.3.x, pinia 4.0.x, vite 8.3.1, vite-plugin-pwa 1.3.0, vitest 5.0.2, typescript 6.0.x, vue-tsc 3.3.x, eslint 10.x, prettier 3.9.6. No UI kit, no i18n library, no HTTP library.
- **Known limitations / remaining problems:**
  1. **For TL / Backend (TASK-001/002): `Retry-After` is not a CORS-safelisted response header.** Because the PWA and the API are different origins, the browser hides `Retry-After` unless the API sends `Access-Control-Expose-Headers: Retry-After` (django-cors-headers `CORS_EXPOSE_HEADERS = ["Retry-After"]`). Without it the client still maps 429 correctly but shows the generic "please wait" message instead of the seconds. Not blocking this task; please add it to the backend CORS settings / contract.
  2. Refresh-failure policy (interpretation for TL review): a **rejected** refresh (400/401) logs out and redirects to `/login?expired=1`; an **unreachable** refresh (network/5xx/429) fails the request without logging out, so a temporary outage does not destroy the session. Tell me if the TL wants logout on every refresh failure.
  3. Logout is client-side only (no logout/blacklist endpoint in the contract); the refresh token remains valid on the server until it expires. Refresh token in `localStorage` is the ADR-008 known limitation.
  4. i18n: one English catalog (`src/i18n/en.ts`), `lang="en" dir="ltr"`, CSS uses logical properties (`inset-inline-start`, `border-inline-start`) ready for RTL; languages/RTL wait for BLK-009. The Arabic tagline appears only inside the logo image.
  5. Responsive (360 px / 1280 px) and installability were **not** checked in a browser: no dev server or manual QA per the PO rule. QA verifies on the server (TASK-010), e.g. Lighthouse installability and viewport screenshots.
  6. Brand colours are sampled from the preliminary logo (`06_brand/README.md`: "can be replaced after final brand approval"); re-run `python3 scripts/generate_icons.py` if the logo changes.
  7. Deep links rely on the nginx SPA fallback (`try_files … /index.html`, ADR-015) plus the service worker navigation fallback; unknown paths render the client-side NotFound view (HTTP 200 from nginx).

## Review Log
- 2026-09-27 | team-lead | PLAN PRE-APPROVED (conditional) | valid while the plan follows ADR-008/011/019 and the Acceptance Criteria

### Review — 2026-09-27 — team-lead — code

**Verdict:** APPROVED

**Checked:**
- [x] Scope limited to the task; no unrelated changes (all files under `frontend/`; `06_brand/` untouched; generated icons only)
- [x] Business rules match `business-logic.md` / `flash_business_logic/` (none invented; no business screens; role → area map is routing only)
- [x] Authorization: the client never decides authorization; guard = anonymous → `/login`, wrong role → own area; backend stays authoritative
- [x] State transitions — n/a (no order logic)
- [x] Money — n/a
- [x] API contract matches `api-contracts.md`: only `/api/auth/token/`, `/api/auth/token/refresh/`, `/api/users/me/`, `/api/status/`; envelope unwrap; `errors.code` / field errors; 429 + `Retry-After`; never `/api/health/` (grep of `dist/`: no `api/health`, `HEALTH`, `X-Health`)
- [x] Tests are meaningful (client refresh concurrency, rejected vs unreachable refresh, 429, guard, views, states); validation commands pass (below)
- [x] Migrations — n/a
- [x] No hardcoded secrets, domains, ports, paths (only origin in `dist/` is the `VITE_API_BASE_URL` value passed at build time; `.env*` ignored except the example)
- [x] Complies with the frontend ADRs (ADR-008 stack, no UI kit/HTTP/i18n library; ADR-011 role areas code-split; ADR-019 status endpoint)
- [x] Infra — n/a (build contract for TASK-013 honoured: `npm ci && VITE_API_BASE_URL=… npm run build` → `frontend/dist`, `base: '/'`; missing URL → exit 1 with a clear message)

**Decisions on the Frontend agent's points:**
- (a) **`Retry-After` exposure — confirmed and now in the contract.** `api-contracts.md` §1.1 (new "Cross-origin" rule) and ADR-008 now state `CORS_EXPOSE_HEADERS = ["Retry-After"]`. Backend already has it in `backend/config/settings/base.py:121` with a test in `backend/tests/test_settings.py` (reviewed with the backend tasks, not here). Until it ships, the client degrades to the generic 429 message, which is correct.
- (b) **Refresh-failure policy — APPROVED as implemented.** Rejected refresh (400/401, or no stored refresh token, or retried call still 401) → logout + `/login?expired=1`; unanswered refresh (network, 5xx, 429) → the request fails, session kept. Written into `api-contracts.md` § Identity "Client behavior" and ADR-008.
- (c) **Vitest 5.0.2 and jsdom 29 — ACCEPTED.** Same libraries as ADR-008 (which pins no versions); the reasons (npm peer-resolution crash with vitest 4 via `@vitest/eslint-plugin`; jsdom 30 needs Node ≥ 24.15) are valid, both are dev-only, versions locked by `package-lock.json`; `npm audit` 0 vulnerabilities. No ADR change needed.
- (d) **Client-side-only logout + refresh token in `localStorage` — ACCEPTED as a known limitation**, recorded in ADR-008 and api-contracts § Identity: the refresh token stays valid until `JWT_REFRESH_TOKEN_LIFETIME_DAYS`. To be revisited in one ADR (httpOnly cookie + blacklist/logout endpoint) before real customer data exists.
- (e) **Browser layout (360/1280 px) and PWA installability — moved to QA TASK-010**, which already covers them (Playwright at 360 and 1280 px; manifest/service worker/icons). The corresponding AC lines here are satisfied at code level (mobile-first CSS, manifest, SW, icons verified in `dist/`) and are verified in the browser by QA.
- (f) **English-only UI until BLK-009 — ACCEPTED** (keyed catalog `src/i18n/en.ts`, logical CSS properties). Recorded in ADR-008.

**Findings:**
1. [non-blocking] `src/stores/auth.ts` `ensureSession` — when the refresh endpoint is unreachable on page load the guard sends the user to `/login` while the refresh token is kept; a later navigation/reload recovers. Acceptable under decision (b); QA should see the login screen (not a crash) with the API down.
2. [non-blocking] `vite.config.ts` — `orientation: 'portrait'` in the manifest locks installed-app rotation (admin/store on tablets). Fine for sprint-01; revisit when the admin/store screens are designed.
3. [non-blocking] Brand colours come from the preliminary logo (`06_brand/README.md`); `scripts/generate_icons.py` regenerates icons when the final logo lands.

**Commands run** (local build machine, Node v24.3.0; build gates only per ADR-018 — no dev server, no QA suites, no browser):
```
npm ci                                         → 0 vulnerabilities                         EXIT 0
npm run lint                                   → no findings                               EXIT 0
npm run format:check                           → all files formatted                       EXIT 0
npm run type-check                             → vue-tsc --build, no errors                EXIT 0
npm run test:unit                              → Test Files 9 passed (9), Tests 67 passed  EXIT 0
VITE_API_BASE_URL=https://api.delivery.hossam-ameen.online npm run build
                                               → vite build + PWA generateSW, precache 32 entries (373.19 KiB)  EXIT 0
env -u VITE_API_BASE_URL vite build            → "[flash] VITE_API_BASE_URL is not set…"   EXIT 1
npm audit --audit-level=high                   → 0 vulnerabilities
dist checks: manifest (Flash, start_url /, scope /, standalone, #0C214F/#FFFFFF, 192/512/maskable-512);
             no api/health|HEALTH|X-Health in dist/; only origin in JS = the VITE_API_BASE_URL value
code inspection: api/client.ts, api/errors.ts, stores/auth.ts, app/authBridge.ts, router/{index,guard}.ts,
                 views/{Login,Status}View.vue, config/env.ts, vite.config.ts, .env.example, .gitignore
```

## QA Log

## Sign-off
- TL final review: ☐
- QA verdict: ☐
- PM acceptance: ☐
