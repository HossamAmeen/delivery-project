---
name: fullstack-slice
description: Flash Fullstack Developer procedure for a TL-assigned task in .ai/tasks/fullstack/ — contract first (DRAFT, TL approval), backend then frontend against the real API, contract-agreement tests on both sides, both validation gates, contract to ACTIVE, split Completion Report.
---

# Fullstack — contract-first vertical slice

Authority: `.ai/agents/fullstack.md`. You inherit **all** of the `backend-task`, `backend-state-money` and `frontend-screen` rules.

## Gate
- Only take tasks that are in `.ai/tasks/fullstack/` and that state the TL's reason for using Fullstack (contract will change / slice too small to split / cross-boundary bug). Anything else: refuse it and report it to the orchestrator for TL assignment.

## Procedure
1. `IN_PROGRESS`, then read everything the backend and frontend skills list.
2. **Contract first.**
   - Write or update the endpoint in `.ai/architecture/api-contracts.md`, marked `DRAFT (TASK-NNN)`: method, path, roles, request, envelope response, errors, 429, `allowed_transitions`.
   - Ask for TL approval in the task's `## Review Log`. **Build nothing before it is APPROVED.**
3. Build the backend: model → service → API → tests. Validate with `make test-backend-remote WORKTREE=1`.
4. Build the frontend against the **real** API shape. No mocks invented from scratch.
5. **Agreement tests:**
   - a backend API test that asserts the exact response shape the frontend consumes
   - frontend tests over recorded contract fixtures taken from that shape
6. Run both gates:
   - backend: `make test-backend-remote WORKTREE=1`
   - frontend: `cd frontend && npm run lint && npm run type-check && npm run test:unit && npm run build-only`
7. Change the contract marker to `ACTIVE`. In the Completion Report, list **Backend changes** and **Frontend changes** separately, with the commands and results for each. Set `READY_FOR_REVIEW`.

## Integration issues outside your task
Do not fix them. Note them for the TL, or raise a blocker.
