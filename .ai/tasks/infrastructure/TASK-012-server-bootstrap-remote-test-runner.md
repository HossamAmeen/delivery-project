# Task

## ID
TASK-012

## Title
Server audit & bootstrap (uv + Python 3.13, /srv/flash layout) and the on-server test runners

## Feature
FEAT-004 — Deployment & Environments (enables FEAT-001 AC9 and REQ-009 for every other task)

## Description
First Infrastructure deliverable of the sprint, small and **first in the queue** because every backend task validates on the server (ADR-016, ADR-018).
1. Read-only audit of the shared server, written up.
2. Bootstrap the Flash footprint: `/srv/flash` layout, `uv` for user `hossam`, Python 3.13.
3. Deliver `make test-backend-remote`, `make qa-remote` and `make throttle-reset`, plus the shared script library (env loading, validation, logging, redaction, `--dry-run`, dental guard) that TASK-013 builds on.

No nginx, systemd, certbot or application deploy in this task.

## Business Requirement
REQ-008, REQ-009; BLK-011 (RESOLVED); ADR-012, ADR-015, ADR-016, ADR-018; FEAT-004 criteria 1, 4 (Python 3.13 part), 9, 10, 11, 13

## Agent
Infrastructure

## Scope (allowed paths)
- `deploy/scripts/lib/common.sh`, `deploy/scripts/lib/dental_guard.sh`, `deploy/scripts/setup-server.sh` (bootstrap phase), `deploy/scripts/remote-test.sh`
- root `Makefile` (targets: `help`, `setup-server`, `test-backend-remote`, `qa-remote`, `throttle-reset`)
- root `.env.example` (deployment variables, list below)
- root `.gitignore`: **append only** `backend/.remote-results/`, `qa/.results/`, `.env` if missing (TL-coordinated exception, recorded here)
- `deploy/README.md` (sections: Overview, Server requirements, SSH setup, Environment variables, Co-hosting rules, Remote testing)
- `.ai/reports/infrastructure/**`
- **Server (via SSH as `hossam`):** `/srv/flash/**`, `~hossam/.local/bin/uv`, `~hossam/.local/share/uv/**`, `~hossam/.cache/uv/**`. Nothing else.

## Dependencies
- none — start immediately, in parallel with TASK-001 coding
- Backend tasks need this task **delivered** (READY_FOR_REVIEW is enough for them to use the runner; the TL reviews it promptly)

## Acceptance Criteria
- [ ] `.ai/reports/infrastructure/server-audit-2026-09-27.md`: OS, CPU/RAM/swap, disk per mount, listening ports (`ss -ltnp` as allowed), nginx version and the list of enabled sites + their `server_name`s (read-only: `sudo nginx -T` output **summarized**, not pasted with any secrets), existing certbot certificates (`sudo certbot certificates`: names + domains only), `certbot.timer` status, python/node/npm/rsync/envsubst/curl versions, the dental footprint as observed. Confirms port 8010 is free and names any deviation from BLK-011.
- [ ] `lib/common.sh`: `set -euo pipefail`; loads root `.env` (or `ENV_FILE`), validates required variables with clear errors, validates `DEPLOYMENT_MODE` (`systemd` OK; `docker` → exit 2 "docker mode is deferred (ADR-015)"; missing/other → exit 2); `run`/`remote` wrappers that honour `--dry-run` (print the step, execute nothing that changes state) and redact values of variables whose names match `*PASSWORD*|*SECRET*|*TOKEN*|*KEY*` (the SSH key **path** may be shown); `ssh` uses `-i "$SSH_KEY_PATH" -p "$SERVER_PORT" -o BatchMode=yes`; logging with UTC timestamps; never `set -x`.
- [ ] `lib/dental_guard.sh`: `dental_snapshot <file>` and `dental_compare <before> <after>` implementing ADR-015 (sha256 of every non-Flash file under `/etc/nginx/{nginx.conf,conf.d,sites-available,sites-enabled}`, `systemctl is-active $DENTAL_GUARD_SERVICE`, HTTP status of each `DENTAL_GUARD_DOMAINS` over https), plus static preflight assertions (port ≠ `DENTAL_GUARD_PORT` and free or held by the Flash service, `DEPLOY_PATH` not under `DENTAL_GUARD_PATH`, service name starts with `flash-`, domains don't contain `dental`). Read-only against dental. All values from `.env`.
- [ ] `setup-server.sh` (bootstrap phase, idempotent, `--dry-run`): dental snapshot → `sudo install -d -o $SERVER_USER -g $SERVER_USER` for `${DEPLOY_PATH}` and `{releases,shared/{db,cache,static,media,logs,backups},sandbox,qa}` (`shared` 0750) → install uv `${UV_VERSION}` for the user if missing/different → `uv python install ${PYTHON_VERSION}` → print versions → dental compare. Re-running changes nothing.
- [ ] `remote-test.sh backend [--ref <git-ref> | --worktree]` and `remote-test.sh qa [pytest args]`, exactly as ADR-018 specifies (sandbox/QA venvs, explicit test env, `shared/.env` never read for backend tests, health token exported only into the QA pytest process via the remote shell without echo, results copied back to `backend/.remote-results/` / `qa/.results/`, exit code = test exit code). Venvs are re-synced only when the requirements file hash changes.
- [ ] `make throttle-reset`: empties `${DEPLOY_PATH}/shared/cache/` only (prints the count of removed files).
- [ ] Root `.env.example`: `APP_NAME=flash`, `DEPLOYMENT_MODE=systemd`, `SERVER_HOST=34.123.215.195`, `SERVER_USER=hossam`, `SERVER_PORT=22`, `SSH_KEY_PATH=~/.ssh/id_ed25519`, `DEPLOY_PATH=/srv/flash`, `API_DOMAIN=api.delivery.hossam-ameen.online`, `WEB_DOMAIN=delivery.hossam-ameen.online`, `BACKEND_PORT=8010`, `BACKEND_SYSTEMD_SERVICE=flash-backend`, `GUNICORN_WORKERS=2`, `GUNICORN_THREADS=2`, `GUNICORN_TIMEOUT=30`, `BACKEND_MEMORY_MAX=700M`, `PYTHON_VERSION=3.13`, `UV_VERSION=<pinned>`, `RELEASES_TO_KEEP=5`, `DB_BACKUPS_TO_KEEP=5`, `MIN_FREE_DISK_MB=1500`, `HEALTH_CHECK_TIMEOUT=60`, `AUTO_DEPLOY=false`, `AUTO_ROLLBACK=true`, `ROLLBACK_RESTORE_DB=auto`, `CERT_NAME=flash-delivery`, `LETSENCRYPT_EMAIL=` (operator fills), `VITE_API_BASE_URL=https://api.delivery.hossam-ameen.online`, `DENTAL_GUARD_DOMAINS=dental.hossam-ameen.online,api.dental.hossam-ameen.online`, `DENTAL_GUARD_SERVICE=dental-clinic-backend`, `DENTAL_GUARD_PORT=8000`, `DENTAL_GUARD_PATH=/srv/dental-clinic`. **No application secrets** (ADR-015). The operator's real `.env` is git-ignored.
- [ ] Validation: `bash -n` + `shellcheck` clean on every script; every script's `--dry-run` output recorded; `make setup-server` executed on the server and re-run to prove idempotency; `uv` and `python3.13` versions shown; dental guard before/after identical; `make test-backend-remote` exercised against a throw-away probe (e.g. `--worktree` with the current `backend/` if TASK-001 has started, otherwise a scratch `backend/` stub in the scratchpad passed via an env override — do not create files in `backend/`) proving the sandbox venv builds on 3.13 and exit codes propagate.
- [ ] Completion Report + `deploy/README.md` sections updated.

## Technical Notes — pre-approved constraints (TL, 2026-09-27)
- Everything runs as `hossam`. `sudo` is used **only** for `install -d` of `/srv/flash` and read-only audit commands (`nginx -T`, `certbot certificates`, `ss -p`). No apt, no system Python changes, no Docker, no nginx/systemd/certbot writes in this task.
- Never read, list recursively, or write `/srv/dental-clinic`. Never touch port 8000 or `dental-clinic-backend.service` (status query only).
- uv installer: `curl -LsSf https://astral.sh/uv/${UV_VERSION}/install.sh | env UV_INSTALL_DIR="$HOME/.local/bin" INSTALLER_NO_MODIFY_PATH=1 sh` (pinned version; scripts call `~/.local/bin/uv` by absolute path).
- Remote test runs must not leave processes behind and must not use more than one pytest worker (no `-n`).
- Keep functions reusable: TASK-013 will extend `setup-server.sh` and use `lib/*.sh` unchanged where possible.

## Testing Requirements
- shellcheck/`bash -n`, dry-runs, the real bootstrap run + idempotent re-run, the runner exit-code check (one passing and one failing probe). Commands and outputs in the Completion Report.

## Plan Review Required
Yes — production server (shared) and infrastructure architecture. **Pre-approved** by the TL on 2026-09-27 against the constraints above and ADR-015/016/018: write a short `## Implementation Plan` (≤ 20 lines: steps and files) and proceed without waiting. Anything outside the constraints (apt installs, sudo writes outside `/srv/flash`, a different Python provisioning) needs TL approval first. The TL reviews the implementation.

## Status

READY_FOR_RELEASE

## Activity Log
- 2026-09-27 | team-lead | — → TODO | created for FEAT-004 (ADR-015/016/018); first in the Infrastructure queue; plan pre-approved
- 2026-09-27 | infrastructure | TODO → IN_PROGRESS | started: plan written, server audit next
- 2026-09-27 | infrastructure | IN_PROGRESS → IN_PROGRESS | server audit done (.ai/reports/infrastructure/server-audit-2026-09-27.md); bootstrap executed on the server (uv 0.12.19, Python 3.13.15, /srv/flash), dental IDENTICAL
- 2026-09-27 | infrastructure | IN_PROGRESS → READY_FOR_REVIEW | runners validated on the server (pass/fail/exit-code/lock/redaction probes, real qa/ collect 106 tests); evidence .ai/reports/infrastructure/TASK-012-validation-2026-09-27.md
- 2026-09-27 | team-lead | READY_FOR_REVIEW → REVIEW | code review started
- 2026-09-27 | team-lead | REVIEW → READY_FOR_QA | code review APPROVED (Review Log); ADR-015/016/017/018 amended; TASK-013/014 amended; QA verification via TASK-015
- 2026-09-27 | team-lead | READY_FOR_QA → IN_PROGRESS | defect found in TL use: `remote-test.sh backend --ref` exits 1 after a green run (`tmp: unbound variable` in the EXIT trap); see Review Log
- 2026-09-27 | infrastructure | IN_PROGRESS → READY_FOR_REVIEW | EXIT-trap fix in `remote-test.sh` (global `REMOTE_TEST_TMP`, `${REMOTE_TEST_TMP:-}`); `make test-backend-remote REF=0a5f845` exit 0, no /tmp leftover; failing probes exit 1 / 4 (Completion Report § Fix)
- 2026-09-27 | team-lead | READY_FOR_REVIEW → REVIEW | re-review of the EXIT-trap fix
- 2026-09-27 | team-lead | REVIEW → READY_FOR_QA | re-review APPROVED: `make test-backend-remote REF=0a5f845` exits 0, no /tmp leftovers, failing probe propagates; QA via TASK-015
- 2026-09-28 | qa | READY_FOR_QA → QA_IN_PROGRESS | FEAT-004 verification on the server started (TASK-015)
- 2026-09-28 | qa | QA_IN_PROGRESS → QA_IN_PROGRESS | QA verdict PASS ticked; status left for TL final review (.ai/reports/qa/FEAT-004-qa-report.md; runners used in 15 qa-remote runs + backend audit 20260927-225853-111545)
- 2026-09-28 | team-lead | QA_IN_PROGRESS → READY_FOR_RELEASE | TL final review signed off (QA PASS in .ai/reports/qa/FEAT-004-qa-report.md; no unreviewed changes)

## Implementation Plan
1. Read-only server audit (ssh as hossam; sudo only for `nginx -T`, `certbot certificates`, `ss -ltnp`) → `.ai/reports/infrastructure/server-audit-2026-09-27.md`.
2. `deploy/scripts/lib/common.sh`: strict mode, `.env`/`ENV_FILE` loading (tilde expansion for `SSH_KEY_PATH`), `require_vars`, `validate_mode` (systemd ok / docker → exit 2 / other → exit 2), UTC logging, `--dry-run` parsing, `run`/`remote`/`remote_script` wrappers with redaction, `ssh_opts` (`-i`, `-p`, `BatchMode=yes`), rsync-over-ssh helper.
3. `deploy/scripts/lib/dental_guard.sh`: `dental_preflight` (static assertions + remote port check), `dental_snapshot <file>` (remote read-only: sha256 of non-Flash nginx files, `systemctl is-active`, https status codes), `dental_compare <before> <after>`.
4. `deploy/scripts/setup-server.sh` (bootstrap phase, idempotent): snapshot → `sudo install -d` layout → uv `${UV_VERSION}` (install only if missing/different) → `uv python install ${PYTHON_VERSION}` → versions → compare.
5. `deploy/scripts/remote-test.sh`: `backend [--ref|--worktree]`, `qa [args]`, `throttle-reset`; source dir overridable (`BACKEND_SRC_DIR`/`QA_SRC_DIR`) for probes; requirements-hash venv re-sync; explicit test env; token exported only into pytest from `shared/.env`; results rsynced back; exit code propagated.
6. Root `Makefile` (help, setup-server, test-backend-remote, qa-remote, throttle-reset; `DRY_RUN=1`), root `.env.example`, `.gitignore` append, `deploy/README.md` sections.
7. Validate: `bash -n`, shellcheck (scratchpad venv via `shellcheck-py`, nothing system-wide), dry-runs (systemd/docker/missing), real bootstrap + re-run, dental before/after, probe pass/fail runs from a scratchpad `backend/` stub.

## Completion Report
- **Files changed:**
  - new: `deploy/scripts/lib/common.sh`, `deploy/scripts/lib/dental_guard.sh`, `deploy/scripts/setup-server.sh` (bootstrap phase), `deploy/scripts/remote-test.sh` (`backend` | `qa` | `throttle-reset`), `deploy/README.md` (Overview, Server requirements, SSH setup, Environment variables, Co-hosting rules, Server bootstrap, Remote testing), root `Makefile` (`help`, `setup-server`, `test-backend-remote`, `qa-remote`, `throttle-reset`; `DRY_RUN=1`), root `.env.example` (every variable in the AC; `UV_VERSION=0.12.19`; `LETSENCRYPT_EMAIL` optional because the existing LE production account is reused)
  - `.gitignore`: appended `backend/.remote-results/`, `qa/.results/` (`.env` was already there). TL-coordinated exception.
  - reports: `.ai/reports/infrastructure/server-audit-2026-09-27.md`, `.ai/reports/infrastructure/TASK-012-validation-2026-09-27.md`
  - local root `.env` created as a copy of `.env.example` (git-ignored, no secrets) so the make targets work for every agent now
  - server: `/srv/flash/{releases,shared/{db,cache,static,media,logs,backups},sandbox,qa}` (hossam, `shared` 0750), `~/.local/bin/uv` (+ `uvx`), `~/.local/share/uv/python/cpython-3.13.15`, `~/.cache/uv`, `~/.config/uv/uv-receipt.json` (installer receipt), sandbox and QA venvs
- **Tests added:** none in the repo (infra). Throw-away probes (pass, fail, usage error, concurrency, secret leak) lived in the scratchpad only.
- **Validation commands run + results** (full output in the validation report):
  - `bash -n` on all 4 scripts OK. `shellcheck -x` (0.11.0, scratch venv) clean.
  - Mode: `docker` / empty / invalid → exit 2 with the ADR-015 message. Missing `.env` or variable → exit 2. `-n` refused → exit 2.
  - Dry-runs of `setup-server`, `test-backend-remote`, `qa-remote`, `throttle-reset` recorded. Nothing was changed.
  - `make setup-server` run for real: 11 dirs created, uv 0.12.19, Python 3.13.15. The re-run printed only `ok` lines (idempotent). Dental before/after IDENTICAL (33 entries) both times.
  - `make test-backend-remote WORKTREE=1` against scratch probes: pass → exit 0 (5 steps PASS, coverage 100 %); fail → exit 1; pytest usage error → exit 4 (make: 2); concurrent runs serialized by the server lock; venv rebuilt only on a requirements hash change; the local `.env` is not shipped; explicit test env verified by assertions.
  - Real in-progress `backend/` run through the runner: works (settings via `--ds config.settings.test`). The backend itself currently fails ruff, 2 tests, and coverage (40 %). Those failures belong to Backend's work in progress.
  - `make qa-remote`: secret plumbing probe (fake token and credentials, removed afterwards). Token and `QA_*` credentials were exported only into pytest, and 0 leaks (prefixes included) in the stream, log and junit. Real `qa/` `--collect-only -q` → 106/111 collected, exit 0.
  - `make throttle-reset`: dry-run `would remove 3` → `removed 3` → `removed 0`.
  - No leftover processes. Task-level dental snapshot before (15:47:16Z) vs after (15:53:16Z) is IDENTICAL.
- **Contract/OpenAPI changes:** none.
- **Deviations / decisions for TL review:**
  1. The dental guard hashes **all of `/etc/nginx/`** (minus the 2 Flash site files), plus the LE shared files, the renewal confs, and the dental unit's PID, start time and unit hash. This is a superset of ADR-015, because dental's includes live in `/etc/nginx/dental-clinic/` (audit deviation 1).
  2. Sources are shipped as a **tar stream over SSH into the server lock** (not rsync), so replacing `sandbox/backend` or `qa/suite` and running the tests is atomic under `flock`. The paths are the ADR-018 ones. Results are copied back with rsync.
  3. The runner keeps every step running and reports each one. Its exit code is pytest's if pytest failed, else the first failing step's. `make` reports any failure as 2; call the script for the exact code.
  4. Results are kept per run: `backend/.remote-results/<run-id>/` and `qa/.results/<run-id>/` plus a `latest` symlink, 10 runs kept.
  5. QA also receives `QA_RESULTS_DIR`, `QA_DENTAL_DOMAINS` and `PLAYWRIGHT_BROWSERS_PATH=/srv/flash/qa/browsers`, which TASK-013 `--with-e2e` should install into.
  6. `uv python install --no-bin` keeps `~/.local/bin` to uv/uvx only.
- **Known limitations / remaining problems:**
  - **`shared` is 0750 (per AC), so nginx (`www-data`) cannot traverse to `shared/static` and `shared/media`.** The ADR-015 `/static/` and `/media/` aliases in TASK-013 will return 403 unless the TL chooses a fix: `shared` 0751 with `db`/`backups` 0700, or group `www-data` on `shared/{static,media}`. TL decision is needed before TASK-013/014.
  - **ADR-017/018 name `locmem://`, which django-environ does not accept** (its scheme is `locmemcache://`). The backend already works around it with its own helper (`config/settings/_helpers.py`), and the runner keeps the ADR value. The TL may want to correct the ADR wording.
  - **`LETSENCRYPT_EMAIL` is optional** (the existing production ACME account is reused), but the TASK-013 AC says `tls.sh` "fails early if LETSENCRYPT_EMAIL is empty". The TL should amend TASK-013 to "omit `-m` and reuse the registered account when it is empty".
  - The uv installer wrote `~/.local/bin/uvx` and `~/.config/uv/uv-receipt.json`, just outside the listed server paths. Both are inherent to the prescribed installer and harmless.
  - `shared/.env`, `qa/credentials.env` and the Playwright browsers don't exist yet (TASK-013/014). `qa-remote` reports this and runs anyway.
  - Hint for Backend (not an infra issue): `test_logging_writes_to_stream_handlers_only` fails on the server because pytest's logging plugin attaches its own `_FileHandler` (to `os.devnull`) to the root logger during the run.

### Fix — 2026-09-27 — reopen (TL finding 1, `tmp: unbound variable`)
- **Change** (`deploy/scripts/remote-test.sh`, `cmd_backend`): the `git archive` copy now lives in the **global** `REMOTE_TEST_TMP` (`mktemp -d ${TMPDIR:-/tmp}/flash-remote-test-XXXXXX`), and the EXIT trap is `rm -rf -- "${REMOTE_TEST_TMP:-}"`, which is safe under `set -u` after the function returns. `--worktree` mode is unchanged.
- **Evidence:**
  - `bash -n` on all 22 files + `shellcheck -x` (0.11.0) → clean.
  - `/tmp` before: 0 `tmp.*` / `flash-remote-test-*` dirs.
  - `make test-backend-remote REF=0a5f845` (run `20260927-204656-15284`): ruff-check, ruff-format, check, makemigrations, pytest all PASS (238 passed, coverage 98.42 %), remote `== exit code: 0`, **make exit 0**, no `unbound variable`. `/tmp` after: 0 leftovers.
  - Failing probes in REF mode (script called directly for the exact code): `--steps pytest -- --cov-fail-under=100` → `FAIL Required test coverage of 100% not reached. Total coverage: 98.42%` → **exit 1**; `--steps pytest -- tests/does_not_exist.py` → **exit 4**. 0 leftovers afterwards.


## Review Log
- 2026-09-27 | team-lead | PLAN PRE-APPROVED (conditional) | valid within the Technical Notes constraints and ADR-015/016/018

### Review — 2026-09-27 — team-lead — code

**Verdict:** APPROVED

**Checked:**
- [x] Scope limited to the task (4 scripts, root `Makefile`, root `.env.example`, `.gitignore` append, `deploy/README.md`, 2 reports; server: `/srv/flash/**` + uv user dirs — see decision 4)
- [x] Business rules — n/a
- [x] Authorization — n/a (sudo only for `install -d` and read-only checks, as constrained)
- [x] State transitions / money / migrations — n/a
- [x] API contract — n/a (runner consumes the Foundation health contract only via QA env)
- [x] Tests: shellcheck/`bash -n`, mode/config negatives, dry-runs, real bootstrap + idempotent re-run, pass/fail/exit-code/lock/redaction probes (validation report); re-verified below
- [x] No hardcoded secrets, domains, ports, paths (all from `.env`; `.env.example` has no application secrets; test secrets are random and generated on the server; QA token/credentials read server-side, never in argv, redacted)
- [x] Complies with ADR-012/015/016/018 and the infra DoD, with the deviations accepted below
- [x] Infra: no secrets in scripts/templates, `DEPLOYMENT_MODE` validated (systemd ok, docker/other → exit 2), systemd mode validated live, docker mode deferred by ADR-015; rollback path n/a in this task

**Decisions on the Infrastructure agent's points:**
1. **`shared/` permissions — option A chosen: `shared` 0751 with private subdirs 0700.** `/srv/flash` 0755, `releases/` 0755, `shared/` 0751, `shared/{static,media}` 0755, `shared/{db,backups,cache}` 0700, `shared/logs` 0750, `shared/.env` 0600, `sandbox/` and `qa/` 0750, all `hossam:hossam`. Reason: `www-data` only needs to traverse `shared/` and read the two public trees; the group option would still need `shared` traversable by `www-data` plus setgid dirs. Verified today (read-only) that `www-data` currently **cannot** traverse `shared/` (0750) — the TASK-013 aliases would 403. Written into ADR-015 (§ Layout, "Permissions"), TASK-013 (new AC: `setup-server.sh` enforces the modes + `www-data` evidence) and TASK-014 (stat evidence + `/static/` 200-not-403 check). Implemented in TASK-013 (`_remote_layout` already fixes modes of existing dirs idempotently).
2. **`locmem://` wording — ADR-017/018 corrected:** `RATELIMIT_CACHE_URL` is parsed by the backend helper `build_cache` (`backend/config/settings/_helpers.py`, `FlashEnv` adds the `locmem` scheme); `locmem://` and django-environ's `locmemcache://` both work; production refuses either. The runner keeps `locmem://`.
3. **`LETSENCRYPT_EMAIL` optional — TASK-013 AC changed** to: omit `-m` and reuse the registered production ACME account when empty; fail early only if empty **and** `certbot show_account` finds no production account; never `--register-unsafely-without-email`. ADR-015 § TLS and TASK-014 dependencies amended. Verified read-only: `sudo certbot show_account` shows a production account.
4. **uv footprint — ACCEPTED.** `~/.local/bin/uvx` and `~/.config/uv/uv-receipt.json` come from the prescribed official installer; `uv python install --no-bin` keeps `~/.local/bin` to uv/uvx. Recorded in ADR-016 as the accepted user-level footprint.
5. **Deviations — all ACCEPTED and recorded:** (a) the dental guard hashes all of `/etc/nginx/` (minus the 2 Flash site files) plus LE shared files/renewal confs and the dental unit state — a strict superset, needed because dental's includes live in `/etc/nginx/dental-clinic/` (ADR-015 amended); (b) sources shipped as a tar stream unpacked under the server `flock` instead of rsync (atomic with respect to concurrent runs; same paths) (ADR-018 amended); (c) results kept per run with `latest`, 10 runs (ADR-018 amended). The "exit code = pytest's else first failing step's" rule is accepted too.
6. **`shared/.env`, `qa/credentials.env`, Playwright browsers** — confirmed as TASK-013 (`setup-server` full, `seed-qa-users`, `--with-e2e`) and TASK-014 (execution). `qa-remote` running without them (reporting it) is the right behaviour.

**Findings:**
1. [non-blocking] `setup-server.sh` / `remote-test.sh throttle-reset` call state-changing remote functions through `remote_fn ro` and rely on an `apply` flag for `--dry-run`. It works (dry-run verified), but the `ro` label is misleading. TASK-013 note added: new state-changing calls use `remote_fn rw`.
2. [non-blocking] `lib/dental_guard.sh` hashes all of `/etc/nginx/`: TASK-013's safe-apply backups and test configs must stay outside `/etc/nginx/` (note added to TASK-013), and a certbot update of `/etc/letsencrypt/options-ssl-nginx.conf` during `tls.sh` would trip the guard — stop and report if it does.
3. [non-blocking] `README.md` layout block shows `shared` 0750 / `sandbox`,`qa` 0755; TASK-013 updates it together with the new modes.

**Commands run** (local + read-only on the server; no QA suite, no backend suite run here):
```
bash -n deploy/scripts/{lib/common.sh,lib/dental_guard.sh,setup-server.sh,remote-test.sh}   → all OK
shellcheck -x (0.11.0, scratch venv) on the 4 scripts                                        → clean, EXIT 0
DEPLOYMENT_MODE=docker setup-server.sh --dry-run       → "docker mode is deferred (ADR-015)"  EXIT 2
DEPLOYMENT_MODE=foo remote-test.sh throttle-reset      → "…is invalid (expected: systemd…)"   EXIT 2
setup-server.sh --dry-run (live, read-only)            → preflight OK (8010 free); 11 dirs "ok"; uv 0.12.19 ok;
                                                         python 3.13.15 ok; dental before/after IDENTICAL (33 entries);
                                                         dental-clinic-backend active, dental 200 / api.dental 302   EXIT 0
make test-backend-remote DRY_RUN=1 WORKTREE=1          → plan printed (79 files, lock, venv, explicit env, steps)     EXIT 0
make qa-remote DRY_RUN=1                               → plan printed, no SSH write                                   EXIT 0
make throttle-reset DRY_RUN=1                          → would remove 0 file(s)                                        EXIT 0
.env == .env.example (no secrets)
server (read-only): nginx `user www-data`; stat of /srv/flash tree as reported; `sudo -u www-data test -x /srv/flash/shared`
  → CANNOT traverse (confirms point 1); ~/.local/bin = uv, uvx; ~/.config/uv/uv-receipt.json; port 8010 free;
  `sudo certbot show_account` → production account present
```
The real bootstrap, idempotent re-run and runner probes are accepted from the validation report (re-running them would only repeat state changes); QA re-verifies on the server in TASK-015.

### Review — 2026-09-27 — team-lead — code (re-opened)

**Verdict:** CHANGES_REQUESTED

**Findings:**
1. [blocking] `deploy/scripts/remote-test.sh:295,303` — `cmd_backend` declares `local ... tmp=""` and then sets `trap 'rm -rf "$tmp"' EXIT`. The EXIT trap runs after the function returned, when the `local` is out of scope, so under `set -u` it fails with `tmp: unbound variable`. Result: `make test-backend-remote REF=<ref>` **exits 1 even when every step passed** (breaks the ADR-018 rule "exit code = test exit code"; the TL runs `REF=` in every backend review), and the `mktemp -d` copy of `backend/` is **leaked in /tmp** (the TL removed the one from its own run). Required change: keep the path in a global (e.g. `REMOTE_TEST_TMP`) or clean it up explicitly before returning, and make the trap safe (`"${REMOTE_TEST_TMP:-}"`). Evidence: re-run `make test-backend-remote REF=<sha>` on a green commit → make exit 0 and no leftover `/tmp/tmp.*`; plus a failing probe → the pytest exit code propagates.

Reproduced: `make test-backend-remote REF=0a5f845` (run `20260927-204315-12107`): all 5 steps PASS, remote `exit code: 0`, then `deploy/scripts/remote-test.sh: line 1: tmp: unbound variable`, `make: *** [Makefile:69: test-backend-remote] Error 1`.

`--worktree` mode is not affected (no trap), so Backend/QA workflows keep working meanwhile. May be fixed within TASK-014's allowed `deploy/**` fixes if Infrastructure is already there; it then comes back through TL review with this task.

### Review — 2026-09-27 — team-lead — code (re-review of the fix)

**Verdict:** APPROVED

**Checked:** `deploy/scripts/remote-test.sh` `cmd_backend`: the archive dir is now a global `REMOTE_TEST_TMP` created as `${TMPDIR:-/tmp}/flash-remote-test-XXXXXX`, and the trap is `rm -rf -- "${REMOTE_TEST_TMP:-}"` (safe under `set -u`). The change is limited to those lines. The finding from the re-opened review is resolved.

**Commands run:**
```
bash -n on all deploy/scripts/*.sh and lib/*.sh          → OK
shellcheck -x (0.11.0) on all scripts                    → clean, EXIT 0
/tmp/tmp.* + /tmp/flash-remote-test-* before             → 0
make test-backend-remote REF=0a5f845                     → run 20260927-204936-16613: 5 steps PASS, 238 passed, remote exit 0, make EXIT 0 (no "unbound variable")
remote-test.sh backend --ref 0a5f845 --steps pytest -- -k tl_probe_no_such_test
                                                         → 0 selected, remote "exit code: 1", script EXIT 1 (exit code propagates)
/tmp/tmp.* + /tmp/flash-remote-test-* after both runs    → 0 (no leftovers)
```

### Review — 2026-09-28 — team-lead — final

**Verdict:** APPROVED — TL final sign-off.
- QA evidence exists: QA verdict PASS ticked, report `.ai/reports/qa/FEAT-004-qa-report.md` with server run ids. The runners were used for 15 `qa-remote` runs and the backend audit without defects.
- No unreviewed changes after the TL code review: remote-test.sh, lib/common.sh, lib/dental_guard.sh (fix reviewed, committed f85848b; `git diff f85848b HEAD` on them empty); setup-server.sh later extended by TASK-013 under its own review.
- Contracts/OpenAPI/docs: as recorded in the code review (api-contracts and ADRs updated in the same session; OpenAPI validated by `spectacular --validate` in the server suite and by QA TC-001-DOC-01..08 where applicable).
- Open bugs against this task: none (BUG-001 is TASK-004, BUG-002 is TASK-013; both Low).

## QA Log
- 2026-09-28 | qa | PASS | .ai/reports/qa/FEAT-004-qa-report.md; runners used in 15 qa-remote runs + backend audit 20260927-225853-111545

## Sign-off
- TL final review: ☑ (team-lead, 2026-09-28)
- QA verdict: ☑ PASS (.ai/reports/qa/FEAT-004-qa-report.md; runners used in 15 qa-remote runs + backend audit 20260927-225853-111545)
- PM acceptance: ☐
