# QA Report — FEAT-004 Deployment & Environments (INTERIM)

QA task: TASK-015 · Tasks under verification: TASK-012, TASK-013, TASK-014, TASK-017 · Plan: `qa/plans/FEAT-004-test-plan.md` · Date: 2026-09-28 (runs are timestamped in UTC on 2026-09-27)

## Verdict: **NOT ISSUED (incomplete)**

The read-only half of TASK-015 is done and green, apart from two Low bugs. The state-changing steps have **not** been executed:
- `make restart TARGET=all`
- `make migrate`
- the QA-observed `make rollback`
- the roll-forward `make deploy` to `db8be6e`
- the final regression on that release

The session's permission policy denied `make restart`/`make migrate` as "Production Deploy". Rollback and deploy are the same kind of action, so QA did not attempt them or work around the denial. They need the user's explicit permission, or they can be run by the operator while QA observes. **No rollback window was opened. The live release is unchanged**: `20260927-205803` (`f85848b`).

## Environment

| Item | Value |
|---|---|
| Server | `34.123.215.195`, systemd mode, `/srv/flash` |
| Live release | `20260927-205803`, sha `f85848b9bbdb`, `dirty=false`; PREVIOUS = `20260927-205208` |
| Repo HEAD | `db8be6e` (the TASK-017 deploy code; not yet released) |
| Runners | `make qa-remote` (Python 3.13.15), `make health`, `make status`, `make deploy DRY_RUN=1`, `make rollback DRY_RUN=1` |

## Evidence

| # | Command | Run / output | Result |
|---|---|---|---|
| 1 | Dental **baseline**: `make qa-remote ARGS="-m deploy -k dental -v"` | 20260927-230318-114725: `dental-20260927T230322Z.json`, `dental-nginx-20260927T230322Z.json` | `dental.hossam-ameen.online/` 200, `api.dental…/` 302, `dental-clinic-backend` active, 7 non-Flash nginx files hashed (nginx.conf, default, and the 2 dental sites in available + enabled), none unreadable |
| 2 | `make qa-remote ARGS="-m 'smoke or deploy' --dental-expect=…=200,…=302"` | 20260927-230332-114972 | **67 passed, 1 failed** (BUG-001, FEAT-001 Low). Covers TLS ×2 domains (chain, SANs = exactly the 2 Flash names, > 60 days, HTTP → 301, HSTS without includeSubDomains/preload), web serving + cache headers, `/static/` admin CSS, runtime (127.0.0.1:8010 only; interface/public IP refused; enabled, `Restart=always`, MemoryMax; no Celery/Redis; layout; 0600 secret files; retention; disk), secret scans of the journal and Flash nginx logs (count-only, readable as `hossam`), dental checks |
| 3 | `make health` | terminal | 8 × PASS (unit active; local + public health/ready; status; web root; `nginx -t`), exit 0 |
| 4 | `make deploy DRY_RUN=1` | captured locally (48 lines) | Order: preflight → dental snapshot → local PWA build → rsync (`--link-dest`) → venv → `check --deploy` → collectstatic → backup + migrate → switch → restart → health → nginx safe-apply → health → dental compare (IDENTICAL) → prune. "DRY-RUN complete: nothing was changed". **0** secret patterns in the output |
| 5 | `DEPLOYMENT_MODE=docker make deploy DRY_RUN=1` | terminal | `ERROR DEPLOYMENT_MODE=docker: docker mode is deferred (ADR-015)`, exit 2 |
| 6 | `make rollback DRY_RUN=1` | terminal | `target from releases/20260927-205803/PREVIOUS: 20260927-205208`; `20260927-205803 applied migrations: no, restore DB: no` (ADR-017 `auto` → correct); "plan only: nothing changed"; dental guard IDENTICAL |
| 7 | `make qa-remote ARGS="smoke/test_server_runtime.py -k '…previous…'"` | 20260927-230500-117444 | 6 passed. New TC-004-RUN-14: `PREVIOUS` exists, 0644, names an existing release; no `/tmp/flash-nginx-backup-*` left (TASK-017) |
| 8 | Deploy-log secret grep (count-only) over `.ai/reports/infrastructure/FEAT-004-deploy-logs/` | local | 2 hits, both count **labels** in `05-logcheck.txt` (`"password=" in journald: 0`). No secret values |
| 9 | Dental **end** snapshot + `--dental-expect` | latest run | 5 passed; nginx hashes + service **IDENTICAL** to the baseline |
| 10 | `make status` | terminal | `previous: 20260927-205208 (from PREVIOUS)`; cert `flash-delivery` covers both domains, valid 89 days |
| — | `make restart TARGET=all`, `make migrate` | — | **Denied** by the session permission policy; not executed |

## Results per acceptance criterion

| AC | Result | Notes |
|---|---|---|
| AC1: mode from `.env`, nothing hardcoded | **PASS** | Run 5 (docker refused); run 4 (all values from `.env`) |
| AC2: `make deploy` pipeline, safe on failure | **PARTIAL** | Dry-run order verified (run 4). A real deploy observed by QA is pending |
| AC3: restart / migrate / health / rollback work | **PARTIAL** | `health` PASS; rollback **dry-run** PASS; `restart`, `migrate` and the real `rollback` are pending (permission) |
| AC4: Python 3.13, systemd, 127.0.0.1 only, auto-restart | **PASS** | TC-004-RUN-01..03, -13 (Python 3.13.15) |
| AC5: nginx from templates, both domains served | **PASS** (BUG-002 Low) | Run 2; `nginx -t` PASS in run 3. BUG-002: duplicate `X-Content-Type-Options` on the API site |
| AC6: Let's Encrypt, HTTP → HTTPS, renewal | **PASS** (renewal dry run not re-run by QA) | Run 2 + `make status`. `certbot renew --dry-run` needs sudo; the TASK-014 evidence was not re-executed |
| AC7: real health endpoints green, token never printed | **PASS** | Runs 2, 3, 8; journal + nginx logs 0 hits |
| AC8: releases/shared layout; rollback restores | **PARTIAL** | Layout PASS (RUN-05); rollback target + DB decision PASS (dry-run); the live rollback, and DB/media/.env surviving it, are pending |
| AC9: dental non-interference | **PASS so far** | Baseline (run 1) = end (run 9): identical codes, nginx hashes and service. The after-rollback snapshot is pending |
| AC10: resources, retention | **PASS** | `free_disk_mb≈11183`, `mem_available≈3068 MB`, no swap; `flash-backend` MemoryCurrent ≈ 101 MB; 3 releases ≤ 5; 2 flash-* backups ≤ 5 |
| AC11: no secrets in repo/templates/scripts/logs; 0600 | **PASS** | RUN-06/10/11, run 8, FEAT-001 TC-001-MAN-03 |
| AC12: `deploy/README.md` followable | **PARTIAL** | `health` and the rollback dry-run behave exactly as the README's Health/Rollback sections describe. `restart` and the real `rollback` could not be followed (pending) |
| AC13: QA smoke + backend suite on the server, QA report | **PARTIAL** | Smoke/deploy (run 2), the TASK-009/010 regressions, and the backend suite (`20260927-225853-111545`, 246 passed, 98.43%) on `f85848b`. The final regression on the rolled-forward release is pending |

## Task outcomes

| Task | Outcome |
|---|---|
| TASK-012 (bootstrap + remote runners) | **QA PASS.** `make qa-remote` (15 runs), `make test-backend-remote`, `make throttle-reset` were all used as documented:<ul><li>exit codes propagate (0 on pass, 1 on failure)</li><li>the venv is rebuilt only on a requirements hash change</li><li>the token and passwords never appear in the output ("QA_HEALTH_TOKEN: set")</li><li>results are copied to `qa/.results/<run>/` + `latest`</li><li>the QA Python is 3.13.15</li></ul> |
| TASK-013 (deploy tooling, systemd, nginx) | QA_IN_PROGRESS. BUG-002 (Low) filed; the real deploy/restart/rollback are pending |
| TASK-014 (server deploy, TLS, rollback) | QA_IN_PROGRESS. Live checks PASS; the rollback exercise is pending |
| TASK-017 (rollback target from history) | QA_IN_PROGRESS. `PREVIOUS` file, `make status` line, dry-run target and DB decision, and `/tmp` cleanup all PASS; the live bare rollback → `20260927-205208` and the roll-forward writing `PREVIOUS` are pending |

## Bugs

| ID | Severity | Area | Summary |
|---|---|---|---|
| [BUG-002](bugs/BUG-002-api-duplicate-nosniff-header.md) | Low | Infrastructure (TASK-013) | `X-Content-Type-Options: nosniff, nosniff` on proxied API responses |
| [BUG-001](bugs/BUG-001-health-401-missing-no-store.md) | Low | Backend (TASK-004) | seen again in the smoke/deploy run (FEAT-001) |

## Remaining steps (need permission for production-changing commands)
1. Announce the window. Take the dental snapshot (`make qa-remote ARGS="-m deploy -k dental"`). Record `make status`.
2. Run `make restart TARGET=all` → `make health`, and `make migrate` (expect no pending migrations).
3. Run `make rollback`. Expect `20260927-205208` serving: check `REVISION`, `make health`, and poll `/api/status/` during the switch. The DB is not restored (auto).
4. Take the dental snapshot with `--dental-expect=https://dental.hossam-ameen.online/=200,https://api.dental.hossam-ameen.online/=302` and compare the nginx hashes.
5. Run `make deploy`, which releases `db8be6e`. Its `PREVIOUS` must name `20260927-205208`, the release live at the switch (TASK-017). Then check that `shared/.env` is unchanged (mode and mtime via RUN-06), that the DB is present, and that the QA users still log in.
6. Run the full regression on the final release: `-m 'smoke or deploy'`, `-m 'regression and not e2e'`, `-m e2e`, the ratelimit session wrapped in `make throttle-reset`, and `make test-backend-remote REF=db8be6e`.
7. Take the final dental snapshot and issue the verdict.
