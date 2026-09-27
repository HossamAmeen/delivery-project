# Flash — what's still needed

Status on 2026-09-28: **Sprint-01 is DONE and Flash is live over HTTPS.**
- PWA: https://delivery.hossam-ameen.online
- API: https://api.delivery.hossam-ameen.online/api/status/
- Admin (staff only): https://api.delivery.hossam-ameen.online/admin/

Live release: `20260927-232246` (commit `d6669b6`).

## 1. Sprint-01: DONE ✅ (2026-09-28)

FEAT-001 (backend), FEAT-003 (PWA) and FEAT-004 (deployment) were accepted by the PM. There are 15 tasks DONE, no open bugs, QA PASS on the server, and dental-clinic untouched.
Demo accounts: `demo_admin`, `demo_store`, `demo_driver`, `demo_customer` (the password is in `account.txt`, which is git-ignored).

## 2. Needed from the owner for Sprint-02

- [ ] **BLK-007: onboarding and accounts (blocking sprint-02):**
  - who creates Store and Driver accounts (self-signup or admin)?
  - is approval or verification needed?
  - is email and/or phone collected or verified?
  - can a store have several staff users?
  - can one user hold several roles?
  - what can each role see about the others?
  - how long is history kept?
- [ ] **BLK-012:** pick a git provider (GitHub, GitLab…), create the remote, and say whether an image registry may be used (needed for CI)
- [ ] Confirm the sprint length (2 weeks?) and the sprint-02 start date
- [ ] Before sprint-03: **BLK-008** (store profile and order scope). Before sprint-04: **BLK-003** (pricing and fees), **BLK-005** (cancellation), **BLK-009** (language and currency)
- [ ] Before real customer data: approve moving the refresh token out of localStorage (ADR-008 review)

## 3. Open later (not blocking)

- [ ] **BLK-009:** language and currency (the UI is English-only for now)
- [ ] **BLK-004 / 006 / 010:** payments, assignment strategy, notifications
- [ ] Hardening before real customer data: refresh token in an httpOnly cookie, and a logout/blacklist endpoint
- [ ] Future: PostgreSQL/Redis instead of SQLite and a file cache; HTTP/2 only with the dental owner's consent
- [ ] Local build machine: upgrade Node to ≥ 24.15 or 22 LTS (EBADENGINE warnings)

## Reference

- Server: `hossam@34.123.215.195`, shared with dental-clinic, which must never be touched. Flash lives at `/srv/flash`, with the backend on `127.0.0.1:8010`.
- Ops: `make status`, `make health`, `make rollback [TO=<id>]`, `make deploy`. See `deploy/README.md`.
- Reports: `.ai/reports/infrastructure/FEAT-004-deployment-report.md` and `.ai/reports/qa/`
