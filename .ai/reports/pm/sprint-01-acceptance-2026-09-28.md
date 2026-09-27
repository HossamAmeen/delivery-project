# Sprint 01 — PM Acceptance & Closing Report (2026-09-28)

Owner: PM. Inputs:
- `.ai/reports/team-lead/sprint-01-final-review.md`
- `.ai/reports/qa/FEAT-001-qa-report.md`, `FEAT-003-qa-report.md`, `FEAT-004-qa-report.md`
- `.ai/reports/qa/bugs/BUG-001`, `BUG-002`
- the task files

Live: `https://delivery.hossam-ameen.online`, `https://api.delivery.hossam-ameen.online`, release `20260927-232246` / commit `d6669b6`.

## Decision
| Feature | Decision | Tasks moved READY_FOR_RELEASE → DONE |
|---|---|---|
| FEAT-001 Backend Platform Foundation | **ACCEPTED** | TASK-001, 002, 003, 004, 005, 016, 009 |
| FEAT-003 Frontend Foundation (Vue PWA) | **ACCEPTED** | TASK-007, 010 |
| FEAT-004 Deployment & Environments (sprint-01 criteria) | **ACCEPTED**, with carry-over conditions (below) | TASK-012, 013, 014, 017, 015 |
| Shared: QA harness | accepted with the features | TASK-008 |

Not part of this acceptance: TASK-006 (local Docker, BACKLOG, optional tooling) and TASK-011 (backend CI, BLOCKED on BLK-012). Both belong to deferred scope and do not gate the features, per the sprint-01 replan.

## Definition of Done check
| DoD item | FEAT-001 | FEAT-003 | FEAT-004 |
|---|---|---|---|
| Business requirements traceable | REQ-001/002/006/009/011; AC table in the QA report | REQ-001/037/009; AC1–6 | REQ-002/008/009; AC1–13 |
| Implemented | yes | yes | yes |
| API contracts match implementation + OpenAPI | § Foundation, § Identity ACTIVE (TL) | consumes them (CORS, envelope verified) | n/a |
| Tests written and passing | backend 257 passed, 98.45% on the server; API regression 110/110 | 67 unit tests (build gates); E2E 30/30 | deploy/runtime/dental suite in 110/110 |
| TL review + final sign-off | yes (every task, 2026-09-28) | yes | yes |
| QA PASS with evidence | yes (after the BUG-001 re-test) | yes | yes (13/13) |
| Infrastructure updated | served by FEAT-004; CI deferred (BLK-012, replan) | nginx static site, `VITE_API_BASE_URL` | owner; `deploy/README.md` |
| Documentation updated | `.ai/`, OpenAPI, READMEs | yes | `deploy/README.md` (QA AC12) |
| No open Critical/High bugs | none open (BUG-001 Low, CLOSED) | none | none (BUG-002 Low, CLOSED) |

Acceptance criteria → QA test cases are traceable in the per-AC tables of each QA report.

## Points weighed before accepting
1. **Live rollback and deploy run by the PO/operator, not QA (FEAT-004 AC3/AC8).** Accepted.
   - QA verified the outcome independently from server records (`PREVIOUS`, `MIGRATION_STATE`, backups, journal) and a full post-exercise regression.
   - The PO confirmed running the TASK-015 rollback and deploy.
   - The standalone `make restart` / `make migrate` targets ran only inside those flows. A standalone QA run is a carry-over.
2. **FEAT-001 AC5 anonymous throttle, shown by the backend suite on the server instead of a live endpoint.** Accepted.
   - No sprint-01 endpoint uses the anon scope (TL decision, api-contracts).
   - A live test is required with the first public anonymous endpoint (likely FEAT-002 registration).
3. **Untested `auto` DB-restore path.** Accepted as a **carry-over condition**, not a defect.
   - No migration has been deployed since the first release.
   - The restore mechanics were proven with `always` in TASK-014.
   - Evidence is due at the first migration-bearing deploy, expected in FEAT-002.
4. **Known limitations** (ADR-008 refresh token in `localStorage` / client-side logout; HTTP/2 off for dental safety, BLK-013; SQLite + file cache, ADR-017; no CI; English-only UI). All are recorded in ADRs and consistent with PO decisions (BLK-011: SQLite, no Redis, no CI remote). ADR-008 must be revisited before real customer data exists (flagged in sprint-02).
5. **Demo accounts** `demo_admin`, `demo_store`, `demo_driver`, `demo_customer` were created and verified by the PO. Noted; not an acceptance input.
6. **QA P2 gaps** (TC-001-JWT-16b expired token, TC-001-DOC-09 full schema diff, TC-003-MAN-01/02/05) are P2 and covered by other evidence. They don't block acceptance.

## Carry-over (tracked in `backlog.md` FEAT-004 and `sprints/sprint-02.md`)
- `auto` DB-restore evidence at the first migration deploy
- QA: standalone `make restart` / `make migrate`, `certbot renew --dry-run`, live anon-throttle test, JWT-16b, DOC-09
- CI (BLK-012); TASK-006 stays BACKLOG
- ADR-008 token storage review before customer self-registration goes live
- Minor: Node ≥ 24.15 / 22 LTS on the build machine; nginx template comment tidy

## Business documents
BLK-001 and BLK-002 (PO-approved 2026-09-27) were mirrored into `flash_business_logic/00_core/02_roles_and_permissions.md` (§ Authentication) and `flash_business_logic/README.md` (MVP client platform). The digest sync line and the requirements Change Log were updated.

## Sprint-02 readiness
See `.ai/planning/sprints/sprint-02.md` (DRAFT).
- **BLK-007 is a hard gate for FEAT-002.**
- BLK-012 gates only CI.
- BLK-008 and BLK-003 must follow soon for sprints 03–04.
