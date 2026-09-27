# Sprint 01 — Foundation & First Live Deployment

- **Dates:** 2026-09-28 → 2026-10-09 (proposed; PO to confirm). The PO wants the build and deployment to start now.
- **Owner:** PM · **Technical plan:** `.ai/reports/team-lead/sprint-01-technical-plan.md` (**the TL must revise it** for this replan)
- **Status:** PLANNED (replanned 2026-09-27 after PO decisions)

## Sprint goal
Deliver the DRF backend foundation and the Vue PWA shell, deployed over HTTPS to the PO's shared server (`api.delivery.hossam-ameen.online`, `delivery.hossam-ameen.online`), and independently QA-verified **on that server**.

## PO decisions driving this plan (2026-09-27)
| Blocker | Decision | Status |
|---|---|---|
| BLK-001 | Login identifier = username + password (Django default `USERNAME_FIELD`) | RESOLVED |
| BLK-002 | The Vue 3 PWA (Vite) is the MVP web client at the web domain; Flutter later | RESOLVED |
| BLK-011 | Shared GCP VPS `34.123.215.195`, systemd, no Docker, SQLite, no Redis, nginx + certbot, backend port 8010 proposed, one environment, operator-triggered deploy | RESOLVED |
| BLK-012 | git init + initial commit `8b5dc17` on `main` done; no remote/provider yet | Still BLOCKED (CI only) |
| QA policy | QA and backend test suites run **on the server** against the deployed instance. The local machine is for building only. | REQ-009 |

## In scope
| Feature | Priority | Acceptance criteria |
|---|---|---|
| FEAT-001 Backend Platform Foundation | P0 | `backlog.md` → FEAT-001, criteria 1–10 (AC11 CI moved to the FEAT-004 deferred criteria) |
| FEAT-003 Frontend Foundation (Vue PWA) | P0 | `backlog.md` → FEAT-003, criteria 1–6 (no longer conditional) |
| FEAT-004 Deployment & Environments | P0 | `backlog.md` → FEAT-004, sprint-01 criteria 1–13 (systemd deploy of backend + PWA, nginx + TLS, health, rollback, dental non-interference, QA on the server) |

## Explicitly out of scope
- Registration/profiles/login screens (FEAT-002), catalog, ordering, assignment, money, notifications, Flutter.
- CI/CD pipelines (TASK-011, frontend/deploy CI): waiting on BLK-012.
- Docker on the server, PostgreSQL, Redis/Celery, a separate staging or production environment, auto-deploy.
- Any change to the dental-clinic app, its nginx sites, its service, `/srv/dental-clinic` or port 8000.
- Running QA locally (PO policy).

## Pre-sprint actions
| Action | Owner | Status |
|---|---|---|
| Initialize git repository + initial commit | Orchestrator (PO consent) | DONE (`8b5dc17`, `main`) |
| Resolve BLK-001, BLK-002, BLK-011 | PO via PM | DONE 2026-09-27 |
| Choose git provider / CI platform (BLK-012 remainder) | PO via PM | OPEN |
| Mirror the BLK-001/BLK-002 decisions into `flash_business_logic/` | PM (PO-approved), when the orchestrator allows it | OPEN |
| Circulate BLK-003, BLK-007 (needed for sprint-02/04 planning) | PM | OPEN |
| Revise the technical plan and create the FEAT-004 tasks, re-scope TASK-006/008/009/010 | TL | OPEN |

## Dependencies & blockers
- There are no business blockers on the sprint goal. BLK-001, BLK-002 and BLK-011 are RESOLVED.
- TASK-003 can now implement username + password. TASK-007/TASK-010 are unblocked (the TL moves them BLOCKED/BACKLOG → TODO).
- BLK-012 still gates TASK-011 and all CI. It does not affect the sprint goal, because deploys are operator-triggered.
- FEAT-001 and FEAT-003 acceptance evidence depends on FEAT-004: QA verifies them on the server (REQ-009).

## Risks
| Risk | Mitigation (TL/Infrastructure decide the technique) |
|---|---|
| **Shared production server:** a Flash deploy could break the dental-clinic app (nginx reload with a bad config, port clash, resource exhaustion, certbot touching other sites) | FEAT-004 AC9: separate site files/service/path/port, `nginx -t` before every reload, QA checks the dental sites before and after the deploy and the rollback. TL plan review is mandatory for the deploy tasks. |
| Small server (3.8 GB RAM, **no swap**, about 13 GB disk): a frontend build or dependency install on the server could trigger the OOM killer | Build locally where possible (the local machine is for building). Prune releases/backups. FEAT-004 AC10. |
| Python 3.13 is not on the server (python3.12 only) | TL ADR (e.g. `uv`-managed 3.13) before the backend deploy task starts. ADR-009 ("Docker as reference runtime") must be revised: the server becomes the reference runtime. |
| SQLite deviates from `DRF_SKILL.md` (PostgreSQL); no Redis means LocMem throttling/cache per process | TL ADR recording the PO choice. Keep `DATABASE_URL`-driven config so a PostgreSQL move is config + migration. Revisit before concurrency-heavy features (assignment, ledger). |
| Migrations on SQLite are hard to reverse | Pre-migrate DB backup and a rollback that restores it (FEAT-004 AC2, AC8). |
| QA only on the server means bugs surface late | Deploy early and often (first backend deploy right after TASK-001/004), and let QA write the harness (TASK-008) from day 1. |
| No CI: quality gates rely on manual runs | Backend test suite + lint run on the server as part of QA evidence (FEAT-001 AC9). CI follows BLK-012. |

## Exit criteria
- Both domains are live over HTTPS with valid certificates: `https://api.delivery.hossam-ameen.online` (API) and `https://delivery.hossam-ameen.online` (PWA).
- `/api/health/` and `/api/health/ready/` are green on the deployed instance (with the header token). `make health` passes.
- A rollback was exercised on the server and passed its health check.
- The dental-clinic sites were verified unaffected before and after the deploy and the rollback.
- A QA report with verdict **PASS** and evidence was produced **on the server** for FEAT-001, FEAT-003 and FEAT-004, including the backend test suite run (≥ 80% coverage) on the server's Python 3.13.
- TL final sign-off, and PM acceptance of FEAT-001, FEAT-003 and FEAT-004 (CI criteria deferred on BLK-012 do not block acceptance).

## Handoff to Team Lead
2026-09-27: FEAT-001, FEAT-003 and FEAT-004 are handed to the TL for technical (re)planning. Please:
1. Revise `.ai/reports/team-lead/sprint-01-technical-plan.md` for the systemd single-server deployment. No Docker on the server. QA and backend tests run on the server.
2. Record the ADRs: Python 3.13 provisioning on the server (e.g. `uv`); SQLite + no Redis (deviation from `DRF_SKILL.md`, PO decision); ADR-012 default mode `systemd` + backend port (8010 proposed); revise ADR-009 (reference runtime = server); accept ADR-008 (BLK-002 resolved); decide ADR-011.
3. Create the FEAT-004 tasks (Infrastructure owner, plus Backend/Frontend pieces for production settings and the build contract, plus a QA on-server verification task). Mandatory plan review for anything that touches nginx, certbot or systemd on the shared server.
4. Update the affected tasks' Activity Logs, which the PM cannot write this session:
   - TASK-003: BLK-001 RESOLVED → username + password.
   - TASK-007: BLK-002 RESOLVED → BLOCKED → TODO.
   - TASK-010: → TODO; verify on the deployed web domain.
   - TASK-006: re-scope. Local Docker is optional tooling, not an acceptance gate.
   - TASK-008/TASK-009: the harness targets the server.
   - TASK-011: stays BLOCKED on BLK-012 (remote/provider).
5. Constraints (unchanged): `DRF_SKILL.md` CREATE-mode order, custom User model before the first migration (ADR-003), no domain apps besides `users`. Never touch dental-clinic resources.

## Sprint board
*(PM rebuilds this from the task files each session; the statuses below are the task files' `## Status` as of 2026-09-27. FEAT-004 tasks are not created yet.)*

| Task | Title | Agent | Feature | Depends on | Status |
|---|---|---|---|---|---|
| TASK-001 | Backend skeleton, settings & env config | Backend | FEAT-001 | — | TODO |
| TASK-002 | Common infrastructure (base model, errors, responses, pagination, throttling) | Backend | FEAT-001 | 001 | TODO |
| TASK-003 | Custom User model, roles, JWT auth, role permissions | Backend | FEAT-001 | 002 (BLK-001 RESOLVED) | TODO |
| TASK-004 | OpenAPI, Jazzmin & Health API | Backend | FEAT-001 | 002 | TODO |
| TASK-005 | Cache & optional Celery configuration | Backend | FEAT-001 | 001 | TODO |
| TASK-006 | Local Docker environment & root ops tooling | Infrastructure | FEAT-001 | 001, 005 | TODO (TL to re-scope) |
| TASK-007 | Vue PWA scaffold & API client | Frontend | FEAT-003 | ADR-008 (BLK-002 RESOLVED) | BLOCKED (stale: TL to set TODO) |
| TASK-008 | QA strategy, Sprint-1 test plan & black-box harness | QA | all | — | TODO |
| TASK-009 | Verify FEAT-001 | QA | FEAT-001 | 001–006, 008, FEAT-004 deploy | TODO |
| TASK-010 | Verify FEAT-003 | QA | FEAT-003 | 007, FEAT-004 deploy | BACKLOG (TL to set TODO) |
| TASK-011 | Backend CI pipeline | Infrastructure | FEAT-004 (deferred) | BLK-012 | BLOCKED |
| *(TBD)* | FEAT-004 deployment tasks | Infrastructure / Backend / Frontend / QA | FEAT-004 | TL to create | — |

## Change log
| Date | Change | Reason |
|---|---|---|
| 2026-09-27 | Sprint planned | Discovery report §14 |
| 2026-09-27 | Infrastructure agent added; TASK-006 reassigned Backend → Infrastructure; TASK-011 (backend CI) added; FEAT-004 moved to P0 for sprint-02 | Agent spec §25–49, ADR-012 |
| 2026-09-27 | **Replan:** FEAT-003 unconditional; FEAT-004 (systemd deploy, nginx + TLS, health, rollback, QA on the server) pulled in from sprint-02; FEAT-001 AC1/AC9 changed to server evidence; FEAT-001 AC11 (CI) deferred; the sprint goal and exit criteria now require both domains live over HTTPS and a QA PASS on the server | PO decisions 2026-09-27: BLK-001/002/011 RESOLVED, BLK-012 partial, QA-on-server policy, "build and deploy now" |
