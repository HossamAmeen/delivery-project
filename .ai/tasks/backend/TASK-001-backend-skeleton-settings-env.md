# Task

## ID
TASK-001

## Title
Backend skeleton, split settings & environment configuration

## Feature
FEAT-001 — Backend Platform Foundation

## Description
Create `backend/` following DRF_SKILL.md §3, §7, §8, §9, §37, §45: project skeleton, split settings, django-environ configuration, DATABASE_URL, requirements files, pytest.ini, Makefile, ruff config, .gitignore, .env.example, README.

## Business Requirement
REQ-002, REQ-008, REQ-009; DRF_SKILL.md §3, §7–9, §37, §45, §78; ADR-012, ADR-015, ADR-016, ADR-017; FEAT-001 criteria 1, 2, 9; FEAT-004 "Backend: production settings" (criteria 4, 5, 11)

## Agent
Backend

## Scope (allowed paths)
- `backend/` (root files), `backend/config/**`, `backend/requirements/**`, `backend/apps/__init__.py`

## Dependencies
- none to start coding
- **TASK-012** (server sandbox + `make test-backend-remote`) before you move to READY_FOR_REVIEW: all validation evidence comes from the server (ADR-016, ADR-018). Never run the test suite locally (REQ-009).

## Acceptance Criteria

- [ ] `backend/` matches the DRF_SKILL.md §3 layout for the parts in scope (apps/ empty except `__init__.py`).
- [ ] `config/settings/{base,development,production}.py` exist; production has DEBUG off and secure defaults (secure cookies, HSTS and SSL redirect configurable by env).
- [ ] Every configurable value is read from env; `backend/.env.example` lists all variables from DRF_SKILL §8 and §78 plus the server variables below, with safe placeholders; `.env` is git-ignored.
- [ ] `DATABASE_URL` via dj-database-url, SQLite default. When the engine is SQLite, `OPTIONS` = `timeout 20`, `transaction_mode "IMMEDIATE"`, `init_command` with `journal_mode=WAL; synchronous=NORMAL; busy_timeout=20000; foreign_keys=ON` and `CONN_MAX_AGE=0` (ADR-017). A settings test proves the options are applied for SQLite only.
- [ ] Server/proxy settings from env (ADR-015): `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS` (django-cors-headers, middleware placed per its docs), `CSRF_TRUSTED_ORIGINS`, `SECURE_PROXY_SSL_HEADER` (env `SECURE_PROXY_SSL_HEADER=HTTP_X_FORWARDED_PROTO,https` → tuple; unset = None), `SECURE_SSL_REDIRECT` (default False in production; nginx redirects), `SECURE_HSTS_SECONDS` (env, default 0 because nginx sets HSTS), `SESSION_COOKIE_SECURE`/`CSRF_COOKIE_SECURE` True in production, `STATIC_ROOT`, `MEDIA_ROOT`, `STATIC_URL=/static/`, `MEDIA_URL=/media/`, `API_DOCS_PUBLIC` (default True in development, False in production; used by TASK-004).
- [ ] `requirements/{base,development,production}.txt` pinned; Django ≥ 5.1 (for the SQLite `init_command`/`transaction_mode`), `django-cors-headers` in base, `gunicorn` in production; all Python 3.13 compatible. No `psycopg`/`redis` needed for the server (they may stay optional/commented).
- [ ] `pytest.ini`, `backend/Makefile` (DRF_SKILL §45 developer targets + `test-rate-limit`; `docker-*`/`deploy-*` targets delegate to the root Makefile per ADR-012, e.g. `test-remote: ; $(MAKE) -C .. test-backend-remote WORKTREE=1`), ruff configured.
- [ ] Logging to stdout/stderr only (journald on the server); no log handler writes secrets or request query strings.
- [ ] On the server via `make test-backend-remote WORKTREE=1` (or `REF=<commit>`): `manage.py check`, `ruff check`, `ruff format --check`, the settings tests pass under Python 3.13. `python manage.py check --deploy` with production settings and server-like dummy env shows no errors (warnings listed in the Completion Report).

## Technical Notes

- No domain apps. Do not run `migrate` before TASK-003 introduces AUTH_USER_MODEL (ADR-003) — `check` only.
- Leave clearly delimited sections in `base.py` (`# --- DRF ---`, `# --- Cache ---`, `# --- Celery ---`, `# --- OpenAPI ---`, `# --- Jazzmin ---`, `# --- Health ---`, `# --- JWT ---`, `# --- CORS/Proxy ---`) for later tasks to fill.
- `TIME_ZONE`/`LANGUAGE_CODE` from env with neutral defaults (UTC/en) — final values pending BLK-009.
- Server values (for reference; the Infrastructure template `deploy/env/shared.env.template` mirrors your `.env.example` names — keep names stable and tell the TL if you add one): `DJANGO_SETTINGS_MODULE=config.settings.production`, `DATABASE_URL=sqlite:////srv/flash/shared/db/flash.sqlite3`, `ALLOWED_HOSTS=api.delivery.hossam-ameen.online,127.0.0.1,localhost`, `CORS_ALLOWED_ORIGINS=https://delivery.hossam-ameen.online`, `CSRF_TRUSTED_ORIGINS=https://api.delivery.hossam-ameen.online,https://delivery.hossam-ameen.online`, `STATIC_ROOT=/srv/flash/shared/static`, `MEDIA_ROOT=/srv/flash/shared/media`.
- `DJANGO_SETTINGS_MODULE` must be overridable by env in `manage.py`/`wsgi.py` (default `config.settings.development` for manage.py, `config.settings.production` for wsgi.py is acceptable if documented).
- Environment loading: read `backend/.env` only if it exists (`environ.Env.read_env` with an explicit path); on the server, systemd provides the environment from `shared/.env`, so the file read must not be required.

## Testing Requirements

- A settings smoke test: settings load with only `.env.example`-style values; production settings refuse to start without SECRET_KEY.

## Plan Review Required
No — standard work fully specified by DRF_SKILL.md and ADR-015/017

## Status

DONE

## Activity Log
- 2026-09-27 | team-lead | — → TODO | created from sprint-01 technical plan
- 2026-09-27 | team-lead | TODO → TODO | re-scoped for the PO hosting decisions: SQLite WAL options, CORS/proxy/static settings, gunicorn, validation on the server via TASK-012 (ADR-015/016/017/018)
- 2026-09-27 | backend | TODO → IN_PROGRESS | started; backend order TASK-001 → 002 → 005 → 004 → 003
- 2026-09-27 | backend | IN_PROGRESS → READY_FOR_REVIEW | implementation + tests done; full server run `make test-backend-remote WORKTREE=1` green (run 20260927-175239-1501198: ruff, format, check, makemigrations, 238 passed, coverage 98.42%)
- 2026-09-27 | team-lead | READY_FOR_REVIEW → REVIEW | code inspection done, decisions recorded; verdict pending the TL's own server validation run (denied by the session permission policy)
- 2026-09-27 | team-lead | REVIEW → READY_FOR_QA | code review APPROVED; TL server run 20260927-204315-12107 at 0a5f845: ruff/format/check/makemigrations PASS, 238 passed, coverage 98.42%
- 2026-09-28 | qa | READY_FOR_QA → QA_IN_PROGRESS | FEAT-001 verification on the server started (TASK-009)
- 2026-09-28 | qa | QA_IN_PROGRESS → QA_IN_PROGRESS | QA verdict PASS ticked; status left for TL final review (.ai/reports/qa/FEAT-001-qa-report.md; server runs 20260927-225552-109762 (API regression), 20260927-225436-108557 (ratelimit), backend audit 20260927-225853-111545)
- 2026-09-28 | team-lead | QA_IN_PROGRESS → READY_FOR_RELEASE | TL final review signed off (QA PASS in .ai/reports/qa/FEAT-001-qa-report.md; no unreviewed changes)
- 2026-09-28 | project-manager | READY_FOR_RELEASE → DONE | FEAT-001 accepted against the DoD (.ai/reports/pm/sprint-01-acceptance-2026-09-28.md)

## Implementation Plan
(not required)

## Completion Report
- Files changed: `backend/manage.py`, `backend/config/{__init__,urls,wsgi,asgi}.py`, `backend/config/settings/{__init__,_helpers,base,development,production,test}.py`, `backend/apps/__init__.py`, `backend/requirements/{base,development,production,celery}.txt`, `backend/.env.example`, `backend/.gitignore`, `backend/pyproject.toml` (ruff + coverage config), `backend/pytest.ini`, `backend/Makefile`, `backend/README.md`, `backend/tests/{__init__,conftest}.py`, `backend/tests/test_settings.py`.
- Tests added: `tests/test_settings.py` (31): SQLite WAL/IMMEDIATE/busy-timeout options applied for SQLite only; proxy-header parsing; development loads with `.env.example` values; SECRET_KEY required everywhere; production secure defaults with server-like env, DEBUG forced off, HSTS/redirect configurable, refuses missing/placeholder `SECRET_KEY`/`HEALTH_CHECK_PASSWORD` and missing `ALLOWED_HOSTS`/`DATABASE_URL`/`STATIC_ROOT`/`MEDIA_ROOT`; `.env.example` documents every variable; `manage.py check --deploy` with production settings and a server-like dummy env exits 0 at `--fail-level ERROR` (subprocess, on the server); logging stream-only; CORS allowed/denied origins; `Retry-After` exposed to the PWA.
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
  `check --deploy` (production settings, server-like dummy env): **0 errors**, 2 warnings, both intentional per ADR-015: `security.W004` (SECURE_HSTS_SECONDS=0: nginx sends HSTS) and `security.W008` (SECURE_SSL_REDIRECT=False: nginx redirects; avoids loops for the 127.0.0.1 health check).
- Contract/OpenAPI changes: none.
- Notes for TL / Infrastructure:
  - Django pinned to **5.2.17 LTS** (≥ 5.1 as required; 6.x not chosen because Jazzmin/simplejwt compatibility is less proven). All pins verified installable on Python 3.13 on the server.
  - `CORS_EXPOSE_HEADERS = ["Retry-After"]` is set (orchestrator/Frontend TASK-007 request) so the PWA can read `Retry-After` on cross-origin 429s; covered by `test_cors_exposes_retry_after_to_the_pwa`. `CORS_ALLOW_CREDENTIALS=False` (Bearer header auth).
  - New env names beyond DRF_SKILL: `DJANGO_ENV_FILE` (optional path of the env file; tests point it at a missing file), `DB_CONN_MAX_AGE`, `LOG_LEVEL`, `LANGUAGE_CODE`, `TIME_ZONE`, `SECURE_HSTS_INCLUDE_SUBDOMAINS`, `SECURE_HSTS_PRELOAD`, `SESSION_COOKIE_SECURE`/`CSRF_COOKIE_SECURE` (dev only; production forces True), `API_PAGE_SIZE`, `API_MAX_PAGE_SIZE`, `JWT_ROTATE_REFRESH_TOKENS`, `FLASH_NEW_USER_PASSWORD` (command only). All have safe defaults; none needs to be in `shared.env` except what ADR-015 already lists.
  - Production refuses to start without `SECRET_KEY`, `ALLOWED_HOSTS`, `DATABASE_URL`, `STATIC_ROOT`, `MEDIA_ROOT`, `HEALTH_CHECK_PASSWORD`, and a non-LocMem `RATELIMIT_CACHE_URL`; the value `change-me` is refused for both secrets.
  - pytest always uses `config.settings.test` (development + LocMem cache, MD5 hasher, test-only app `tests.testapp`) via `--ds` in `pytest.ini`, which wins over the runner's exported `DJANGO_SETTINGS_MODULE=config.settings.development`; the runner's DATABASE_URL/SECRET_KEY etc. still apply. `manage.py check`/`makemigrations` still run with development settings as ADR-018 says.
  - `celery` is in `requirements/celery.txt` (pulled by development.txt), not in production.txt.
- Known limitations / remaining problems:
  - gunicorn's default access log line (`--access-logfile -`, ADR-015 unit) includes the query string, so a `?password=` health request would reach journald. Tooling uses the header only, but Infrastructure may want `--access-logformat` without `%(q)s`/with `%(U)s` in the unit (TASK-013). Not a backend change.
  - `runserver` (development only) logs full request lines; not used on the server.

## Review Log
### Review — 2026-09-27 — team-lead — code (in progress)

**Verdict:** PENDING — not issued yet. Code inspection and the decisions below are done; the TL's own validation run (`make test-backend-remote WORKTREE=1`, which executes the DRF_SKILL §57 commands on the server: `ruff check`, `ruff format --check`, `manage.py check`, `makemigrations --check --dry-run`, `pytest --cov`) was **denied by the session's permission policy** (classified as interfering with the shared server). Per team-lead.md §6 ("do not approve work without running the validation yourself") the verdict waits for that run; Backend's run `20260927-175239-1501198` (238 passed, 98.42 %) is noted but is not the TL's evidence. No blocking defect was found in the inspection.

**Checked so far (inspection):** split settings; env-only config; SQLite ADR-017 options via `build_database`; production fail-fast (`SECRET_KEY`, `ALLOWED_HOSTS`, `DATABASE_URL`, `STATIC_ROOT`, `MEDIA_ROOT`, `HEALTH_CHECK_PASSWORD`, non-LocMem cache); CORS/CSRF/proxy settings; stdout-only logging; `CORS_ALLOW_CREDENTIALS=False`; `CORS_EXPOSE_HEADERS=["Retry-After"]`; no secrets in `backend/.env.example`.

**Decisions on Backend's points:**
- **Django 5.2.17 LTS — ACCEPTED** (recorded in ADR-001 "Runtime pin").
- **pytest uses `config.settings.test` via `--ds` in `pytest.ini` — ACCEPTED** (ADR-001 "Test settings", ADR-018 implementation notes); `check`/`makemigrations` keep the runner's development settings.
- **New optional env names — ACCEPTED** (`DJANGO_ENV_FILE`, `DB_CONN_MAX_AGE`, `LOG_LEVEL`, `LANGUAGE_CODE`, `TIME_ZONE`, `SECURE_HSTS_INCLUDE_SUBDOMAINS`, `SECURE_HSTS_PRELOAD`, `SESSION_COOKIE_SECURE`/`CSRF_COOKIE_SECURE` (dev only), `API_PAGE_SIZE`, `API_MAX_PAGE_SIZE`, `JWT_ROTATE_REFRESH_TOKENS`, `FLASH_NEW_USER_PASSWORD`). TASK-013 told: `FLASH_NEW_USER_PASSWORD` and `DJANGO_ENV_FILE` never go into `shared/.env`; HSTS subdomain/preload stay False.
- **`CORS_EXPOSE_HEADERS=["Retry-After"]` — ACCEPTED**, now in api-contracts §1.1 and ADR-008 (TASK-007 review).
- **gunicorn access log captures `?password=` — ACCEPTED as an Infrastructure requirement:** ADR-015 unit amended (`--access-logformat` with `%(U)s`, no `%(r)s`/`%(q)s`, `%%` escaping) and written into TASK-013 (AC) and TASK-014 (journald evidence). No backend change.
- `check --deploy` warnings W004/W008 — ACCEPTED (nginx owns HSTS and the HTTPS redirect, ADR-015).

**Findings (non-blocking):**
1. `backend/.env.example` also lists the DRF_SKILL §78 deployment names (`DOMAIN`, `FRONTEND_PORT`, `BACKEND_PATH`, …) under "NOT read by Django" — fine; TASK-013's `shared.env.template` does not need them.

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

### Review — 2026-09-28 — team-lead — final

**Verdict:** APPROVED — TL final sign-off.
- QA evidence exists: QA verdict PASS ticked, report `.ai/reports/qa/FEAT-001-qa-report.md` with server run ids.
- No unreviewed changes after the TL code review: backend/ (reviewed at 0a5f845; unchanged through HEAD 81e197a).
- Contracts/OpenAPI/docs: as recorded in the code review (api-contracts and ADRs updated in the same session; OpenAPI validated by `spectacular --validate` in the server suite and by QA TC-001-DOC-01..08 where applicable).
- Open bugs against this task: none (BUG-001 is TASK-004, BUG-002 is TASK-013; both Low).

## QA Log
- 2026-09-28 | qa | PASS | .ai/reports/qa/FEAT-001-qa-report.md; server runs 20260927-225552-109762 (API regression), 20260927-225436-108557 (ratelimit), backend audit 20260927-225853-111545

## Sign-off
- TL final review: ☑ (team-lead, 2026-09-28)
- QA verdict: ☑ PASS (.ai/reports/qa/FEAT-001-qa-report.md; server runs 20260927-225552-109762 (API regression), 20260927-225436-108557 (ratelimit), backend audit 20260927-225853-111545)
- PM acceptance: ☑ (project-manager, 2026-09-28; FEAT-001 accepted, .ai/reports/pm/sprint-01-acceptance-2026-09-28.md)
