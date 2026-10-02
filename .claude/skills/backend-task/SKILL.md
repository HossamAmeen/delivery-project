---
name: backend-task
description: Flash Backend Developer procedure for implementing an assigned TASK in backend/ with Django REST Framework — read-first list, layer order (model → migration → service/selector → serializer → view → URL → permission → tests → OpenAPI), required test matrix, server-side validation via make test-backend-remote, contract update and Completion Report.
---

# Backend — implement a TASK

Authority: `.ai/agents/backend.md` and `docs/standards/DRF_SKILL.md` (mandatory). ADR-012 and ADR-015…019 adapt the DRF_SKILL deployment, database and cache parts. For any work on state, money, ledger, assignment or concurrency, also use the `backend-state-money` skill.

## 0. Before coding
- Read:
  - the task file
  - its business refs (`.ai/business/business-logic.md` and the cited `docs/business/` sections)
  - `architecture.md`, `api-contracts.md` and `decisions.md`
  - the existing app code and tests (`backend/apps/<app>/`, `backend/common/`, `backend/tests/`)
- Dependencies must be `READY_FOR_QA` or later. Otherwise you are `BLOCKED`.
- Set the task to `IN_PROGRESS` and add an Activity Log line.
- If `Plan Review Required: Yes`, write `## Implementation Plan` first: files, models/migrations, service functions, endpoints, tests and risks. **Stop until the TL marks it APPROVED.**

## 1. Build in this order (DRF_SKILL §56)
1. Model, on `common` BaseModel / soft-delete managers where they apply
2. Migration. It must be expand → contract compatible with the previous release, because rollback never reverses migrations (ADR-013). Never make a destructive migration without explicit approval
3. Service and selector. Business logic lives here, never in views or serializers
4. Serializer. Money is serialized as a string
5. View or ViewSet, using the standard envelope `{success, message, data | errors}` and the throttle scopes
6. URL
7. Permission classes plus queryset scoping. Another user's object must be 404/403, never retrievable
8. Tests
9. OpenAPI (drf-spectacular annotations, with 429 documented)

Never hardcode secrets, domains, ports or paths; they come from env. If you add an env var, put it in `backend/.env.example` **and** tell the TL, so an Infrastructure task is created.

## 2. Test matrix (only the rows that apply)
| Layer | Must cover |
|---|---|
| Models/managers | constraints, soft delete, default managers |
| Serializers | valid input, each invalid field |
| APIs | unauthenticated (401), wrong role (403), not owner (403/404), success, validation errors in the envelope, 404, pagination, throttling (429) |
| Services | happy path, each business rule, failures, edge cases, idempotency on retry, concurrency |

## 3. Validate (on the server; the local machine only builds)
```bash
make test-backend-remote WORKTREE=1      # or: cd backend && make test-remote
```
This runs `ruff check`, `ruff format --check`, `manage.py check`, `makemigrations --check --dry-run` and `pytest --cov --cov-fail-under=80`. All of them must pass. Results land in `backend/.remote-results/latest/`.

## 4. Finish
- If the implementation refines a contract, update `api-contracts.md`. If it changes the contract beyond a refinement, ask the TL first.
- Fill in `## Completion Report`:
  - files changed
  - tests added
  - the validation commands with their summarized results (pass counts, coverage %)
  - contract and OpenAPI changes
  - known limitations
- Set `READY_FOR_REVIEW` and add an Activity Log line. Next agent: the TL (`tl-review`).
