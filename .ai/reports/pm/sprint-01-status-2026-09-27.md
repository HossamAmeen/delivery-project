# Sprint 01 — Status (2026-09-27): Replan after PO decisions

## What changed
- The Product Owner resolved **BLK-001** (username + password), **BLK-002** (Vue 3 PWA is the MVP web client; Flutter later) and **BLK-011** (shared GCP VPS, systemd, SQLite, no Redis/Docker, nginx + Let's Encrypt, two domains, one environment, operator-triggered deploy).
- **BLK-012** is partially resolved. git init and the initial commit `8b5dc17` on `main` are done. The provider/remote is still open, so CI stays blocked.
- New PO policy: **QA and the backend test suites run on the server**, not locally (REQ-009).
- Sprint-01 now contains FEAT-001, FEAT-003 (no longer conditional) and **FEAT-004** (pulled in from sprint-02, re-scoped to the systemd single-server deployment).
- New sprint exit criteria: both domains live over HTTPS, health endpoints green, rollback exercised, dental-clinic unaffected, QA PASS produced on the server.

## Sprint board summary
No task status changed in this session (the PM does not own task statuses). TASK-007 (BLOCKED) and TASK-010 (BACKLOG) are now stale because BLK-002 was resolved. The TL must move them to TODO and create the FEAT-004 tasks.

## Top risks
1. The server is shared with a production app (dental-clinic). Any nginx, certbot or systemd mistake affects a live third-party service.
2. The server is small with no swap. Builds on the server could trigger the OOM killer.
3. Python 3.13 is missing on the server. An ADR is needed before the first backend deploy.
4. SQLite and no Redis deviate from `DRF_SKILL.md`. Accepted for now by PO choice; to be revisited before assignment/ledger work.

## Open business items
- BLK-012 remainder (git provider/remote, CI platform, registry): PO.
- BLK-007 (onboarding, email/phone collection & verification): needed for sprint-02 FEAT-002.
- Sprint dates (2026-09-28 → 2026-10-09) not yet confirmed by the PO.
- BLK-001/BLK-002 decisions to be mirrored into `flash_business_logic/` (PO-approved; not done in this session).
