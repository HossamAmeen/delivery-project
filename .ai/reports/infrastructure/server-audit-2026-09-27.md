# Server audit — 2026-09-27 (TASK-012)

Read-only audit of the shared VPS before any Flash change. Auditor: Infrastructure. Access: `ssh -i ~/.ssh/id_ed25519 hossam@34.123.215.195` (key by path; BatchMode).
Commands used: `cat /etc/os-release`, `nproc`, `lscpu`, `free -m`, `swapon --show`, `df -hT`, `sudo ss -ltnp`, `nginx -v`, `sudo nginx -T` (grep for file names / `server_name` / `listen` only), `sudo nginx -t`, `sudo certbot certificates` (names/domains/expiry only), `systemctl is-active|is-enabled|list-timers certbot.timer`, `systemctl is-active|is-enabled|show dental-clinic-backend`, `curl -o /dev/null -w '%{http_code}'`, `getent hosts`, tool `--version`s. No file was written on the server during the audit. `/srv/dental-clinic` was only `ls -ld` (not listed, not read).

## Host
| Item | Value |
|---|---|
| OS | Ubuntu 24.04.5 LTS, kernel 7.0.0-1013-gcp (GCP, us-central1-a) |
| CPU | 2 vCPU (AMD EPYC 7B12) |
| RAM | 3908 MB total, ~696 MB used, ~3211 MB available |
| Swap | **none** |
| Disk | `/` ext4 19 G, 6.3 G used, **13 G free** (35%); `/boot` 881 M; `/boot/efi` 105 M. `/srv` is on `/` |
| User | `hossam` (uid 1001), login shell `/bin/bash`, passwordless sudo (`google-sudoers`) |

## Listening TCP ports (`sudo ss -ltnp`)
| Address | Process |
|---|---|
| `0.0.0.0:80`, `[::]:80`, `0.0.0.0:443`, `[::]:443` | nginx |
| `0.0.0.0:22`, `[::]:22` | sshd |
| `127.0.0.1:8000` | gunicorn (dental-clinic) |
| `127.0.0.53:53`, `127.0.0.54:53` | systemd-resolved |

**Port 8010 is free** (no listener). Nothing else is listening.

## nginx
- `nginx/1.24.0 (Ubuntu)`; `sudo nginx -t` → syntax ok / test successful.
- `/etc/nginx/conf.d/` is empty. `nginx.conf` is the Ubuntu default (Nov 2023).
- `sites-available/`: `api.dental.hossam-ameen.online.conf`, `dental.hossam-ameen.online.conf`, `default`.
- `sites-enabled/` (symlinks): the same three.
- Configuration files loaded (`nginx -T` headers): `nginx.conf`, `mime.types`, the three enabled sites, `/etc/letsencrypt/options-ssl-nginx.conf`, and **dental include files under `/etc/nginx/dental-clinic/`** (`api.dental.hossam-ameen.online/backend.conf`, `dental.hossam-ameen.online/web.conf`, `security-headers.conf`).
- `server_name`s: `_` (default site, `listen 80 default_server`), `dental.hossam-ameen.online`, `api.dental.hossam-ameen.online` (both 80 + 443 ssl, certbot-managed `listen` lines).
- No `delivery` / Flash site exists yet.

## TLS / certbot
- certbot 2.9.0. `certbot.timer`: active, enabled (next run ~20:29 UTC).
- Certificates: **one**, name `dental.hossam-ameen.online`, domains `dental.hossam-ameen.online api.dental.hossam-ameen.online`, expiry 2026-12-25 (88 days).
- Renewal configs: `/etc/letsencrypt/renewal/dental.hossam-ameen.online.conf` only.
- ACME accounts: a **production** account exists under `/etc/letsencrypt/accounts/acme-v02.api.letsencrypt.org/directory/` (1 account) and a staging one. certbot reuses the existing production account when `-m` is omitted, so `LETSENCRYPT_EMAIL` can be optional for TASK-013/014 (see `.env.example`).

## DNS (resolved from the server)
- `api.delivery.hossam-ameen.online` → 34.123.215.195
- `delivery.hossam-ameen.online` → 34.123.215.195
Both Flash names already point at this host (ACME HTTP-01 will be possible).

## Tool versions
| Tool | Version |
|---|---|
| python3 (system) | 3.12.3 (`/usr/bin/python3.12`); **no python3.13** → uv (ADR-016) |
| uv | not installed (`~/.local/bin` absent) → installed by TASK-012 |
| node / npm | v22.23.3 / 10.9.9 (present; not used by Flash — no builds on the server, ADR-015) |
| rsync | 3.2.7 |
| envsubst | GNU gettext 0.21 |
| curl | 8.5.0 (OpenSSL 3.0.13, HTTP/2) |
| git | 2.43.0 |
| sqlite3 CLI | 3.45.1 |
| flock, perl, base64, timeout, setsid, pkill, tar, sha256sum | present (used by the runner) |
| docker | not installed (as required by ADR-015) |
| shellcheck | not installed (validation uses a local scratch venv `shellcheck-py`; nothing installed system-wide) |

## Dental-clinic footprint (observed, read-only)
| Item | Observed |
|---|---|
| systemd unit | `dental-clinic-backend.service` (`/etc/systemd/system/…`), active, enabled, MainPID 18284, NRestarts 0, active since 2026-09-26 22:52:01 UTC |
| process | gunicorn on `127.0.0.1:8000` |
| code | `/srv/dental-clinic` (root:root 0755) — not read |
| nginx | 2 sites + include dir `/etc/nginx/dental-clinic/` |
| TLS | cert `dental.hossam-ameen.online` |
| public status | `https://dental.hossam-ameen.online/` → **200**, `https://api.dental.hossam-ameen.online/` → **302** |
| other | `~hossam/dental-qa/` and `~hossam/.npm` exist in the shared home (dental tooling; Flash never touches them) |

Running services: chrony, cron, dbus, dental-clinic-backend, google-guest-agent, google-osconfig-agent, multipathd, networkd-dispatcher, nginx, polkit, rsyslog, snapd, ssh, systemd-*, unattended-upgrades.

## Deviations from BLK-011 / ADR-015 and consequences
1. **Dental nginx includes live outside `sites-*`/`conf.d`** (`/etc/nginx/dental-clinic/**`), plus `snippets/`, `/etc/letsencrypt/options-ssl-nginx.conf`. The ADR-015 guard list (`nginx.conf`, `conf.d`, `sites-available`, `sites-enabled`) would miss them. **`dental_guard.sh` therefore hashes every file and symlink under `/etc/nginx/`** except the two Flash site files (a superset of the ADR list), plus dental's unit file, its MainPID/start time, and `/etc/letsencrypt/renewal/*.conf` except Flash's `${CERT_NAME}`.
2. `https://api.dental.hossam-ameen.online/` returns **302**, not 200. The guard compares status codes before/after (not "== 200"), so this is fine.
3. A `default` site with `default_server` on port 80 exists. Flash sites must not declare `default_server` (TASK-013 note).
4. Everything else matches BLK-011/ADR-015: Ubuntu 24.04, 2 vCPU, 3.8 GB RAM, no swap, ~13 GB free, nginx 1.24, certbot + timer, no Docker, python 3.12 only, port 8010 free.
