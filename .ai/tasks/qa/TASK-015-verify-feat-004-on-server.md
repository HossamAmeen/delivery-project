# Task

## ID
TASK-015

## Title
Independent verification of FEAT-004 on the server: post-deploy smoke, TLS, health, rollback, dental non-interference, regression

## Feature
FEAT-004 — Deployment & Environments

## Description
Verify the deployment independently **on the server** (REQ-009, ADR-018): post-deploy smoke and health, TLS/redirects, SPA serving, secrets hygiene, resource bounds, a QA-observed rollback + roll-forward, and that the dental-clinic app is unaffected before and after. Then run the full sprint-01 regression suite (FEAT-001 + FEAT-003 tests) on the final deployed release.

## Business Requirement
REQ-008, REQ-009; FEAT-004 criteria 1–13 (13 = this task); ADR-013, ADR-015, ADR-017, ADR-018

## Agent
QA

## Scope (allowed paths)
- `qa/**`, `.ai/reports/qa/**`

## Dependencies
- TASK-014 READY_FOR_QA (TL reviewed the deployment evidence); TASK-008
- Can run in parallel with TASK-009 and TASK-010 (same server; coordinate the rollback window so FEAT-001/003 runs are not in flight — run the rollback part first or last)

## Acceptance Criteria
- [ ] Dental baseline **before** anything: status codes of `https://dental.hossam-ameen.online/` and `https://api.dental.hossam-ameen.online/`, `systemctl is-active dental-clinic-backend`, sha256 of the dental nginx site files (read-only); the same **after** the rollback exercise and at the end — identical (FEAT-004 AC9).
- [ ] Smoke (`-m "smoke or deploy"`): both domains HTTPS with a valid chain for the right names, expiry > 60 days; HTTP → 301 HTTPS; HSTS present, no `includeSubDomains`; `/api/status/` 200; `/api/health/` + `/ready/` green with the header token and 401 without; web root 200, deep link 200, `manifest.webmanifest` and service worker served with the cache headers of ADR-015; `/static/` admin CSS served by nginx.
- [ ] Backend bound to 127.0.0.1:8010 only (port not reachable from outside: test from the server against the public IP:8010 → refused/filtered); `flash-backend` enabled and `Restart=always`.
- [ ] `make health`, `make restart TARGET=all` and `make migrate` (no pending migrations) run by QA succeed (FEAT-004 AC3); `DRY_RUN=1 make deploy` prints the steps with secrets redacted and `DEPLOYMENT_MODE=docker` is refused (AC1).
- [ ] QA-observed rollback: `make rollback` → previous release serves (`REVISION`), health green, the site stays up; then `make deploy` back to the latest; SQLite DB, media and `shared/.env` survive (AC8). Record whether the DB was restored and check it matches ADR-017.
- [ ] Secrets: no token/password in `qa/.results`, deploy output, `journalctl -u flash-backend` (last deploy window), or the Flash nginx logs (count-only grep on the server); `shared/.env` and `credentials.env` mode 0600; repo grep for secrets clean (AC11).
- [ ] Resources: memory/disk within budget, release/backup retention as configured (AC10).
- [ ] `deploy/README.md` followed as written for at least `health`, `restart`, `rollback` — gaps filed as documentation bugs (AC12).
- [ ] Full regression (`make qa-remote ARGS="-m regression"`, ratelimit last with `make throttle-reset`) on the final release, plus `make test-backend-remote REF=<deployed sha>` green.
- [ ] `.ai/reports/qa/FEAT-004-qa-report.md` with evidence and verdict PASS/FAIL; bugs filed with Suggested Area `Infrastructure` where applicable.

## Technical Notes
- Never edit `deploy/` or the Makefile; missing or broken tooling is a bug.
- The rollback exercise changes the live release: announce the window in the report and finish on the latest release.

## Testing Requirements
- Automated checks in `qa/smoke/` tagged `deploy` + `regression`; manual/exploratory steps documented with commands.

## Plan Review Required
No

## Status

TODO

## Activity Log
- 2026-09-27 | team-lead | — → TODO | created: QA on-server verification of FEAT-004 (REQ-009, ADR-018)

## Implementation Plan
(not required)

## Completion Report
(assignee, when moving to READY_FOR_REVIEW)
- Files changed:
- Tests added:
- Validation commands run + results:
- Contract/OpenAPI changes:
- Known limitations / remaining problems:

## Review Log

## QA Log

## Sign-off
- TL final review: ☐
- QA verdict: ☐
- PM acceptance: ☐
