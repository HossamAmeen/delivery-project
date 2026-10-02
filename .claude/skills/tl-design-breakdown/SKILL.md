---
name: tl-design-breakdown
description: Flash Team Lead procedure after a PM handoff — write the FEAT design, record API contracts and ADRs before frontend work, decompose into ≤1-day single-agent TASK files with allowed paths, dependencies and plan-review flags, pick the right agent, and write the sprint technical plan with a file-ownership map.
---

# TL — design and breakdown

Authority: `.ai/agents/team-lead.md` §5.1, §5.2, §5.3 and §5.7.

## 1. Pre-checks
- Read the feature in `backlog.md`, its `Business refs`, and the code that exists today in the affected area. Never design blind.
- If any business rule is incomplete, raise a blocker for the PM (`flash-workflow` skill). Do not design around the gap.
- Look for existing capability before you add new work: `grep -rn "<capability>" .ai/tasks backend/apps frontend/src`.

## 2. Design → `.ai/reports/team-lead/FEAT-NNN-design.md`
Cover:
- affected Django apps and models
- state handling: transitions go only through `orders.services.transition_order()` (ADR-005/006, architecture.md)
- money: Decimal, currency, snapshots, ledger idempotency
- permissions: authenticated → role → ownership → transition → constraints
- endpoints
- frontend screens and their states
- deploy-time needs
- risks
- test strategy

Known constraint: the DB is SQLite (ADR-017), and `select_for_update` is a no-op on it. Before FEAT-009 (assignment concurrency) or ledger work (FEAT-011+), raise the PostgreSQL ADR.

## 3. Contracts and ADRs (before any frontend task starts)
- Add or update each endpoint in `.ai/architecture/api-contracts.md`:
  - method, path, auth/role, request, response inside the standard envelope, errors, 429, `allowed_transitions` where relevant
  - mark it `DRAFT (TASK-NNN)` until it is implemented
- Significant decisions become `ADR-NNN` entries in `decisions.md`, with Status, Context, Decision and Consequences.
- Major changes (DB, auth, API architecture, frontend framework, new infrastructure, deployment architecture) **require** an ADR.

## 4. Tasks → `.ai/tasks/<agent>/TASK-NNN-short-name.md` from `.ai/templates/task.md`
Each task has:
- one agent, one scope (allowed paths), about 1 day or less
- `Business Requirement` refs, and acceptance criteria traced to the FEAT's criteria
- dependencies in execution order
- `Plan Review Required: Yes` when the task:
  - touches state transitions, assignment, money/ledger or permissions
  - adds an app or model relationships
  - migrates existing data
  - changes a contract other clients use
  - is more than 1 day
  - is infrastructure work touching deployment, networking, security, CI, Nginx or systemd
- Status `TODO` and a creation line in the Activity Log

Agent choice:
- **Backend** owns `backend/`. **Frontend** owns `frontend/` and `mobile/`.
- **Fullstack** only when at least one of these is true, and the task states which:
  - the contract will change during the work
  - the slice is too small to split
  - it fixes a cross-boundary integration bug
- **QA**: at least one verification task per feature. The plan can start at once, without waiting for code.
- **Infrastructure**: any new env var, service, worker, port or static/media path. Schedule it at the sprint **start**.
- Never give two agents overlapping paths at the same time. Sequence them through dependencies instead.

## 5. Sprint technical plan → `.ai/reports/team-lead/sprint-NN-technical-plan.md`
Include:
- the task graph
- what can run in parallel and what must run in sequence
- the file-ownership map (path → TASK → agent)
- the order the orchestrator should call agents in

Finish with the `flash-workflow` end-of-turn report. The next step is usually Infrastructure plus the first unblocked developers, in parallel.
