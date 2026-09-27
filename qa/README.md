# Flash QA suite

This is QA's black-box suite: pytest + httpx for the API, and Playwright (Chromium) for the Vue PWA. It is owned by QA (ADR-007). It never imports backend or frontend code.

> **QA never runs locally.** The suite runs **on the server** against the deployed instance, through `make qa-remote` (REQ-009, ADR-018). The harness refuses to run where `/srv/flash/qa` does not exist, and it rejects non-HTTPS or local target URLs. Locally you may edit files, and you may run `pytest --collect-only` in a scratch venv to check syntax.

Strategy, severity rules and policies: [`plans/test-strategy.md`](plans/test-strategy.md). Test plans: [`plans/FEAT-001-test-plan.md`](plans/FEAT-001-test-plan.md), [`FEAT-003`](plans/FEAT-003-test-plan.md), [`FEAT-004`](plans/FEAT-004-test-plan.md).

## How to run (from the repository root, on the local machine)

The `make` targets are owned by Infrastructure. They SSH to the server and run there.

```bash
make seed-qa-users                                   # once per server/reseed: creates qa_customer, qa_driver, qa_store, qa_admin
make qa-remote ARGS="--collect-only -q"              # harness installs + imports on Python 3.13 (TASK-008 check)
make qa-remote ARGS="-m 'smoke or deploy'"           # post-deploy gate
make qa-remote ARGS="-m 'regression and not e2e'"    # API + deployment regression baseline
make qa-remote ARGS="-m e2e"                         # Playwright, Chromium headless, one worker
make throttle-reset && make qa-remote ARGS="-m ratelimit"; make throttle-reset   # rate limits: own session, LAST
make qa-remote ARGS="-m deploy -k dental --dental-expect='https://dental.hossam-ameen.online/=200,https://api.dental.hossam-ameen.online/=404'"  # compare with a baseline (use the codes you recorded)
make test-backend-remote REF=<deployed sha>          # developer-suite audit (FEAT-001 AC9)
```

- `make qa-remote` rsyncs `qa/` to `/srv/flash/qa/suite/`, installs `requirements.txt` into `/srv/flash/qa/venv` (uv, Python 3.13), runs `pytest $ARGS` from the suite root, and copies the results back to **`qa/.results/latest/`** (git-ignored).
- Results contain:
  - `junit.xml`
  - `pytest.log`: method, host, path and status per request; never query strings or bodies
  - `dental-<UTC>.json`
  - `resources.txt`
  - `playwright/*.png`: screenshots of failures
- Rate-limit tests are **deselected automatically** unless `-m` names `ratelimit`. A normal run therefore reports `N/M collected (5 deselected)`, and those 5 are `api/test_ratelimit.py`. Never run them while a deploy is in progress.
- Rules for functional tests:
  - one login per role per session
  - every `/api/auth/*` call is paced under `RATELIMIT_AUTH` by `AuthPacer`, so a run may pause for up to a minute
  - a 429 is never retried

## Environment variables

All values come from the environment. Nothing secret has a default, and nothing secret is ever printed.

| Variable | Set by | Meaning |
|---|---|---|
| `QA_BASE_URL` | `make qa-remote` | API base, `https://api.delivery.hossam-ameen.online`. Must be HTTPS and non-local |
| `QA_WEB_URL` | `make qa-remote` | PWA base, `https://delivery.hossam-ameen.online` |
| `QA_HEALTH_TOKEN` | `make qa-remote`, from the server's `shared/.env` `HEALTH_CHECK_PASSWORD`, exported only into pytest | Health token. Sent only as the `X-Health-Check-Token` header |
| `QA_CUSTOMER_USERNAME` / `QA_CUSTOMER_PASSWORD` | `/srv/flash/qa/credentials.env` (from `make seed-qa-users`, 0600) | CUSTOMER QA user |
| `QA_DRIVER_USERNAME` / `QA_DRIVER_PASSWORD` | same | DRIVER QA user |
| `QA_STORE_USERNAME` / `QA_STORE_PASSWORD` | same | STORE QA user |
| `QA_ADMIN_USERNAME` / `QA_ADMIN_PASSWORD` | same | ADMIN QA user (staff + superuser) |
| `QA_INACTIVE_USERNAME` / `QA_INACTIVE_PASSWORD` | optional, not seeded yet | Inactive user for TC-001-JWT-07 (skipped without it) |
| `QA_DEPLOY_PATH` | default `/srv/flash` | Server layout root. The harness refuses to run if `<path>/qa` is missing |
| `QA_RATELIMIT_ANON/USER/AUTH/HEALTH` | defaults `60/minute`, `300/minute`, `10/minute`, `120/minute` | Must equal the server's `RATELIMIT_*` values |
| `QA_ANON_THROTTLE_PATH` | optional | Public GET path using the anon scope (TC-001-RL-05). Skipped when unset |
| `QA_JWT_ACCESS_LIFETIME_MINUTES` / `QA_JWT_REFRESH_LIFETIME_DAYS` | defaults 30 / 7 | Expected token lifetimes |
| `QA_BACKEND_PORT`, `QA_BACKEND_SERVICE`, `QA_SERVER_PUBLIC_IP` | defaults `8010`, `flash-backend`, `34.123.215.195` | Runtime checks |
| `QA_DENTAL_URLS`, `QA_DENTAL_SERVICE` | defaults: the two dental HTTPS URLs, `dental-clinic-backend` | Read-only non-interference checks |
| `QA_CERT_MIN_DAYS`, `QA_RELEASES_TO_KEEP`, `QA_DB_BACKUPS_TO_KEEP`, `QA_MIN_FREE_DISK_MB` | defaults `60`, `5`, `5`, `1500` | Deployment thresholds |
| `QA_HTTP_TIMEOUT` | default `20` | Seconds per request |

## Layout

```
qa/
├── conftest.py        root fixtures, server-only guard, secret scrubbing, ratelimit ordering
├── pytest.ini         markers: smoke, regression, security, ratelimit, deploy, e2e
├── requirements.txt   pinned: pytest, httpx, playwright, pytest-playwright
├── harness/           config (env), secrets (Secret/redact), envelope assertions, http (clients, JWT, AuthPacer), pwa
├── api/               API contract tests (status, health, envelope, JWT, users/me, OpenAPI, admin, CORS, ratelimit)
│   └── flows/         multi-actor business flows (from FEAT-008)
├── smoke/             deployment checks (TLS, redirects, HSTS, SPA serving, dental, server runtime)
├── e2e/               Playwright tests (Chromium, 360 px + 1280 px, one worker, no traces)
└── plans/             strategy + per-feature test plans
```

## Secret hygiene

- Secrets are wrapped in `harness.secrets.Secret`. Every report is redacted by `conftest.py`, and the session **fails** if a registered secret reaches `.results/`.
- Use `harness.envelope.check()` / `assert_*` helpers, not a bare `assert`, whenever a compared value could contain a secret.
- Playwright tracing and video are disabled because traces record typed passwords.
- `?password=` is used only once, with a wrong value.
