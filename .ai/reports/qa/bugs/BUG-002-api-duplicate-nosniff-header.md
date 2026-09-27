# Bug Report

## Bug ID

BUG-002

## Feature

FEAT-004 — Deployment & Environments (related task: TASK-013, nginx `api.conf.template`); observed during FEAT-001 verification (TASK-009)

## Severity

Low

<!-- Hygiene. Browsers use the first value of the combined header (Fetch spec), so the
     nosniff protection works. No functional or security impact. -->

## Business Rule Violated

ADR-015 (nginx API site). Response headers should be emitted once. FEAT-004 AC5 (nginx site configs correct). Found by TC-001-SEC-03.

## Steps to Reproduce

1. `GET https://api.delivery.hossam-ameen.online/api/status/` (any API response proxied to gunicorn).
2. Look at the `X-Content-Type-Options` header.

## Expected Result

A single `X-Content-Type-Options: nosniff`. Set it either in Django (`SECURE_CONTENT_TYPE_NOSNIFF=True`) or in nginx, not both, or hide the upstream copy with `proxy_hide_header`.

## Actual Result

`x-content-type-options: nosniff, nosniff`. Django's `SecurityMiddleware` adds it (`backend/config/settings/base.py:138`), and `deploy/nginx/api.conf.template:39` adds it again with `add_header … always`.

## Environment

Live release `20260927-205803` (commit `f85848b`). Requests from the server through nginx over HTTPS (`make qa-remote`).

## Evidence

Run `20260927-224701-94472` (`qa/.results/20260927-224701-94472/output.log`), full response headers of `GET /api/status/`:
```
'x-frame-options': 'DENY', 'vary': 'origin', 'x-content-type-options': 'nosniff, nosniff', 'referrer-policy': 'same-origin', ... 'strict-transport-security': 'max-age=31536000'
```
QA then changed the test to parse the header as the Fetch spec does (first value), so it passes. This bug tracks the duplication.

## Suggested Area

Infrastructure. Suggested fix: remove `add_header X-Content-Type-Options` from the API site (location `/`, proxied) and keep it for `/static/` and `/media/` only, or add `proxy_hide_header X-Content-Type-Options;`. Then `nginx -t` and reload per ADR-015.

## Status

ASSIGNED

## Routing (TL, 2026-09-28)

Confirmed: Infrastructure, TASK-013 (`deploy/nginx/api.conf.template`). Decision: **nginx stays the single edge source of `X-Content-Type-Options`; hide the upstream copy.**
- Add `proxy_hide_header X-Content-Type-Options;` in the proxied `location /` of the API TLS template (and the http bootstrap variant if it proxies). Keep the server-level `add_header X-Content-Type-Options "nosniff" always;` so `/static/`, `/media/` and nginx-generated errors (e.g. 502) still get exactly one.
- Do **not** change Django (`SECURE_CONTENT_TYPE_NOSNIFF=True` stays: it covers direct 127.0.0.1 access and `check --deploy`); no change to other headers or to the web site.
- Validation: bash -n/shellcheck unaffected; local render; isolated `sudo nginx -t -c /tmp/flash-*` on the server (TASK-013 method); no live apply by itself. READY_FOR_REVIEW → TL review. It ships with the next `make deploy` (the rendered file differs → safe-apply → reload), which is TASK-015's roll-forward.
- Live evidence after that deploy: exactly one `x-content-type-options: nosniff` on `/api/status/`, a `/static/` file and a 404; QA re-tests TC-001-SEC-03 (strict: one value).
- 2026-09-28 | qa | — → OPEN | filed from TASK-009 (TC-001-SEC-03)
- 2026-09-28 | team-lead | OPEN → ASSIGNED | routed to Infrastructure (TASK-013 → IN_PROGRESS); fix constraints in § Routing
- 2026-09-28 | team-lead | ASSIGNED → ASSIGNED | fix reviewed and APPROVED by the TL; ships with TASK-015's roll-forward `make deploy`; awaiting QA re-test (VERIFIED/REOPENED)
