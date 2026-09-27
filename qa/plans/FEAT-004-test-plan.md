# FEAT-004 — Deployment & Environments — Test Plan

Owner: QA · Planned in: TASK-008 · Executed in: TASK-015 · Strategy: `qa/plans/test-strategy.md`
Sources: backlog FEAT-004 AC1–AC13 (sprint-01; CI deferred on BLK-012); ADR-013, ADR-015, ADR-016, ADR-017, ADR-018; TASK-012/013/014; `deploy/README.md`.

**Environment:** the shared VPS (`34.123.215.195`):
- Flash at `/srv/flash`, `flash-backend.service` on `127.0.0.1:8010`, nginx sites for the two Flash domains
- co-hosted dental-clinic app: `dental-clinic-backend` on port 8000, `/srv/dental-clinic`, `*.dental.hossam-ameen.online`

**Actors:** QA runs `make` targets from the local machine (they act on the server over SSH) and read-only commands on the server. **Never** edit `deploy/`, the Makefile or any server file. Missing or broken tooling is a bug for Infrastructure.

**Data setup:**
1. TASK-014 is READY_FOR_QA.
2. `make seed-qa-users` has been run.
3. The rollback window is announced in the report.
4. No FEAT-001/003 runs are in flight during the rollback part.

**Safety:**
- Dental is only read: GET, `systemctl is-active`, `sha256sum`.
- Secret scans are **count-only** (`grep -c`), and the value is never printed.
- The rollback exercise ends on the latest release.

## 1. Traceability

| AC | Criterion (short) | Test cases |
|---|---|---|
| AC1 | `DEPLOYMENT_MODE` from `.env`; nothing hardcoded | TC-004-MAN-02, TC-004-MAN-03 |
| AC2 | `make deploy` pipeline; a failed health check does not leave the site broken | TC-004-MAN-04 (report review + one observed deploy), TC-004-MAN-07 |
| AC3 | `make restart/migrate/health/rollback` work | TC-004-MAN-01, TC-004-MAN-05, TC-004-MAN-07 |
| AC4 | Python 3.13, systemd, 127.0.0.1 only, auto-restart | TC-004-RUN-01..03, TC-001-MAN-01 |
| AC5 | nginx from templates, `nginx -t`; both domains served | TC-004-TLS-01..05, TC-003-WEB-01..04, TC-004-WEB-01..03, TC-004-MAN-08 |
| AC6 | Let's Encrypt certs, HTTP→HTTPS, renewal | TC-004-TLS-01..04, TC-004-MAN-09 |
| AC7 | Real health endpoints green; the token never printed or logged | TC-001-HLT-01/07, TC-004-RUN-10/11, TC-004-MAN-06 |
| AC8 | Releases/shared layout; DB/media/.env survive; rollback restores | TC-004-RUN-05, TC-004-MAN-07 |
| AC9 | Dental non-interference | TC-004-DEN-01..02, TC-004-RUN-04, TC-004-RUN-12, TC-004-MAN-10 |
| AC10 | Resources; retention | TC-004-RUN-07, -08, TC-004-MAN-11 |
| AC11 | No secrets in repo/templates/scripts/logs; `.env` 0600 | TC-004-RUN-06, -10, -11, TC-004-MAN-06, TC-001-MAN-03 |
| AC12 | `deploy/README.md` complete and followable | TC-004-MAN-12 |
| AC13 | QA smoke/health + backend suite on the server; report PASS | TC-004-MAN-13 (the full regression) |

## 2. Test cases

Level: **HTTP** = `qa/smoke/` httpx/ssl; **RUN** = `qa/smoke/test_server_runtime.py` (read-only, on the server as `hossam`); **MAN** = manual command on the local machine or server, with output in the report.

### 2.1 TLS / HTTPS — `qa/smoke/test_tls_https.py` (each case ×2 domains)
| ID | Preconditions | Steps | Expected | Level | Priority |
|---|---|---|---|---|---|
| TC-004-TLS-01 | — | TLS handshake with the default CA store and hostname check | The chain verifies for the host | HTTP | P1 |
| TC-004-TLS-02 | — | Read the SANs | Exactly `{api.delivery…, delivery…}` (one `flash-delivery` cert, no dental name) | HTTP | P1 |
| TC-004-TLS-03 | — | `notAfter` | More than 60 days left (`QA_CERT_MIN_DAYS`) | HTTP | P1 |
| TC-004-TLS-04 | — | `GET http://<host>/qa/redirect-probe?x=1` without following | 301. `Location: https://<host>/qa/redirect-probe?x=1` | HTTP | P1 |
| TC-004-TLS-05 | — | `GET https://<host>/` headers | HSTS `max-age=31536000`. **No** `includeSubDomains`, no `preload` | HTTP | P1 |

### 2.2 Web/API serving — `qa/smoke/test_web_serving.py`
| ID | Preconditions | Steps | Expected | Level | Priority |
|---|---|---|---|---|---|
| TC-004-WEB-01 | — | `GET /` on the web domain | `Cache-Control` contains `no-cache` | HTTP | P1 |
| TC-004-WEB-02 | — | First `/assets/*` referenced by index.html | `max-age=31536000` and `immutable` | HTTP | P2 |
| TC-004-WEB-03 | — | `GET https://api…/static/admin/css/base.css` | 200 `text/css` (nginx alias to `shared/static`) | HTTP | P1 |
| (also) | | TC-003-WEB-01..05 (root, deep links, manifest/sw no-cache, bundle) | | HTTP | P1 |

### 2.3 Dental non-interference — `qa/smoke/test_dental_non_interference.py`
| ID | Preconditions | Steps | Expected | Level | Priority |
|---|---|---|---|---|---|
| TC-004-DEN-01 | — | GET each dental URL | Any status < 500, no connection error. The snapshot is written to `.results/dental-<UTC>.json` | HTTP | P1 |
| TC-004-DEN-03 | — | Read-only sha256 of every non-Flash file under `/etc/nginx/{nginx.conf,conf.d,sites-available,sites-enabled}` and `systemctl is-active dental-clinic-backend`, written to `.results/dental-nginx-<UTC>.json` (automates the hash part of MAN-10) | Snapshots before, after the rollback and at the end are identical | HTTP | P1 |
| TC-004-DEN-02 | baseline codes | Re-run with `--dental-expect="https://dental.hossam-ameen.online/=<c>,https://api.dental.hossam-ameen.online/=<c>"` | Identical to the baseline | HTTP | P1 |

### 2.4 Server runtime — `qa/smoke/test_server_runtime.py`
| ID | Preconditions | Steps | Expected | Level | Priority |
|---|---|---|---|---|---|
| TC-004-RUN-01 | — | `systemctl is-active/is-enabled/show -p Restart,MemoryMax flash-backend` | active, enabled, `Restart=always`, MemoryMax set | RUN | P1 |
| TC-004-RUN-02 | — | TCP connect to `127.0.0.1:8010`, `<primary iface IP>:8010`, `34.123.215.195:8010`; read ExecStart | Loopback open. Interface and public addresses refused/filtered. ExecStart binds `127.0.0.1:8010` | RUN | P1 |
| TC-004-RUN-03 | — | `ss -ltnH` | Port 8010 listeners are only `127.0.0.1:8010` | RUN | P1 |
| TC-004-RUN-04 | — | `systemctl is-active dental-clinic-backend` | active | RUN | P1 |
| TC-004-RUN-05 | — | Inspect `/srv/flash` | `current` → `releases/<id>` with `REVISION` and `frontend/dist/index.html`. `shared/{db,cache,static,media,logs,backups}` exist. `shared/db/flash.sqlite3` exists | RUN | P1 |
| TC-004-RUN-06 | — | `stat` (mode only) of `shared/.env`, `qa/credentials.env` | 0600 | RUN | P1 |
| TC-004-RUN-07 | — | Count `releases/*` and `shared/backups/flash-*.sqlite3` | ≤ 5 each (`RELEASES_TO_KEEP`, `DB_BACKUPS_TO_KEEP`) | RUN | P2 |
| TC-004-RUN-08 | — | Free disk on `/srv/flash`; `/proc/meminfo` recorded to `.results/resources.txt` | Free ≥ 1500 MB | RUN | P2 |
| TC-004-RUN-09 | — | `systemctl list-units flash-*`; connect to `127.0.0.1:6379` | No Celery unit. Nothing on 6379 | RUN | P1 |
| TC-004-RUN-10 | journal readable | `journalctl -u flash-backend --since -24h`, count-only | 0 occurrences of the health token or QA passwords, no `password=`. **Skip → TC-004-MAN-06** if not readable | RUN | P1 |
| TC-004-RUN-11 | logs readable | The Flash nginx access logs, count-only | 0 occurrences. **Skip → TC-004-MAN-06** if not readable | RUN | P1 |
| TC-004-RUN-13 | — | `current/venv/bin/python --version`; ExecStart | Python 3.13.x; gunicorn from `current/venv` | RUN | P1 |
| TC-004-RUN-14 | — | `PREVIOUS` in the current release; `/tmp/flash-nginx-backup-*` | `PREVIOUS` exists, 0644, names an existing release; no leftovers (TASK-017) | RUN | P1 |
| TC-004-RUN-15 | after rollback/deploy | Record REVISION/PREVIOUS/MIGRATION_STATE of every release and the mode/mtime of `shared/.env`, the DB and media → `.results/release-evidence.json` | DB present, `.env` 0600 and untouched; the history matches the rollback target and the ADR-017 DB decision | RUN | P1 |
| TC-004-RUN-12 | — | Config sanity | Deploy path not under `/srv/dental-clinic`. Port ≠ 8000 | RUN | P3 |

### 2.5 Manual / observed operations (TASK-015)
| ID | Preconditions | Steps | Expected | Level | Priority |
|---|---|---|---|---|---|
| TC-004-MAN-01 | — | `make health` | Green: health + ready via 127.0.0.1 and via HTTPS, web root, `systemctl is-active`, `nginx -t`. No token in the output | MAN | P1 |
| TC-004-MAN-02 | — | `DRY_RUN=1 make deploy` | Prints the steps (ADR-015 order). Secret values redacted. Nothing changes on the server | MAN | P1 |
| TC-004-MAN-03 | — | `DEPLOYMENT_MODE=docker make deploy` (or the documented override) | Non-zero exit, `docker mode is deferred (ADR-015)`. Nothing changes. `grep` of `deploy/` for hardcoded hosts/domains/ports/paths: none outside `.env.example`/templates variables | MAN | P1 |
| TC-004-MAN-04 | — | Review the TASK-014 deploy evidence, then observe one `make deploy` of the reviewed sha | The pipeline order matches AC2. Health green. `REVISION` = the deployed sha. The dental guard pre/post are identical | MAN | P1 |
| TC-004-MAN-05 | — | `make restart TARGET=all`, then `make health`; `make migrate` | Restart OK and health green within the timeout. `migrate` reports no pending migrations | MAN | P1 |
| TC-004-MAN-06 | — | On the server: `sudo grep -c -F -f <(printf '%s\n' "$token") /var/log/nginx/flash-*.log`, with the token read inside the remote shell from `shared/.env` and never echoed; the same for `journalctl -u flash-backend --since '<deploy window>'`, the deploy output and `qa/.results/*`. Grep for `password=` | All counts 0 | MAN | P1 |
| TC-004-MAN-07 | window announced; dental baseline taken (DEN-01 + MAN-10) | 1) Record `REVISION`, a DB row count proxy (`qa_*` users exist via login), and a media file checksum if one exists. 2) `make rollback`. 3) Check `REVISION` = previous, `make health` green, the site stays up (poll `/api/status/` every 2 s during the rollback, record any non-200), the `MIGRATION_STATE`/restore decision matches ADR-017 (`ROLLBACK_RESTORE_DB=auto`). 4) `make deploy` back to the latest. 5) `shared/.env` mtime unchanged, DB present, QA users can still log in, media intact. 6) Dental check with `--dental-expect` + MAN-10 | Everything as described. Downtime recorded. Ends on the latest release | MAN | P1 |
| TC-004-MAN-08 | — | Review: nginx sites are rendered from templates; `sudo nginx -t` passes (read-only); only the two Flash site files exist with the Flash names | Confirmed | MAN | P2 |
| TC-004-MAN-09 | — | `sudo certbot certificates --cert-name flash-delivery` (names/expiry only); `systemctl is-active certbot.timer`; `sudo certbot renew --dry-run --cert-name flash-delivery` | The cert covers both domains. The timer is active. The dry run succeeds | MAN | P2 |
| TC-004-MAN-10 | — | Before, after the rollback and at the end: `sha256sum` of every non-Flash file in `/etc/nginx/{nginx.conf,conf.d,sites-available,sites-enabled}` (read-only), `systemctl is-active dental-clinic-backend`, the dental status codes | All three snapshots identical | MAN | P1 |
| TC-004-MAN-11 | — | `free -m`, `systemctl show flash-backend -p MemoryCurrent`, `du -sh /srv/flash/*`, `df -h /srv` | Memory and disk within budget (AC10). Retention as configured | MAN | P2 |
| TC-004-MAN-12 | — | Follow `deploy/README.md` literally for `health`, `restart`, `rollback`; check that it covers server requirements, SSH, env, systemd, nginx/TLS, all commands, dental rules and troubleshooting | Followable as written. Gaps are filed as Low/Medium documentation bugs (Area Infrastructure) | MAN | P2 |
| TC-004-MAN-13 | the final release | `make qa-remote ARGS="-m 'smoke or deploy'"`, then `-m 'regression and not e2e'`, `-m e2e`, the ratelimit session with `make throttle-reset` around it, and `make test-backend-remote REF=<deployed sha>` | All green (known skips listed as gaps) | MAN | P1 |

## 3. Execution order (TASK-015)
1. Dental baseline: TC-004-DEN-01 and TC-004-MAN-10.
2. The smoke/deploy suite: `make qa-remote ARGS="-m 'smoke or deploy'"`.
3. TC-004-MAN-01..06, -08, -09, -11, -12.
4. The rollback window: TC-004-MAN-07, then DEN-02 and MAN-10 (after).
5. The full regression: TC-004-MAN-13.
6. The final dental check: DEN-02 and MAN-10 (end).

## 4. Exit criteria
- All P1 cases PASS.
- The dental snapshots are identical.
- No secret found anywhere.
- No open Critical/High bug.
- `.ai/reports/qa/FEAT-004-qa-report.md` is written with the evidence and the rollback window.
