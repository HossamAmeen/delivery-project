# TASK-012 — validation evidence (2026-09-27)

Target: `hossam@34.123.215.195` (real server; the only environment). All times are UTC.
Probes and results were kept in the agent scratchpad. Nothing was written into `backend/` or `qa/`.

## 1. Static checks (local)
```
$ for f in deploy/scripts/*.sh deploy/scripts/lib/*.sh; do bash -n "$f"; done      → all OK
$ shellcheck -x -P deploy/scripts deploy/scripts/*.sh deploy/scripts/lib/*.sh       → clean (ShellCheck 0.11.0)
```
ShellCheck ran from a scratch venv (`pip install shellcheck-py`). Nothing was installed system-wide. The
inline `# shellcheck disable=` directives are intentional and justified in comments: SC2029 (client-side ssh
expansion), SC2034 (dynamic scope), SC2016 (perl code), SC2119, SC2153 (.env variables).

## 2. Mode and config validation
```
DEPLOYMENT_MODE=docker     → "docker mode is deferred (ADR-015)"                    exit 2 (setup-server, remote-test)
DEPLOYMENT_MODE=           → "DEPLOYMENT_MODE is not set (expected: systemd)"        exit 2
DEPLOYMENT_MODE=kubernetes → "… is invalid (expected: systemd; docker is deferred)"  exit 2
ENV_FILE=/nonexistent      → "env file not found … (copy .env.example …)"            exit 2
.env without SERVER_HOST   → "missing required variable(s) …: SERVER_HOST"          exit 2
backend --worktree -- -n 2 → "parallel pytest (-n) is not allowed …"                exit 2
backend --ref nosuchref    → "git ref 'nosuchref' not found"                         exit 2
make test-backend-remote   → "commit 8b5dc1729561 has no backend/ directory (use --worktree …)"  (backend not committed yet)
```

## 3. Dry-runs
- `make setup-server DRY_RUN=1` (before bootstrap): dental preflight OK (port 8010 free), snapshot 31→33 entries,
  `would-create` × 11 dirs, `would-install uv 0.12.19 (current: none)`, `would-install python 3.13`, dental IDENTICAL, exit 0.
- `make test-backend-remote WORKTREE=1 DRY_RUN=1`: prints ship/lock/venv/env/steps/results plan, exit 0, no SSH write.
- `make qa-remote DRY_RUN=1 ARGS=-v`: prints ship/lock/venv/env (token shown as `<from shared/.env, server-side only>`)/results plan, exit 0.
- `make throttle-reset DRY_RUN=1`: `would remove 3 file(s) from /srv/flash/shared/cache`, exit 0.

## 4. Bootstrap (real) + idempotency
First run (15:47:21Z, 6.6 s): 11 × `created … (hossam:hossam:755|750)`, `installed uv 0.12.19`,
`Installed Python 3.13.15`, versions:
```
uv:      uv 0.12.19 (x86_64-unknown-linux-gnu)
python:  /home/hossam/.local/share/uv/python/cpython-3.13-linux-x86_64-gnu/bin/python3.13 Python 3.13.15
disk:    12G 36% free/used on /srv
dental guard: before/after IDENTICAL (33 entries)
```
Re-run (15:48:23Z): 11 × `ok`, `ok uv 0.12.19`, `ok python 3.13.15`, dental IDENTICAL, exit 0 → **idempotent**.

Side effects of the TL-prescribed uv installer outside the listed paths (all inside `~hossam`): `~/.local/bin/uvx`
and `~/.config/uv/uv-receipt.json`. `uv python install` also created a `~/.local/bin/python3.13` symlink. I
removed it, and the script now passes `--no-bin`. `.bashrc`/`.profile` are unchanged (`INSTALLER_NO_MODIFY_PATH=1`).

## 5. Backend runner (`make test-backend-remote`) with throw-away probes
Probe = minimal Django 5.2 project in the scratchpad (`BACKEND_SRC_DIR`), with requirements `Django, django-environ,
pytest, pytest-django, pytest-cov, ruff`. Its tests assert Python 3.13, the explicit test env (`DATABASE_URL`
under `/sandbox/test.sqlite3`, `RATELIMIT_CACHE_URL=locmem://`, `CELERY_ENABLED=False`, no `DEPLOY_PATH`
leaking in) and that the local `.env` is **not** shipped.

| Run | Result |
|---|---|
| pass probe `20260927-154935-1452162` | venv up to date (hash reuse); ruff-check/format, check, makemigrations, pytest PASS; 3 passed, coverage 100 %; **exit 0** |
| fail probe `20260927-154953-1452520` | ruff-check FAIL, pytest `1 failed, 2 passed`; **exit 1** |
| usage-error probe (`STEPS=pytest ARGS=tests/does_not_exist.py`) | pytest FAIL (exit 4); **script exit 4** (make exit 2) |
| two concurrent runs | 2nd printed `another run holds /srv/flash/sandbox/.lock — waiting`; both exit 0 |
| first run ever | `venv … (re)building on Python 3.13 (requirements hash dbd89f9ebbe2)` |

Results were copied back (`junit.xml`, `coverage.xml`, `output.log`, `summary.txt`, `latest` symlink).

**Compatibility run on the real in-progress `backend/`** (`--worktree`, results kept in the scratchpad), run
`20260927-155037-1453514`: shipped 42 files, rebuilt the venv (new hash f62a168a3137), `settings:
config.settings.test (from option)`, check PASS, makemigrations PASS, ruff-check/format FAIL, pytest
`2 failed, 27 passed`, coverage 39.78 % → exit 1. These are in-progress Backend issues, not runner issues (see
the Completion Report notes).

## 6. QA runner (`make qa-remote`)
Secret plumbing probe (scratch suite). For the test only, a fake `shared/.env` (`HEALTH_CHECK_PASSWORD="fake-token-…"`,
`SECRET_KEY=fake-…`) and a fake `qa/credentials.env` were created (0600) and **removed right after**:
- `QA_HEALTH_TOKEN: set (from shared/.env)`, `QA credentials: 2 variable(s)`; the env-contract test PASSED
  (`QA_BASE_URL`, `QA_WEB_URL`, token, credentials present; `SECRET_KEY`, `DEPLOY_PATH` absent).
- The leak test printed the secrets on purpose. The stream showed `token=*** password=***` and
  `assert '***' == 'leak ***'`. The first iteration leaked a truncated prefix (`'fake-toke...'`), so the filter
  was hardened to mask prefixes followed by `...`/`…`. After the fix, `grep -c "fake-tok|fake-pas|fake-sec"`
  finds **0** in the streamed log, `output.log`, `junit.xml` and `summary.txt`. Exit 1 propagated.

Real `qa/` harness (TASK-008, read-only for me): `make qa-remote ARGS="--collect-only -q"`, run
`20260927-155239-1455361`: venv built (playwright + pytest-playwright + httpx on 3.13.15), `106/111 tests
collected (5 deselected)`, **exit 0**. The token and credentials are reported as not set (expected before TASK-013/014).

## 7. throttle-reset
With 3 dummy files seeded in `shared/cache` (one in a subdir): DRY_RUN → `would remove 3`; real → `removed 3 file(s)`;
again → `removed 0`; the directory is left empty and intact.

## 8. Hygiene
- After all runs: `pgrep -u hossam -af /srv/flash` → no Flash processes left.
- Disk: sandbox 121 MB, qa 150 MB, uv pythons 111 MB, uv cache 24 MB. RAM available 3188 MB.
- Secret literal grep over `deploy/`, `Makefile`, `.env.example` → only code references, no literals.
- `/srv/flash/shared/.env` and `/srv/flash/qa/credentials.env` do **not** exist (the fake ones were removed).

## 9. Dental non-interference
- Every `setup-server` run: before/after IDENTICAL (33 entries).
- **Task-level** snapshot taken before any change (15:47:16Z) and after all validation (15:53:16Z):
  `dental guard: before/after IDENTICAL (33 entries)` — nginx tree hashes, LE files, dental unit
  (active, MainPID 18284, NRestarts 0, start 2026-09-26 22:52:01), port 8000 listener, `https://dental…` 200,
  `https://api.dental…` 302.
- `/srv/dental-clinic` was never read or listed (only `ls -ld` during the audit).
