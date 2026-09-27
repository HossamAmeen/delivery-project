# Task

## ID
TASK-005

## Title
Cache configuration & optional Celery

## Feature
FEAT-001 — Backend Platform Foundation

## Description
Configure the cache used for throttling from `RATELIMIT_CACHE_URL` (LocMem locally/tests, **FileBasedCache on the server**, Redis supported for later) and optional Celery (disabled on the server) per DRF_SKILL.md §28–33, §70–71, §79 as adapted by ADR-017; configure the trusted-proxy settings (ADR-015).

## Business Requirement
REQ-002, REQ-006, REQ-008; DRF_SKILL.md §28–33, §70–71, §74, §79; ADR-015, ADR-017; FEAT-001 criteria 5, 10

## Agent
Backend

## Scope (allowed paths)
- `backend/config/celery.py`, `backend/config/__init__.py`, Cache + Celery sections of settings

## Dependencies
- TASK-002 (sequencing: shares `base.py`; backend order TASK-001 → 002 → 005 → 004 → 003)
- TASK-012 for server validation

## Acceptance Criteria

- [ ] `CACHES["default"] = env.cache_url("RATELIMIT_CACHE_URL", default="locmem://")`; supports `locmem://`, `filecache:///abs/path` (with `OPTIONS.MAX_ENTRIES=10000`) and `redis://`. Production settings raise `ImproperlyConfigured` when the URL is `locmem://` or missing (multi-worker, ADR-017).
- [ ] With `CELERY_ENABLED=False` and no Redis running: Django starts, `check` passes, tests pass. This is the server configuration.
- [ ] With `CELERY_ENABLED=True`: Celery app configured from `CELERY_*` settings and autodiscovers tasks (import only; nothing runs on the server).
- [ ] Trusted proxy: `SECURE_PROXY_SSL_HEADER` and DRF `NUM_PROXIES` from env, documented in `backend/.env.example` with the server values (`HTTP_X_FORWARDED_PROTO,https`, `1`). (If TASK-001/002 already placed them, just verify and test.)
- [ ] All Celery/cache/proxy variables in `backend/.env.example`.
- [ ] Tests pass on the server with `make test-backend-remote`.

## Technical Notes

- Celery import must not fail if the `celery` package is installed but broker unreachable; `celery` may be omitted from production requirements if the import is guarded.
- Keep Redis DB separation for later: 0 broker, 1 results, 2 throttle cache.
- nginx overwrites `X-Forwarded-For` with `$remote_addr` (one trusted hop), so `NUM_PROXIES=1` is correct on the server (ADR-015). Locally/tests: unset.
- The FileBasedCache directory (`/srv/flash/shared/cache`) is created by Infrastructure; the app must not create directories outside its config.

## Testing Requirements

- Settings tests for both Celery toggle states and for `locmem://`, `filecache://` (tmp dir) and the production refusal of LocMem.
- A trivial eager-mode task test proving the Celery wiring (can live in `backend/tests/`), skipped cleanly if Celery is not installed.
- A throttle test with FileBasedCache in a tmp dir proving two separate cache instances (simulating two workers) share counters.

## Plan Review Required
No

## Status

QA_IN_PROGRESS

## Activity Log
- 2026-09-27 | team-lead | — → TODO | created from sprint-01 technical plan
- 2026-09-27 | team-lead | TODO → TODO | re-scoped per ADR-017 (FileBasedCache via RATELIMIT_CACHE_URL, no Redis, Celery disabled) and ADR-015 (proxy settings); depends on TASK-002 for sequencing
- 2026-09-27 | backend | TODO → IN_PROGRESS | started after TASK-002 code complete (shared base.py)
- 2026-09-27 | backend | IN_PROGRESS → READY_FOR_REVIEW | implementation + tests done; full server run `make test-backend-remote WORKTREE=1` green (run 20260927-175239-1501198: ruff, format, check, makemigrations, 238 passed, coverage 98.42%)
- 2026-09-27 | team-lead | READY_FOR_REVIEW → REVIEW | code inspection done, decisions recorded; verdict pending the TL's own server validation run (denied by the session permission policy)
- 2026-09-27 | team-lead | REVIEW → READY_FOR_QA | code review APPROVED; TL server run 20260927-204315-12107 at 0a5f845: ruff/format/check/makemigrations PASS, 238 passed, coverage 98.42%
- 2026-09-28 | qa | READY_FOR_QA → QA_IN_PROGRESS | FEAT-001 verification on the server started (TASK-009)

## Implementation Plan
(not required)

## Completion Report
- Files changed: `backend/config/celery.py`, `backend/config/__init__.py` (import guarded: only a missing `celery` package is tolerated), Cache + Celery sections of `config/settings/base.py`, production cache in `config/settings/production.py`, `build_cache` / `celery_runtime` / `FlashEnv` in `config/settings/_helpers.py`, `requirements/celery.txt`, `backend/.env.example` (cache/Celery/proxy variables with server values), `tests/test_cache_celery.py`.
- Tests added: `tests/test_cache_celery.py` (26): `locmem://`/`locmemcache://`/empty → LocMem; `filecache:///abs` → FileBasedCache with `MAX_ENTRIES=10000`; relative filecache refused; `redis://` supported; production refuses LocMem and a missing URL (helper and full settings); production settings use the server filecache and `NUM_PROXIES=1`; `NUM_PROXIES` unset locally, invalid value refused; **two FileBasedCache instances on one tmp dir share throttle counters** (two gunicorn workers); both Celery toggle states (helper + full settings, Beat only when Celery is on); test settings have no Redis anywhere; eager task through the real Celery app (skipped cleanly without Celery); `config` imports with `celery` missing (subprocess).
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
- Contract/OpenAPI changes: none.
- Notes for TL / Infrastructure:
  - django-environ does not know `locmem://` (its scheme is `locmemcache://`); `FlashEnv` adds `locmem://` so the ADR-017/ADR-018 value works unchanged. Both spellings are accepted.
  - With `CELERY_ENABLED=False` the effective settings are `CELERY_BROKER_URL=memory://`, `CELERY_RESULT_BACKEND=None`, `CELERY_TASK_ALWAYS_EAGER=True`: `task.delay()` runs inline and nothing ever connects to Redis. With `True`, the env values are used unchanged. `CELERY_BEAT_ENABLED` is forced False when Celery is off.
  - Trusted proxy: `SECURE_PROXY_SSL_HEADER` (TASK-001) and `NUM_PROXIES` (TASK-002) verified here with the server values (`HTTP_X_FORWARDED_PROTO,https`, `1`).
  - The app never creates the cache directory; Infrastructure creates `/srv/flash/shared/cache`.
- Known limitations / remaining problems: FileBasedCache throttle counters are approximate under concurrent requests (read-modify-write, accepted in ADR-017).

## Review Log
### Review — 2026-09-27 — team-lead — code (in progress)

**Verdict:** PENDING — not issued yet. Code inspection and the decisions below are done; the TL's own validation run (`make test-backend-remote WORKTREE=1`, which executes the DRF_SKILL §57 commands on the server: `ruff check`, `ruff format --check`, `manage.py check`, `makemigrations --check --dry-run`, `pytest --cov`) was **denied by the session's permission policy** (classified as interfering with the shared server). Per team-lead.md §6 ("do not approve work without running the validation yourself") the verdict waits for that run; Backend's run `20260927-175239-1501198` (238 passed, 98.42 %) is noted but is not the TL's evidence. No blocking defect was found in the inspection.

**Checked so far (inspection):** `build_cache` (`FlashEnv` adds `locmem://`; filecache absolute path + `MAX_ENTRIES=10000`; production refuses LocMem and a missing URL), `celery_runtime` (disabled → `memory://`, eager, no Redis), guarded Celery import, `NUM_PROXIES` parsing.

**Decisions on Backend's points:**
- **`locmem://` helper — ACCEPTED**; ADR-017/018 wording corrected to describe the helper (`locmem://` and `locmemcache://` both accepted; production refuses either).
- **`NUM_PROXIES=1` on the server — CONFIRMED** (ADR-015 already lists it; valid because nginx overwrites `X-Forwarded-For` with `$remote_addr`). TASK-013's `shared.env.template` AC now states it explicitly.

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
