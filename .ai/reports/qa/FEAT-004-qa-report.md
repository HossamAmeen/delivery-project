# QA Report — FEAT-004 Deployment & Environments

QA task: TASK-015 · Tasks verified: TASK-012, TASK-013, TASK-014, TASK-017 · Plan: `qa/plans/FEAT-004-test-plan.md` · Date: 2026-09-28 (runs are timestamped in UTC on 2026-09-27)

## Verdict: **PASS**

All 13 sprint-01 criteria of FEAT-004 have evidence that QA produced itself on the server. BUG-002 (the one Infrastructure finding) is fixed and VERIFIED, and no bug is open.

**Disclosure: the live state-changing steps were run by the user (operator), not by QA, and QA did not observe them live.** These steps were:
- the bare `make rollback`
- the roll-forward `make deploy` of `d6669b6`

The session's permission policy denied QA those commands, and `make restart` / `make migrate` as well. QA did not work around the denial. QA verified the *outcome* afterwards from the server's own records:
- release metadata (`REVISION`, `PREVIOUS`, `MIGRATION_STATE`)
- backups and file mode/mtime
- the systemd journal
- `make status`

It then ran the full regression on the resulting release. The standalone `make restart TARGET=all` and `make migrate` targets were not run by QA. Their code paths (`_fs_restart_backend`, `_fs_migrate`) ran inside the operator's rollback/deploy (journal and `MIGRATION_STATE` evidence below). This is recorded as a note on AC3, not as a gap in the behaviour.

## Environment

| Item | Value |
|---|---|
| Server | `34.123.215.195`, `DEPLOYMENT_MODE=systemd`, `/srv/flash`, `flash-backend` on `127.0.0.1:8010` |
| Release before the exercise | `20260927-205803` (`f85848b`), PREVIOUS `20260927-205208` |
| Final release | **`20260927-232246`**, sha `d6669b61f5a6`, `dirty=false`, built 2026-09-27T23:23:15Z, PREVIOUS `20260927-205208` |
| Runners | `make qa-remote` (Python 3.13.15), `make test-backend-remote`, `make status`, `make health`, `make logs`, `make deploy DRY_RUN=1`, `make rollback DRY_RUN=1`, `make throttle-reset` |

## Timeline

| UTC | Actor | Event | Evidence |
|---|---|---|---|
| 23:03:22 | QA | Dental **baseline** | run 20260927-230318-114725 |
| 23:03–23:05 | QA | Pre-exercise smoke/deploy, `make health`, the deploy/rollback dry runs, TASK-017 checks | see Evidence |
| 23:22:31 → 23:22:32 | operator | **Rollback** `20260927-205803` → `20260927-205208`: `flash-backend` stopped and started (new master pid 51677, 2 workers). About 1 s without a backend process | `make logs` journal |
| 23:23:15 → 23:23:28 | operator | **Deploy** `d6669b6` → release `20260927-232246`: pre-migrate backup `flash-20260927-232246-20260927-232326.sqlite3`, `MIGRATION_STATE applied=no`, switch, restart (pid 52135) | `release-evidence.json`, journal |
| 23:35–23:41 | QA | Post-exercise verification + full regression | runs below |

## Evidence

| # | Command | Run ID (`qa/.results/<id>/`) | Result |
|---|---|---|---|
| 1 | Dental baseline: `make qa-remote ARGS="-m deploy -k dental -v"` | 20260927-230318-114725 | dental `/` 200, `api.dental` 302, `dental-clinic-backend` active, 7 non-Flash nginx files hashed, none unreadable |
| 2 | `make qa-remote ARGS="-m 'smoke or deploy' --dental-expect=…"` (pre-exercise) | 20260927-230332-114972 | 67 passed, 1 failed (BUG-001, since VERIFIED) |
| 3 | `make deploy DRY_RUN=1` | local capture | ADR-015 order; "nothing was changed"; 0 secret patterns; dental guard IDENTICAL |
| 4 | `DEPLOYMENT_MODE=docker make deploy DRY_RUN=1` | terminal | `docker mode is deferred (ADR-015)`, exit 2 |
| 5 | `make rollback DRY_RUN=1` (pre-exercise) | terminal | `target from releases/20260927-205803/PREVIOUS: 20260927-205208`; `applied migrations: no, restore DB: no`; plan only |
| 6 | `make status` (post-exercise) | terminal | current `20260927-232246` (`d6669b6`), `previous: 20260927-205208 (from PREVIOUS)`, 4 releases, 4 backups, both nginx sites TLS, cert `flash-delivery` valid 89 days, `NRestarts=0` |
| 7 | `make logs LINES=600` | terminal | Two stop/start cycles only: 23:22:31–32 (rollback) and 23:23:28 (deploy); gunicorn listening on `127.0.0.1:8010` both times |
| 8 | `make qa-remote ARGS="smoke/test_server_runtime.py -k 'history or previous' -v"` (new TC-004-RUN-15) | 20260927-233518-139162: `release-evidence.json` | See *Rollback / roll-forward verification* |
| 9 | **Full regression**: `make qa-remote ARGS="-m 'regression and not e2e' --dental-expect=https://dental.hossam-ameen.online/=200,https://api.dental.hossam-ameen.online/=302"` | 20260927-233545-139616 | **110 passed, 0 failed, 0 skipped** (API, smoke, deploy, runtime, dental) |
| 10 | `make qa-remote ARGS="-m e2e"` | 20260927-233803-141021 | **30 passed** |
| 11 | `make throttle-reset` → `-m ratelimit -v` → `make throttle-reset` | 20260927-233920-141829 | 4 passed, 1 skipped (anon, TL decision); resets removed 10 and 3 files |
| 12 | `make test-backend-remote REF=d6669b6` | `backend/.remote-results/20260927-234034-142654/` | ruff, format, check, makemigrations PASS; **257 passed**; **98.45%** |
| 13 | BUG re-test: `-k 'security_headers or not_cacheable'` | 20260927-234058-143079 | 2 passed (`X-Content-Type-Options` sent exactly once; health 401 has `no-store`) |
| 14 | `make health` (final) | terminal | ALL CHECKS PASSED |
| 15 | Dental end state: nginx hash snapshot of run 9 vs baseline (run 1) | `dental-nginx-20260927T233751Z.json` vs `dental-nginx-20260927T230322Z.json` | **IDENTICAL** (files + service). Status codes equal the baseline (`--dental-expect` passed) |

## Rollback / roll-forward verification (from the server's records; not observed live)

From `release-evidence.json` (run 8), the journal (7) and `make status` (6):
- **The bare rollback targeted the recorded history, not id order.** The new release `20260927-232246` has `PREVIOUS` = `20260927-205208`. That means `205208` was `current` at the deploy switch, so the preceding bare rollback moved `205803 → 205208`, exactly as the dry run predicted (5) and as TASK-017 requires.
- **DB decision matched ADR-017 (`auto`).** `20260927-205803` had `MIGRATION_STATE … applied=no`, so no restore was due, and none happened: there is no new `pre-rollback-*.sqlite3` (the only one is from TASK-014 at 20:57:49). The roll-forward took the pre-migrate backup `flash-20260927-232246-20260927-232326.sqlite3` (`applied=no`).
- **Shared state survived.**
  - `shared/.env` is mode 0600 with mtime 2026-09-27T20:51:57Z, untouched by rollback or deploy.
  - `shared/db/flash.sqlite3` is present, mode 0600.
  - The QA users, including `qa_inactive`, still authenticate on the new release (run 9: TC-001-ME-01 ×4, TC-001-JWT-07).
  - Media: 0 files before and after, so only the directory's survival is checked.
- **Health.** The operator's scripts gate on health. QA's `make health` and the regression after the exercise are green. The journal shows about 1 s between stop and start at each switch. QA did not poll during the switch, because it did not observe it.
- **Dental.** Codes, nginx hashes and the service are identical to the baseline after the exercise (15).

## Results per acceptance criterion

| AC | Result | Evidence |
|---|---|---|
| AC1: mode from `.env`, nothing hardcoded | **PASS** | 3, 4 |
| AC2: `make deploy` pipeline; a failed health check does not leave the site broken | **PASS** | Dry-run order (3); a real deploy produced a clean release (`dirty=false`), a backup and `MIGRATION_STATE` (8), health green (14). The failure path was verified in TASK-014 (auto-rollback evidence in its deploy logs), not re-provoked by QA |
| AC3: restart / migrate / health / rollback | **PASS** (with note) | `health` (14); rollback (8, 7, 5). `restart` and `migrate` were exercised inside the operator's rollback/deploy (journal restarts; `MIGRATION_STATE`). The standalone targets were not run by QA (permission) |
| AC4: Python 3.13, systemd, 127.0.0.1 only, auto-restart | **PASS** | Run 9: TC-004-RUN-01..03, -13 |
| AC5: nginx from templates, `nginx -t`, both domains served | **PASS** | Run 9, 14; BUG-002 fixed (13) |
| AC6: Let's Encrypt, HTTP → HTTPS, renewal | **PASS** | Run 9 TLS cases; `make status` cert valid 89 days. The renewal dry run is TASK-014 evidence; QA did not re-run it (needs sudo) |
| AC7: health endpoints green; token never printed or logged | **PASS** | 9, 14; journal and Flash nginx logs 0 hits (RUN-10/11 in run 9) |
| AC8: releases/shared layout; DB/media/.env survive; rollback restores | **PASS** | See the verification section |
| AC9: dental non-interference | **PASS** | 1, 15; dental guard IDENTICAL in 3 and 5 |
| AC10: resources, retention | **PASS** | Run 9 RUN-07/08: 4 releases ≤ 5, flash-* backups ≤ 5, about 11.1 GB free; `MemoryCurrent` about 97 MB |
| AC11: no secrets anywhere; 0600 files | **PASS** | Run 9 RUN-06/10/11; deploy-log grep (count labels only); QA `.results` session scans clean in every run |
| AC12: `deploy/README.md` followable | **PASS** (with note) | Health and Rollback sections match observed behaviour (dry run, target, DB decision, `make status` line). The live commands were run by the operator following the README |
| AC13: QA smoke/health + backend suite on the server; QA report | **PASS** | 9–12, this report |

## Task outcomes

| Task | Outcome |
|---|---|
| TASK-012 (bootstrap + runners) | QA PASS (earlier; the TL has since moved it to READY_FOR_RELEASE) |
| TASK-013 (deploy tooling, systemd, nginx) | **QA PASS**. BUG-002 VERIFIED |
| TASK-014 (server deploy, TLS, rollback) | **QA PASS** |
| TASK-017 (rollback target from deploy history) | **QA PASS**:<ul><li>`PREVIOUS` is written on deploy</li><li>the bare rollback followed it</li><li>`make status` shows it</li><li>no `/tmp` leftovers (RUN-14)</li></ul> |

## Bugs

| ID | Severity | Area | Status |
|---|---|---|---|
| [BUG-002](bugs/BUG-002-api-duplicate-nosniff-header.md) | Low | Infrastructure (TASK-013) | **VERIFIED** on `d6669b6` |
| [BUG-001](bugs/BUG-001-health-401-missing-no-store.md) | Low | Backend (TASK-004), FEAT-001 | **VERIFIED** on `d6669b6` |

## Notes and gaps
- QA did not observe the live rollback/deploy (the operator ran them), so there is no QA-side uptime poll during the switch. The journal shows about 1 s stop→start at each switch.
- The standalone `make restart TARGET=all` / `make migrate` targets and `certbot renew --dry-run` were not run by QA.
- Harness additions in this task:
  - TC-004-DEN-03: dental nginx hash snapshot
  - TC-004-RUN-13: release Python
  - TC-004-RUN-14: `PREVIOUS` and `/tmp` cleanup
  - TC-004-RUN-15: release history evidence
  - TC-001-SEC-03 now requires a single `X-Content-Type-Options` value
