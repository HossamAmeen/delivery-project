# Sprint 02 — Identity & Accounts (+ CI when unblocked)

- **Dates:** to be confirmed by the PO. Sprint-01 closed early (2026-09-28), so sprint-02 can start as soon as the PO answers BLK-007.
- **Owner:** PM
- **Status:** DRAFT: waiting on Product Owner decisions (see *Readiness*). Not handed to the TL yet.

## Proposed sprint goal
Customers can register, and every role can log in with username + password and see only their own profile, in the live PWA and API. CI runs on every push once a git remote exists.

## Proposed scope
| Feature | Priority | Readiness |
|---|---|---|
| FEAT-002 Identity & Accounts | P0 | **Needs BLK-007.** BLK-001 is resolved (username + password). |
| FEAT-004 deferred criteria: CI (backend, frontend, deploy pipelines; TASK-011) | P0 | **Needs BLK-012** (git provider/remote). If it is still open at sprint start, it stays out without affecting the goal. |
| FEAT-004 carry-over conditions | — | The `auto` DB-restore path is evidenced at the first migration-bearing deploy (FEAT-002 will add migrations). QA runs standalone `make restart` / `make migrate` / `certbot renew --dry-run`. |

## Readiness: decisions needed from the Product Owner
| # | Blocker | Question (options are in the blocker file) | Needed for | Needed by |
|---|---|---|---|---|
| 1 | **BLK-007** Onboarding & accounts | Who creates Store and Driver accounts (self-signup or admin)? Is approval/verification needed? Is email and/or phone collected or verified at registration? Can a store have several staff users? Can one user hold several roles? What data may each role see about the others? How long is history kept? | FEAT-002 acceptance criteria (models, registration endpoint, screens) | Before sprint-02 planning (**hard gate**) |
| 2 | **BLK-012** (remainder) Git provider & CI | Which provider (GitHub/GitLab/other)? Create the remote. May an image registry be used? | TASK-011 and all CI | Sprint-02 start (soft: CI slips, goal unaffected) |
| 3 | Sprint dates / cadence | Confirm the 2-week cadence and the sprint-02 start date | Planning | Sprint-02 start |

Needed soon after, for later sprints (circulate now):
| Blocker | Needed for | Needed by |
|---|---|---|
| BLK-008 Order scope & store profile (store fields, opening hours, addresses, single-store orders) | Sprint-03: FEAT-005, FEAT-007 | Sprint-03 planning |
| BLK-003 Pricing & fees model (**highest risk**) | Sprint-04: FEAT-008, FEAT-011 | Sprint-04 planning |
| BLK-005 Cancellation & terminal states | FEAT-008, FEAT-012 | Sprint-04 planning |
| BLK-009 Localization, languages, RTL, currency | FEAT-008 money display; the UI is English-only until then | Sprint-04 planning |
| BLK-004 Payment methods & collection | FEAT-011 | Sprint-05/06 planning |
| BLK-006 Assignment strategy | FEAT-009 | Sprint-05 planning |
| BLK-010 Notifications MVP | FEAT-013 | Sprint-07 planning |

## Known technical items the TL must plan into sprint-02
Accepted limitations from sprint-01 become relevant once real users register:
- ADR-008: the refresh token is in `localStorage` and logout is client-side only. The TL's own ADR says to "revisit before real customer data exists". Customer self-registration (if BLK-007 allows it) is that point.
- Demo accounts `demo_admin`, `demo_store`, `demo_driver` and `demo_customer` exist on the live server (created by the PO). Their passwords and lifetime are the PO's; FEAT-002 must not break them.
- SQLite and a file cache (ADR-017) are fine for FEAT-002. A PostgreSQL ADR is due before FEAT-009/ledger.
- P2 QA gaps: TC-001-JWT-16b (really expired token), TC-001-DOC-09 (full schema diff).
- Build machine: Node ≥ 24.15 or 22 LTS (EBADENGINE warnings).

## Explicitly out of scope (proposed)
Catalog, ordering, assignment, money, notifications, Flutter, a separate production environment, PostgreSQL/Redis, Docker.

## Handoff to Team Lead
Not yet. The handoff happens after BLK-007 is RESOLVED and the FEAT-002 acceptance criteria are written in `backlog.md`.

## Change log
| Date | Change | Reason |
|---|---|---|
| 2026-09-28 | Draft created with a readiness list | Sprint-01 closed; orchestrator request |
