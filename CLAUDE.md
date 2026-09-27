# Flash — Delivery Platform

Flash is a delivery platform with four roles: Customer, Store, Driver and Admin.
It is built by a controlled multi-agent team. **Read `.ai/README.md` before doing anything.**

## Sources of truth
- Business rules: `flash_business_logic/` (canonical). The agent digest is `.ai/business/business-logic.md`.
- Backend engineering standard: `DRF_SKILL.md` (mandatory for all backend work). Its deployment file locations are adapted by ADR-012 (repo-root `deploy/`).
- Architecture, ADRs and API contracts: `.ai/architecture/`.
- Plans and work: `.ai/planning/`, `.ai/tasks/`, `.ai/reports/`.

## The team (Claude Code subagents in `.claude/agents/`)
| Subagent | Instructions | Writes to |
|---|---|---|
| `project-manager` | `.ai/agents/project-manager.md` | `.ai/business`, `.ai/planning`, `.ai/reports/pm` |
| `team-lead` | `.ai/agents/team-lead.md` | `.ai/architecture`, `.ai/tasks`, `.ai/reports/team-lead` |
| `backend-developer` | `.ai/agents/backend.md` | `backend/` |
| `frontend-developer` | `.ai/agents/frontend.md` | `frontend/`, `mobile/` |
| `fullstack-developer` | `.ai/agents/fullstack.md` | only what TL assigns in `.ai/tasks/fullstack/` |
| `qa-engineer` | `.ai/agents/qa.md` | `qa/`, `.ai/reports/qa` |
| `infrastructure-engineer` | `.ai/agents/infrastructure.md` | `deploy/`, `.github/`, root `Makefile`, root `.env.example`, `.ai/reports/infrastructure` |

## Orchestration (main session)
The main session is the orchestrator. It does not do the agents' work itself. It calls them in workflow order and passes each one the relevant ID:

```
PM (feature, sprint) → TL (design, contracts, tasks) → [TL plan review]
→ Backend / Frontend / Fullstack / Infrastructure (implement) → TL (code review)
→ QA (verify) → bugs? → TL → developer → TL review → QA re-test
→ TL final sign-off → PM acceptance → DONE
```

- Start Infrastructure tasks at the beginning of the sprint, in parallel with development. They are not an end-of-sprint step.
- Independent tasks with non-overlapping scopes may run in parallel. Tasks that share files run in sequence (see the TL's technical plan).
- After each agent returns, check the status it set in the task file before calling the next agent.
- Never skip review or QA. Never mark DONE without QA PASS, TL sign-off and PM acceptance.

## Golden rules
- Do not invent business rules. A gap becomes a blocker in `.ai/planning/blockers/`.
- Do not make architectural changes without an ADR from the TL.
- Agents stay inside their directory ownership.
- PLAN → DESIGN → IMPLEMENT → REVIEW → TEST → FIX → VERIFY → RELEASE.

## Current state (update as it changes)
- 2026-09-27: Discovery done (`.ai/reports/pm/discovery-report.md`). Sprint 01 is planned and decomposed into TASK-001…011. No application code yet.
- 2026-09-27: Infrastructure agent added (ADR-012/013/014). TASK-006 is now Infrastructure's. TASK-011 (backend CI) is blocked on BLK-012.
- The runtime is Python 3.13 via uv on the server (ADR-016, which supersedes ADR-009). The local interpreter is 3.12, for building only.
- 2026-09-27: PO decisions: BLK-001 (username + password), BLK-002 (Vue 3 PWA) and BLK-011 are RESOLVED. BLK-012 is partial: git init done at `8b5dc17` on `main`, no remote, so CI is still blocked.
- Sprint-01 scope is now FEAT-001, FEAT-003 and FEAT-004 (deployment pulled forward).
- Target: shared VPS `hossam@34.123.215.195` (the dental-clinic app also runs there; never touch it), systemd mode, SQLite, no Redis/Docker, `api.delivery.hossam-ameen.online` + `delivery.hossam-ameen.online`, backend on `127.0.0.1:8010`.
- **QA runs on the server, never locally.** The local machine is for building only.
