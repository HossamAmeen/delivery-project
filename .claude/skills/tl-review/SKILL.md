---
name: tl-review
description: Flash Team Lead plan review and code review — run the validation yourself (make test-backend-remote for backend, npm lint/type-check/test/build for frontend, shellcheck/render/dry-run for infrastructure), walk the review.md checklist, and record APPROVED or CHANGES_REQUESTED in the task's Review Log with blocking findings as file:line.
---

# TL — plan review and code review

Authority: `.ai/agents/team-lead.md` §5.3–5.4. Use the template `.ai/templates/review.md`.

## Plan review (`## Implementation Plan` present, `Plan Review Required: Yes`)
- Check the plan against: the task scope, the business refs, the contract, the ADRs, and the Flash backend/frontend rules.
- Append `### Review — <date> — team-lead — plan` to `## Review Log`, with verdict APPROVED or CHANGES_REQUESTED. The developer must not code before APPROVED.
- For infrastructure, the plan is `.ai/reports/infrastructure/<FEAT>-infra-design.md`.

## Code review (`READY_FOR_REVIEW` → `REVIEW` → `READY_FOR_QA` | `IN_PROGRESS`)
1. Set the status to `REVIEW` and add an Activity Log line.
2. Read the Completion Report, then the **actual changes**:
   ```bash
   git status --short; git diff --stat; git diff -- <allowed paths>
   ```
   Any change outside the task's allowed paths is a blocking finding.
3. **Run the validation yourself.** A developer's pasted output is not enough.
   | Area | Commands |
   |---|---|
   | Backend | `make test-backend-remote WORKTREE=1` (or `REF=<sha>` once committed). This runs `ruff check`, `ruff format --check`, `manage.py check`, `makemigrations --check --dry-run` and `pytest --cov --cov-fail-under=80` on the server (ADR-018) |
   | Frontend | `cd frontend && npm run lint && npm run type-check && npm run test:unit && npm run build-only` |
   | Infrastructure | `bash -n` + `shellcheck` on changed scripts; `make render OUT=<scratch dir>`, then validate the rendered nginx/systemd; the scripts' `--dry-run` / `DRY_RUN=1`; read-only `make status` / `make health` |
4. Walk **every** checkbox in `review.md`. The ones to watch most closely:
   - authorization order: authenticated → role → ownership → transition → constraints
   - transitions only through the service, with history, idempotent
   - money as Decimal/string with currency, plus snapshots
   - ledger idempotency key with a unique constraint
   - no status changes through a generic serializer update
   - frontend computes nothing (it uses `allowed_transitions`, totals as returned, the 4 UI states, envelope `errors`)
   - migrations are expand/contract compatible with the previous release (ADR-013)
   - no hardcoded secrets, domains, ports or paths
5. Record `### Review — <date> — team-lead — code`:
   - verdict
   - the ticked checklist
   - findings as `[blocking|non-blocking] path:line — issue — required change`
   - the commands you ran, with their results
6. If there are any blocking findings: `IN_PROGRESS`. Otherwise: `READY_FOR_QA`. Add an Activity Log line either way.

## Do not
- Do not rewrite the developer's code. You may make a trivial fix only if you record it in the Review Log.
- Do not approve without running the validation yourself.
