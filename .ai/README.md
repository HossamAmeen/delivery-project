# Flash — AI Engineering Team Operating System

This folder is how the seven Flash agents work together: Project Manager, Team Lead,
Backend, Frontend, Fullstack, QA and Infrastructure/DevOps.

```
                   PROJECT MANAGER
                          │
                      TEAM LEAD
       ┌──────────┬───────┴───────┬──────────────┐
    Backend    Frontend       Fullstack    Infrastructure  ← works all sprint long
       └──────────┴───────┬───────┘        (CI, Docker, Nginx,
                          QA                 staging, deploy)
```
Agents share information only through the files in this folder and the repository.
Chat history, memory and "I assumed…" are not handoff channels.

## Sources of truth

| Topic | Canonical source | Owner |
|---|---|---|
| Business rules (detailed) | `docs/business/` | PM / Product Owner |
| Business rules (agent digest) | `.ai/business/business-logic.md` | PM |
| Requirements, scope, priorities | `.ai/business/requirements.md`, `.ai/planning/` | PM |
| Brand and design assets | `docs/design/` | PM / Product Owner |
| Backend engineering standard | `docs/standards/DRF_SKILL.md` (deployment layout adapted by ADR-012) | Team Lead |
| Agent procedures (skills) | `.claude/skills/*/SKILL.md`, attached in `.claude/agents/*.md` | Team Lead (with user approval) |
| Deployment & operations | `deploy/README.md`, ADR-012/013/014 | Infrastructure (TL approves) |
| Architecture, decisions, API contracts | `.ai/architecture/` | Team Lead |
| Work items | `.ai/tasks/` | Team Lead (creates), assignee (updates) |
| Bugs | `.ai/reports/qa/bugs/` | QA |
| Blockers | `.ai/planning/blockers/` | Whoever is blocked (creates), PM/TL (resolves) |

If `business-logic.md` disagrees with `docs/business/`, `docs/business/` wins
and the conflict must be reported to the PM (see ADR-004).

## Repository map

```
docs/{business,design,standards}/   ← business rules, brand, engineering standards
backend/ frontend/ qa/ deploy/       ← code, QA suite, infrastructure
.ai/                                 ← this operating system (below)
.claude/agents/ .claude/skills/      ← subagents and the skills they preload
```

## Folder map (`.ai/`)

```
.ai/
├── README.md                  ← this file
├── agents/                    ← one instruction file per agent (read yours first)
├── business/                  ← business-logic digest, requirements, glossary
├── planning/
│   ├── roadmap.md
│   ├── backlog.md             ← features (FEAT-NNN)
│   ├── sprints/               ← sprint-NN.md
│   └── blockers/              ← BLK-NNN-*.md
├── architecture/              ← architecture.md, api-contracts.md, decisions.md (ADRs)
├── tasks/{backend,frontend,fullstack,qa,infrastructure}/   ← TASK-NNN-*.md
├── reports/
│   ├── pm/                    ← discovery report, sprint status/acceptance
│   ├── team-lead/             ← technical plans, reviews
│   ├── qa/                    ← QA reports; bugs/BUG-NNN-*.md
│   └── infrastructure/        ← infra designs, validation & deployment reports
└── templates/                 ← task, bug, blocker, feature, review templates
```

## Identifiers

| Kind | Format | Numbering |
|---|---|---|
| Feature | `FEAT-001` | global, assigned by PM in `backlog.md` |
| Task | `TASK-001` | global across all agents, assigned by TL |
| Bug | `BUG-001` | global, assigned by QA |
| Blocker | `BLK-001` | global |
| Decision | `ADR-001` | global, in `architecture/decisions.md` |
| Requirement | `REQ-001` | global, in `business/requirements.md` |
| Sprint | `sprint-01` | sequential |

Before creating an ID, run `grep -rho "TASK-[0-9]*" .ai | sort -u | tail -1` (or the equivalent for other kinds) and use the next number.

## Workflow

```
Business requirement
  → PM: feature (FEAT) + acceptance criteria + priority → sprint
  → TL: technical design + API contract + ADRs → tasks (Backend / Frontend / Fullstack / QA / Infrastructure)
  → [TL plan review, if the task is complex]
  → Developers: implement → READY_FOR_REVIEW
  → TL: code review → READY_FOR_QA (or back to IN_PROGRESS)
  → QA: independent verification → pass, or BUG → TL → developer → fix → QA re-test
  → TL: final review / sign-off
  → PM: acceptance against the Definition of Done → DONE
```

The Infrastructure agent runs in parallel from the start of the sprint (CI, Docker, Nginx, staging, deployment).
Its tasks follow the same review → QA → sign-off path. QA verifies deployments through smoke and health tests on the target environment.

Nothing skips a stage. A feature is DONE only when all of its tasks are DONE.

## Task status lifecycle

| Status | Set by | Meaning |
|---|---|---|
| `BACKLOG` | TL | Task exists but is not in the current sprint |
| `TODO` | TL | In the sprint, ready to start |
| `IN_PROGRESS` | Assignee | Work started |
| `BLOCKED` | Assignee | Waiting on a `BLK-NNN` (link it) |
| `READY_FOR_REVIEW` | Assignee | Implementation + tests + completion report done |
| `REVIEW` | TL | TL is reviewing |
| `READY_FOR_QA` | TL | Review approved |
| `QA_IN_PROGRESS` | QA | QA verifying. On PASS, QA ticks `QA verdict` in Sign-off and leaves the status for the TL's final review |
| `QA_FAILED` | QA | Bug(s) filed; TL routes them back to the developer (→ `IN_PROGRESS`) |
| `READY_FOR_RELEASE` | TL | QA passed **and** TL final review signed off |
| `DONE` | PM | PM accepted against the Definition of Done |

The person changing a status appends a line to the task's `## Activity Log`:
`- 2026-09-27 | <agent> | <OLD> → <NEW> | <one-line reason / link>`

## Definition of Done (feature level)

A feature is not DONE until:
- [ ] Business requirements implemented (traceable to REQ / business-logic sections)
- [ ] Backend implemented (and meets `docs/standards/DRF_SKILL.md` §58 Definition of Done)
- [ ] Frontend implemented, when required
- [ ] API contracts in `architecture/api-contracts.md` match the implementation and OpenAPI
- [ ] Tests written and passing (developer tests + QA tests)
- [ ] TL review recorded
- [ ] QA verification recorded with evidence; QA verdict PASS
- [ ] TL final sign-off recorded
- [ ] Infrastructure updated when required (CI green, deployable, `deploy/README.md`), meeting the infra DoD in `agents/infrastructure.md` §7
- [ ] Documentation updated (`.ai/`, OpenAPI, READMEs)
- [ ] No open Critical/High bugs against the feature

## Directory ownership (conflict prevention)

| Path | Writer(s) |
|---|---|
| `backend/` | Backend, Fullstack (only when assigned) |
| `frontend/` (Vue PWA) | Frontend, Fullstack (only when assigned) |
| `mobile/` (Flutter, future) | Frontend, Fullstack (only when assigned) |
| `qa/` | QA |
| `deploy/`, `.github/`, root `Makefile`, root `.env.example` | Infrastructure |
| `backend/Makefile`, `backend/.env.example` | Backend (infra variables are added through the TL) |
| `docs/business/` | PM, and only after Product Owner approval |
| `.ai/business/`, `.ai/planning/`, `.ai/reports/pm/` | PM |
| `.ai/architecture/`, `.ai/reports/team-lead/` | TL |
| `.ai/tasks/**` | TL creates; the assignee updates Status, Activity Log and Completion Report; QA and PM append their own sections |
| `.ai/reports/qa/` | QA |
| `docs/standards/DRF_SKILL.md` | TL, and only with explicit approval |
| `docs/design/` | PM, and only after Product Owner approval |
| `.claude/skills/`, `.claude/agents/` | TL, and only with explicit user approval |

If a task needs a file outside its owner's area, the TL coordinates the change and records it in the task.

## Skills

Each agent preloads skills from `.claude/skills/`. They are short procedures with the real commands for its recurring jobs:

| Agent | Skills |
|---|---|
| All | `flash-workflow` (IDs, status + Activity Log, blockers, end-of-turn report) |
| PM | `pm-feature`, `pm-sprint`, `pm-acceptance` |
| TL | `tl-design-breakdown`, `tl-review`, `tl-bug-routing-signoff`, `drf-standard` |
| Backend | `backend-task`, `backend-state-money`, `drf-standard` |
| Frontend | `frontend-screen` |
| Fullstack | `fullstack-slice` + the Backend and Frontend skills |
| QA | `qa-test-plan`, `qa-verify` |
| Infrastructure | `infra-change`, `infra-deploy-verify` |

- Precedence: this README, `agents/*.md` and the ADRs win over a skill. Report any conflict to the TL.
- When a procedure here changes, update the matching skill in the same change.
- `drf-standard` is a copy of `docs/standards/DRF_SKILL.md`. Re-copy it after any change to the standard.
- How the built-in Claude Code skills (`/code-review`, `/security-review`, `/simplify`, `/run`, …) fit the workflow: see `CLAUDE.md` § Skills.

## Golden rule

PLAN → DESIGN → IMPLEMENT → REVIEW → TEST → FIX → VERIFY → RELEASE.
The team does not allow random coding, invented business rules, skipped reviews or QA,
uncontrolled large changes, unapproved architecture changes, or unverified DONE.
