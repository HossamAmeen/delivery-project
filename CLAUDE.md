# Flash — Delivery Platform

Flash is a delivery platform with four roles: Customer, Store, Driver and Admin.
It is built by a controlled multi-agent team. **Read `.ai/README.md` before doing anything.**

## Project layout
```
docs/                    ← what we build (read-only for code agents)
├── business/            ← canonical business rules (PO-approved; PM edits)
├── design/              ← brand assets: logo, brand notes
└── standards/           ← engineering standards (DRF_SKILL.md)
backend/  frontend/      ← application code (Backend / Frontend / Fullstack)
qa/                      ← black-box QA suite (QA)
deploy/  Makefile  .env.example  .github/   ← infrastructure (Infrastructure)
.ai/                     ← team operating system: plans, architecture, tasks, reports
.claude/agents/          ← the subagents
.claude/skills/          ← project skills (procedures the agents load)
```
The code and infra paths are deliberately unchanged, because the deploy tooling and the live server depend on them.

## Sources of truth
- Business rules: `docs/business/` (canonical). The agent digest is `.ai/business/business-logic.md`.
- Brand and design: `docs/design/`. The frontend's icons are generated from it (`frontend/scripts/generate_icons.py`).
- Backend engineering standard: `docs/standards/DRF_SKILL.md` (mandatory for all backend work). Its deployment file locations are adapted by ADR-012 (repo-root `deploy/`).
- Architecture, ADRs and API contracts: `.ai/architecture/`.
- Plans and work: `.ai/planning/`, `.ai/tasks/`, `.ai/reports/`.

## The team (Claude Code subagents in `.claude/agents/`)
| Subagent | Instructions | Preloaded skills | Writes to |
|---|---|---|---|
| `project-manager` | `.ai/agents/project-manager.md` | `pm-feature`, `pm-sprint`, `pm-acceptance` | `.ai/business`, `.ai/planning`, `.ai/reports/pm`, `docs/business` (after PO approval) |
| `team-lead` | `.ai/agents/team-lead.md` | `tl-design-breakdown`, `tl-review`, `tl-bug-routing-signoff`, `drf-standard` | `.ai/architecture`, `.ai/tasks`, `.ai/reports/team-lead` |
| `backend-developer` | `.ai/agents/backend.md` | `backend-task`, `backend-state-money`, `drf-standard` | `backend/` |
| `frontend-developer` | `.ai/agents/frontend.md` | `frontend-screen` | `frontend/`, `mobile/` |
| `fullstack-developer` | `.ai/agents/fullstack.md` | `fullstack-slice`, plus the backend and frontend skills | only what TL assigns in `.ai/tasks/fullstack/` |
| `qa-engineer` | `.ai/agents/qa.md` | `qa-test-plan`, `qa-verify` | `qa/`, `.ai/reports/qa` |
| `infrastructure-engineer` | `.ai/agents/infrastructure.md` | `infra-change`, `infra-deploy-verify` | `deploy/`, `.github/`, root `Makefile`, root `.env.example`, `.ai/reports/infrastructure` |

Every agent also preloads `flash-workflow`: ID allocation, status changes with Activity Log lines, blockers and the end-of-turn report.

## Skills

### Project skills (`.claude/skills/`)
- Each skill is a short, step-by-step procedure with the real commands for one recurring job. They are attached to agents with the `skills:` field in `.claude/agents/*.md` and load when the agent starts.
- Precedence: the agent instruction file (`.ai/agents/*.md`) and the ADRs win over a skill. An agent that finds a conflict reports it.
- `drf-standard` is a verbatim copy of `docs/standards/DRF_SKILL.md` under a header listing the Flash ADR deviations. The `docs/` file is canonical. After any change to it, re-copy the body into the skill.
- The TL maintains the skills, and changes need the user's approval (the same rule as `DRF_SKILL.md`). When a procedure in `.ai/agents/*.md` changes, update the matching skill in the same change.
- The main session must not use a role skill to do an agent's work itself. It calls the agent.

### Built-in Claude Code skills (general)
| Skill | Use in Flash | Not for |
|---|---|---|
| `/code-review` | An extra pass on a diff before or alongside the TL review. Findings go to the TL, who records them in the task's Review Log. | Replacing the TL review or its validation commands |
| `/security-review` | Before release of anything that touches auth, permissions, money/ledger, secrets or deploy tooling. File the findings as bugs or TL review findings. | Replacing QA permission tests |
| `/simplify` | Cleanup of a developer's own changes before `READY_FOR_REVIEW`, inside the task's allowed paths only. | Changing behaviour or contracts |
| `/run` | Local preview of the PWA build (the local machine is for building only). | QA evidence. QA runs on the server only (ADR-018). |
| `/update-config`, `/fewer-permission-prompts` | Permission and hook settings in `.claude/settings*.json`. The user approves them. | Granting agents live production actions |
| `/loop`, `/schedule` | Polling or scheduled read-only checks (for example `make status` / `make health`). | Live deploys, rollbacks or migrations |

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
- 2026-09-28: **Sprint-01 CLOSED.** FEAT-001, FEAT-003 and FEAT-004 are DONE, live at release `20260927-232246` / `d6669b6` (https://delivery.hossam-ameen.online, https://api.delivery.hossam-ameen.online). Sprint-02 (`.ai/planning/sprints/sprint-02.md`) is a DRAFT waiting on BLK-007 from the PO.
- Permission note: the auto-mode classifier denies agents live production actions (`make deploy/rollback/restart/migrate`, remote user creation) even with allow rules, so the PO runs those. The agents can run the server tests (`make test-backend-remote`, `make qa-remote`) and the read-only ops.
- 2026-10-02: Docs reorganized under `docs/` (`business/` ← `flash_business_logic/`, `design/` ← `06_brand/`, `standards/` ← `DRF_SKILL.md`). All references were updated. Code and infra paths are unchanged. Project skills were added in `.claude/skills/` and attached to every agent.
