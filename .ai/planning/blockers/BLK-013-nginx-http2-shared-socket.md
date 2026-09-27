# Blocker

## ID

BLK-013

## Title

HTTP/2 on the Flash nginx 443 listeners would also switch dental-clinic to HTTP/2 (ADR-015 internal conflict)

## Raised By / Date

infrastructure — 2026-09-27 (TASK-013 validation)

## Affects

TASK-013 (templates), TASK-014 (live nginx apply), ADR-015 § nginx ("443 `ssl http2`") vs ADR-015 dental non-interference

## Description

ADR-015 specifies `listen 443 ssl http2` for both Flash sites. The server runs nginx **1.24**. Before 1.25.1, `http2` is a
`listen` parameter that applies to the whole address:port socket, not to one server block. Dental-clinic's sites listen on
the same `0.0.0.0:443` / `[::]:443` without `http2`. nginx merges the options (`http2 = new || old`), so adding Flash's
`http2` turns HTTP/2 on for **dental's** HTTPS sites too. That changes dental's protocol behaviour (ALPN h2), which
ADR-015 forbids ("Flash must never modify any of it"). The dental guard would not catch it, because status codes and
file hashes stay the same.

Evidence (server, isolated `nginx -t` against temp configs; nothing live was touched): a copy of the live `nginx.conf` +
the live dental sites + the rendered Flash TLS files:
- with `http2`: `[warn] protocol options redefined for 0.0.0.0:443 …` and `… for [::]:443 …` (test successful with warnings)
- without `http2`: syntax ok, test successful, **no warnings**

Report: `.ai/reports/infrastructure/TASK-013-validation-2026-09-27.md` § nginx.

## Why It Blocks Development

It doesn't block TASK-013: the templates take `NGINX_HTTP2=on|off`, and the default is **`off`** (dental unaffected).
It does block the final nginx shape applied live in TASK-014: the TL must confirm `off`, or accept the dental protocol change.

## Options Considered (for the decision owner)

- A: `NGINX_HTTP2=off` (current default). Flash is served over HTTP/1.1 + TLS, and dental is unchanged. A small performance cost for the PWA's first load; negligible at MVP traffic.
- B: `NGINX_HTTP2=on`. Flash and **dental** both get HTTP/2. This needs the dental owner's consent, since it changes a live third-party app.
- C: Upgrade nginx to ≥ 1.25.1 (per-server `http2 on;`). This is an apt change to a shared system package, affects dental, and is out of the agreed scope.

## Required Decision

The TL (with the PO if B or C) picks A/B/C, and ADR-015 § nginx is amended to match.

## Owner

Team Lead

## Status

RESOLVED

## Resolution

2026-09-27 — Team Lead: **option A**, `NGINX_HTTP2=off`. The user's hard constraint is that dental-clinic must not be affected; B changes dental's live protocol and C changes a shared system package, both out of scope. Flash is served over HTTP/1.1 + TLS (negligible cost at MVP traffic). `NGINX_HTTP2=on` is not allowed while dental shares the 443 socket on nginx < 1.25.1; re-enabling needs a new ADR with PO and dental-owner consent. Updated: ADR-015 § nginx ("No HTTP/2 on the shared 443 socket"), TASK-013 Review Log, TASK-014 (acceptance criteria + notes).
