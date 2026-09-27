# Sprint 01 — Foundation

- **Dates:** 2026-09-28 → 2026-10-09 (proposed; PO to confirm)
- **Owner:** PM · **Technical plan:** `.ai/reports/team-lead/sprint-01-technical-plan.md`
- **Status:** PLANNED

## Sprint goal
Deliver a production-grade, independently QA-verified Django REST Framework foundation (DRF_SKILL CREATE mode) for every Flash feature to build on.

## In scope
| Feature | Priority | Acceptance criteria |
|---|---|---|
| FEAT-001 Backend Platform Foundation | P0 | `backlog.md` → FEAT-001, criteria 1–10 (11 conditional on BLK-012) |
| FEAT-003 Frontend Foundation | P0 | **Conditional:** only if BLK-002 is RESOLVED by 2026-09-30; otherwise it moves to sprint-02 without affecting the sprint goal |

## Explicitly out of scope
Registration/profiles (FEAT-002), catalog, ordering, assignment, money, notifications, SSH deployment/staging/production/rollback (FEAT-004, sprint-02), Flutter.
The Infrastructure agent works from day 1 on the local Docker environment and backend CI.

## Pre-sprint actions
| Action | Owner | Status |
|---|---|---|
| Initialize git repository + initial commit (R1) | User approval → TL | OPEN |
| Choose git provider / CI platform (BLK-012) | PO via PM | OPEN |
| Circulate BLK-001, BLK-002 to Product Owner (needed during this sprint) | PM | OPEN |
| Circulate BLK-003, BLK-007, BLK-011 (needed for sprint-02/04 planning) | PM | OPEN |

## Dependencies & blockers
- BLK-001 affects only TASK-003's login identifier and token request shape. Due **2026-10-01**, or TASK-003 becomes BLOCKED.
- BLK-002 gates FEAT-003 (TASK-007, TASK-010).
- BLK-012 plus git init gate TASK-011 (backend CI). If they are unresolved by 2026-10-05, TASK-011 moves to sprint-02 (FEAT-004), with no effect on the sprint goal.

## Risks
- The login identifier is late → TASK-003 slips. Mitigation: TASK-003 is sequenced after TASK-002, TASK-004 and TASK-005.
- Python 3.13 is available only through Docker (ADR-009). QA and TL evidence must come from the Docker runtime.

## Exit criteria
- FEAT-001 is DONE: every task is READY_FOR_RELEASE with QA PASS and TL sign-off, and the PM has accepted it.
- The QA harness `qa/` runs against local Docker, and the regression baseline is recorded.
- The blocker status for sprint-02 inputs is known.

## Handoff to Team Lead
FEAT-001 (and FEAT-003, conditionally) are handed to the TL for technical breakdown on 2026-09-27.
Constraints:
- follow `DRF_SKILL.md` CREATE-mode order
- custom User model before the first migration (ADR-003)
- no domain apps besides `users`

## Sprint board
*(PM rebuilds this from the task files each session)*

| Task | Title | Agent | Depends on | Status |
|---|---|---|---|---|
| TASK-001 | Backend skeleton, settings & env config | Backend | — | TODO |
| TASK-002 | Common infrastructure (base model, errors, responses, pagination, throttling) | Backend | 001 | TODO |
| TASK-003 | Custom User model, roles, JWT auth, role permissions | Backend | 002, BLK-001 | TODO |
| TASK-004 | OpenAPI, Jazzmin & Health API | Backend | 002 | TODO |
| TASK-005 | Cache & optional Celery configuration | Backend | 001 | TODO |
| TASK-006 | Local Docker environment & root ops tooling | Infrastructure | 001, 005 (003, 004 for final check) | TODO |
| TASK-007 | Vue PWA scaffold & API client | Frontend | BLK-002, ADR-008 | BLOCKED |
| TASK-008 | QA strategy, Sprint-1 test plan & black-box harness | QA | — | TODO |
| TASK-009 | Verify FEAT-001 | QA | 001–006, 008 | TODO |
| TASK-010 | Verify FEAT-003 | QA | 007 | BACKLOG |
| TASK-011 | Backend CI pipeline | Infrastructure | 001, 006, BLK-012, git init | BLOCKED |

## Change log
| Date | Change | Reason |
|---|---|---|
| 2026-09-27 | Sprint planned | Discovery report §14 |
| 2026-09-27 | Infrastructure agent added; TASK-006 reassigned Backend → Infrastructure; TASK-011 (backend CI) added; FEAT-004 moved to P0 for sprint-02 | Agent spec §25–49, ADR-012 |
