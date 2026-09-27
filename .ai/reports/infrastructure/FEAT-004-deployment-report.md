# FEAT-004 — first deployment report (TASK-014, 2026-09-27)

Operator: Infrastructure agent, from the build machine over SSH (`hossam@34.123.215.195`). Source: commit **`f85848b`**
on `main`, clean tree (`dirty=false`, checked `backend frontend deploy Makefile`). All times UTC. Every state-changing
step ran inside the dental guard, and **every guard compare was IDENTICAL (33 entries)**. Secrets were never printed:
the counts below come from greps on the server.

## Live URLs
| URL | Result |
|---|---|
| https://delivery.hossam-ameen.online/ | PWA, 200, `id="app"`, `Cache-Control: no-cache` |
| https://delivery.hossam-ameen.online/driver (deep link) | 200, SPA fallback |
| https://api.delivery.hossam-ameen.online/api/status/ | 200 `{"success":true,…,"data":{"status":"ok"}}` |
| https://api.delivery.hossam-ameen.online/api/health/ , `/ready/` | 200 with the `X-Health-Check-Token` header; 401 `HEALTH_TOKEN_INVALID` without it |
| https://api.delivery.hossam-ameen.online/static/admin/css/nav_sidebar.css | **200 text/css** (www-data traverses `shared/` 0751) |
| https://api.delivery.hossam-ameen.online/admin/ | Django admin (Jazzmin), staff only |

## Timeline
| Time | Step | Result |
|---|---|---|
| 20:51:38 | baseline (read-only) | dental snapshot 33 entries; dental 200 / api.dental 302, **HTTP/1.1** with `curl --http2`; `nginx -t` clean; no Flash files; port 8010 free |
| 20:51:50 | `make setup-server` (11 s) | `shared/.env` created (0600, `SECRET_KEY` + `HEALTH_CHECK_PASSWORD` generated on the server); unit installed + **enabled**, not started (no release); both **http** bootstrap sites via safe-apply (`nginx -t` ok → reload); modes and www-data checks all `ok`; dental IDENTICAL |
| 20:52:08 | `make deploy` #1 → **20260927-205208** (39 s) | PWA built locally (28 files); 79 backend files; venv **Python 3.13.15**; `check --deploy` W004/W008 only (expected: nginx sets HSTS and redirects); collectstatic 244 (the duplicate `admin/js/popup_response.js` warning is expected); migrate: no DB → no backup, `applied=yes`; switch; unit started; http health green; nginx unchanged → no reload; dental IDENTICAL |
| 20:52:59 | `make tls` (68 s) | `certbot certonly --nginx --cert-name flash-delivery -d api.delivery… -d delivery…` **without `-m`** (reused the production ACME account); certificate issued; both sites → TLS templates via safe-apply; `certbot renew --dry-run --cert-name flash-delivery` → *all simulated renewals succeeded*; **dental IDENTICAL around certbot**, including `/etc/letsencrypt/options-ssl-nginx.conf` and the dental renewal conf |
| 20:54:24 | `make health` | 8/8 PASS (unit, local health + ready, **https token health + ready**, `/api/status/`, web root, `nginx -t`) |
| 20:54:48 | log / token checks | see § Secrets |
| 20:55:xx | `make seed-qa-users` | qa_customer, qa_driver, qa_store, qa_admin (staff + superuser), **qa_inactive (inactive)**; `credentials.env` 0600 hossam |
| 20:55:23 | `make setup-server WITH_E2E=1` (46 s) | `install-deps --dry-run`: *All system dependencies are installed*; apt: **0 upgraded, 0 newly installed**; dpkg count 694 → 694; Chromium 1243 + headless shell + ffmpeg → `/srv/flash/qa/browsers` (658 MB); disk 6.8 → 7.4 GB used; dental IDENTICAL |
| 20:56:32 | `make deploy` #2 → **20260927-205632** (43 s) | `--link-dest` #1; pre-migrate backup `flash-20260927-205632-….sqlite3` (132K), `applied=no`; health green; dental IDENTICAL |
| 20:57:47 | **`make rollback RESTORE_DB=always`** (6 s) | see § Rollback |
| 20:58:03 | `make deploy` #3 → **20260927-205803** (roll-forward, 43 s) | backup, `applied=no`, switch `205208 → 205803`, health green, dental IDENTICAL |
| 20:59:03 | crash test | see § Crash recovery |
| 20:59:30 | `make throttle-reset`, final checks | removed 3 cache files; final dental compare vs the 20:51 baseline **IDENTICAL** |

## Evidence
- **Listeners:** `127.0.0.1:8010` (flash-backend) and `127.0.0.1:8000` (dental) only. Flash does not listen on 0.0.0.0.
- **Modes** (`stat`): `/srv/flash` 755, `releases` 755, `shared` **751**, `static`/`media` 755, `db`/`backups`/`cache` **700**, `logs` 750,
  `sandbox`/`qa` 750, `shared/.env` **600**, `qa/credentials.env` 600, all `hossam:hossam`. www-data: `test -r static/.` ok,
  `media/.` ok; `ls shared`, `db/.`, `backups/.` and `cat .env` all **denied**.
- **Certificates** (`sudo certbot certificates`): `flash-delivery` → `api.delivery.hossam-ameen.online delivery.hossam-ameen.online`,
  expiry 2026-12-26 (89 days). `dental.hossam-ameen.online` is unchanged (expiry 2026-12-25). Renewal comes from the existing `certbot.timer`.
- **Redirects:** `http://api.delivery…/api/status/` → 301 `https://…`; `http://delivery…/driver` → 301 `https://…/driver`.
- **HSTS** `max-age=31536000` (no includeSubDomains/preload) on both. `/assets/*` → `public, max-age=31536000, immutable`;
  `index.html`, `sw.js`, `manifest.webmanifest` and SPA routes → `no-cache`.
- **HTTP/2 (BLK-013):** the Flash files contain 0 `http2`; `sudo nginx -t` shows **0** `protocol options redefined`. Dental negotiated
  **HTTP/1.1** before and **HTTP/1.1** after (`curl --http2`: dental 200, api.dental 302). Flash also serves HTTP/1.1.
- **Resources** (final): RAM available 3090 MB; `flash-backend` MemoryCurrent 91 MB / MemoryMax 700 MiB, Tasks 6/128;
  disk `/` 7.4 GB used, 11 GB free; releases 3 (75 + 22 + 22 MB thanks to hardlinks); backups 3; `shared` 16 MB; `qa` 815 MB
  (venv + Chromium); `sandbox` 67 MB.

## Secrets / query strings (counts on the server; values never printed)
One `GET https://api.delivery…/api/health/?password=<wrong dummy>` (→ 401) plus the same against 127.0.0.1:8010 were sent, then:
| Check | Count |
|---|---|
| health token (64 chars) in the local deploy/tls/health logs (uploaded to the server temporarily, then deleted) | 0 |
| token in `/var/log/nginx/flash-*.log` | 0 |
| token in `journalctl -u flash-backend` | 0 |
| dummy value in nginx flash logs / in journald | 0 / 0 |
| `password=` in nginx flash logs / in journald | 0 / 0 |
Both access logs record the path only, e.g. gunicorn: `- [27/Sep/2026:20:54:48 +0000] "GET /api/health/ HTTP/1.1" 401 101 2254us "curl/8.5.0"`;
nginx `flash_api`: `34.123.215.195 - […] "GET /api/health/ HTTP/1.1" 401 101 0.004 "curl/8.5.0"`.

## Rollback (live, including the DB-restore path)
1. After deploy #2, a marker user `zz_rollback_marker` was created (a write **after** release 205632's pre-migrate backup):
   users 6, marker present.
2. Plans (dry-run): `RESTORE_DB=auto` → *restore DB: no* (205632 applied no migrations, ADR-017 auto rule);
   `RESTORE_DB=always` → *restore DB: yes, from flash-20260927-205632-20260927-205706.sqlite3*.
3. `make rollback RESTORE_DB=always`: `current 205632 → 205208`; warning printed ("writes … are LOST"); the unit was stopped; the live DB was saved as
   `pre-rollback-20260927-205749.sqlite3` (0600); the backup was restored; the unit started; `ROLLBACK_RESULT … db_restored=1`; health 8/8; dental IDENTICAL.
4. Verified: users **5**, marker **absent**, all 5 QA users present → the restore happened, and exactly the post-backup write was lost.
5. Roll-forward: `make deploy` → 20260927-205803 (current), health green.

## Crash recovery
`sudo systemctl kill -s KILL flash-backend` at 20:59:03 → journald `Main process exited, code=killed, status=9/KILL` →
`Scheduled restart job, restart counter is at 1` → `Started` at 20:59:08. **Active + `/api/status/` 200 after 5.8 s**
(RestartSec=5). MainPID 40907 → 41268, NRestarts 1, `is-enabled` = enabled. `make health` passed afterwards. No reboot.

## Final state
- `current` → `releases/20260927-205803` (sha f85848b, dirty=false). Releases kept: 205208, 205632, 205803.
- `flash-backend` active + enabled on 127.0.0.1:8010. nginx: 2 Flash sites (TLS variant) + the unchanged dental/default sites.
- DB `shared/db/flash.sqlite3` (0600) with the 5 QA users. Backups: 2 pre-migrate + 1 pre-rollback.
- `/tmp/flash-nginx-backup-*` (2 dirs, the pre-setup and pre-TLS Flash files, which were empty or http variants) kept on the server as recovery copies.

## Deviations / findings
1. **Default rollback target = the previous release id, not deploy history.** After the rollback + roll-forward, a bare
   `make rollback` would target 205632 (the release rolled back *from*), not 205208. `deploy.sh`'s auto-rollback uses the
   true previous release, so it is correct. Manual rollbacks should use `TO=<id>` until this is fixed (proposal: record `PREVIOUS` in each
   release at switch time and use it as the default target). Not changed during the live run.
2. The rollback exercise used `RESTORE_DB=always`, because no release has applied a migration since the first deploy
   (`auto` → no restore, verified in the plan).
3. The local `npm ci` warns `EBADENGINE` (`abbrev@5`, `nopt@10` want node `^24.15`; the build machine has 24.3.0). The build
   succeeds. Frontend/operator FYI: upgrade the local Node to ≥ 24.15 or 22.22.
4. `LETSENCRYPT_EMAIL` stayed empty, and certbot reused the registered production account as designed.
