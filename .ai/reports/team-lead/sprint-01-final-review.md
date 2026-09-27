# Sprint 01 — TL final review (2026-09-28)

Owner: Team Lead. Input for the PM's acceptance of FEAT-001, FEAT-003 and FEAT-004.

## Result
All sprint-01 implementation and QA tasks are **READY_FOR_RELEASE**, with the TL's final sign-off and QA PASS:

| Feature | Tasks (READY_FOR_RELEASE) | QA task / report | Verdict |
|---|---|---|---|
| FEAT-001 Backend Platform Foundation | TASK-001, 002, 003, 004, 005, 016 | TASK-009, `.ai/reports/qa/FEAT-001-qa-report.md` | PASS (after the BUG-001 re-test) |
| FEAT-003 Frontend Foundation (Vue PWA) | TASK-007 | TASK-010, `.ai/reports/qa/FEAT-003-qa-report.md` | PASS |
| FEAT-004 Deployment & Environments | TASK-012, 013, 014, 017 | TASK-015, `.ai/reports/qa/FEAT-004-qa-report.md` | PASS (13/13 AC) |
| (QA foundation) | TASK-008 | — | harness used for every run |

Not in this release: TASK-006 (local Docker, BACKLOG) and TASK-011 (backend CI, BLOCKED on BLK-012).

## Live state (TL read-only check, 2026-09-28)
- Release **`20260927-232246`** from commit **`d6669b6`**, `dirty=false`. `PREVIOUS` = `20260927-205208`, which is the correct deploy history.
- `make health` ALL CHECKS PASSED. `flash-backend` is active and enabled on `127.0.0.1:8010`, NRestarts 0.
- The TLS cert `flash-delivery` covers exactly the two Flash names and is valid until 2026-12-26.
- `/api/health/` returns 401 with `Cache-Control: no-store`. `/api/status/` sends exactly one `X-Content-Type-Options`.
- dental-clinic: active, MainPID 18284, NRestarts 0, unchanged since the audit. QA found its nginx files identical to the baseline.

## Evidence summary
- **Backend** (`make test-backend-remote REF=d6669b6`): ruff, format, check and makemigrations PASS; 257 passed; 98.45 % coverage.
- **QA on the server:**
  - API + deploy regression: 110/110.
  - E2E: 30/30 at 360 and 1280 px.
  - Rate-limit: 4 passed, 1 skipped (the anonymous scope, TL decision).
  - Dental before/after: identical.
- **Bugs:** BUG-001 (Low, health `no-store`) and BUG-002 (Low, duplicate `nosniff`) were fixed, VERIFIED and **CLOSED**. No bug is open.
- **Contracts:** api-contracts § Foundation and § Identity are **ACTIVE** and match OpenAPI.
- **Architecture decisions** made and amended this sprint:
  - ADR-008 (refresh policy, CORS `Retry-After`)
  - ADR-013 (definition of "previous release")
  - ADR-015 (permissions, TLS email, dental guard, HTTP/2 off / BLK-013, sudo list, gunicorn access log)
  - ADR-016, ADR-017, ADR-018 and ADR-019 wording

## Points the PM should know for acceptance
1. **Operator-run live steps (FEAT-004 AC3/AC8).**
   - The final rollback and roll-forward on the live server were run by the user (operator), not by QA, because of the session's permission policy.
   - QA verified the outcome from the server's records and a full regression, and the TL accepts this evidence.
   - QA did not run the standalone `make restart` and `make migrate` targets. Their code ran inside the operator's rollback and deploy, as the journal and `MIGRATION_STATE` show.
2. **FEAT-001 AC5, the "anonymous" throttle.**
   - Covered by the backend suite on the server, not by a live endpoint, because no sprint-01 public endpoint uses the `anon` scope (TL decision, recorded in api-contracts).
   - A live test comes with the first public anonymous endpoint.
3. **Known limitations, accepted and recorded in ADRs:**
   - the refresh token is in `localStorage` and logout is client-side only (ADR-008); revisit before real customer data exists
   - no HTTP/2, to protect dental (BLK-013)
   - SQLite and a file-based cache instead of PostgreSQL and Redis (ADR-017); a PostgreSQL ADR comes before FEAT-009 or the ledger
   - no CI yet (BLK-012; the ADR-015 exception applies)
   - English-only UI until BLK-009
4. **Not yet exercised live:** the `auto` DB-restore path with a release that actually applied a migration. There has been no migration since the first release, and it is to be evidenced at the first such deploy. The DB-restore mechanics were proven with `always`.
5. **Minor follow-ups (non-blocking, no task yet):**
   - build machine: Node ≥ 24.15 (or 22 LTS) to silence the EBADENGINE warnings
   - tidy a comment in the nginx API templates
   - QA P2 gap TC-001-DOC-09 (a full schema field-by-field diff)
