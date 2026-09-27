# Flash — what's still needed

Status on 2026-09-28: **Flash is live over HTTPS.**
- PWA: https://delivery.hossam-ameen.online
- API: https://api.delivery.hossam-ameen.online/api/status/
- Admin (staff only): https://api.delivery.hossam-ameen.online/admin/

Live release: `20260927-205803` (commit `f85848b`). Latest commit: `d6669b6` (includes the bug fixes, not yet deployed).

## 1. Decision the owner needs to make (blocking)

The permission policy denied `make restart`, `make migrate`, `make rollback` and `make deploy` to the QA agent as "Production Deploy", even though `.claude/settings.local.json` allows them. These commands are needed to:
- finish TASK-015: the live rollback test and the roll-forward
- ship the BUG-001 and BUG-002 fixes to the live site

Choose one:
- [ ] **A. Run them yourself** from the repo root, and QA observes and records the results:
  ```bash
  make rollback        # expected target: 20260927-205208
  make health
  make deploy          # ships d6669b6 (bug fixes + TASK-017), records PREVIOUS
  make health
  ```
- [ ] **B. Approve the prompts** when the agents run these commands.
- [ ] **C. Skip the live rollback test.** It was already exercised once in TASK-014. Only `make deploy` runs, which still needs A or B for that one command.

## 2. After that (the agents do it)

1. [ ] QA: TASK-015 live steps, then re-test BUG-001 (TC-001-HLT-10) and BUG-002 (TC-001-SEC-03), then the full regression
2. [ ] TL: final sign-off for TASK-004, 013, 014, 015 and 017, and TASK-009 and 010
3. [ ] PM: accept FEAT-001, FEAT-003 and FEAT-004 → DONE

## Progress

| Task | Status |
|---|---|
| TASK-001, 002, 003, 005, 016 (backend), 007 (PWA), 012 (server bootstrap) | READY_FOR_RELEASE |
| TASK-004 (health, BUG-001 fix), TASK-013 (deploy tooling, BUG-002 fix) | READY_FOR_QA (fix reviewed, not deployed) |
| TASK-014 (live deploy), TASK-017 (rollback target) | READY_FOR_QA (waiting on TASK-015 live steps) |
| TASK-008 (QA harness) | READY_FOR_QA |
| TASK-009 (verify FEAT-001) | FAIL on BUG-001 only; re-test after deploy |
| TASK-010 (verify FEAT-003) | PASS |
| TASK-015 (verify FEAT-004) | read-only half PASS; live half blocked (section 1) |
| TASK-006 (local Docker) | BACKLOG |
| TASK-011 (CI) | BLOCKED on BLK-012 |

## 3. Open later (not blocking)

- [ ] **BLK-012:** git provider and remote (GitHub/GitLab), to unblock CI (TASK-011)
- [ ] **BLK-007:** onboarding and accounts (FEAT-002 registration, sprint-02)
- [ ] **BLK-009:** language and currency (the UI is English-only for now)
- [ ] **BLK-003 / 004 / 005 / 006 / 008 / 010:** pricing and fees, payments, cancellation, assignment, order scope, notifications
- [ ] Confirm the sprint-01 dates
- [ ] Copy the BLK-001 and BLK-002 decisions into `flash_business_logic/` (PM)
- [ ] Hardening before real customer data: refresh token in an httpOnly cookie, and a logout/blacklist endpoint
- [ ] Future: PostgreSQL/Redis instead of SQLite and a file cache; HTTP/2 only with the dental owner's consent
- [ ] Local build machine: upgrade Node to ≥ 24.15 or 22 LTS (EBADENGINE warnings)

## Reference

- Server: `hossam@34.123.215.195`, shared with dental-clinic, which must never be touched. Flash lives at `/srv/flash`, with the backend on `127.0.0.1:8010`.
- Ops: `make status`, `make health`, `make rollback [TO=<id>]`, `make deploy`. See `deploy/README.md`.
- Reports: `.ai/reports/infrastructure/FEAT-004-deployment-report.md` and `.ai/reports/qa/`
