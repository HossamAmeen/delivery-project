---
name: flash-workflow
description: Shared Flash team mechanics used by every Flash subagent — allocating FEAT/TASK/BUG/BLK/ADR IDs, changing a task status with an Activity Log line, raising a blocker instead of inventing a rule, and the end-of-turn report to the orchestrator.
---

# Flash workflow mechanics

`.ai/README.md` is the authority. This skill is the quick procedure. If they disagree, the README wins. Report the disagreement.

## Allocate an ID
Run this every time before you create an ID. Never guess the next number.
```bash
grep -rhoE "TASK-[0-9]{3}" .ai qa | sort -u | tail -1   # swap TASK for FEAT / BUG / BLK / ADR / REQ
```
Use the next number. IDs are global, so do not restart numbering per agent or per sprint.

## Change a status
1. Check that the transition is yours to make (see the status table in `.ai/README.md`).
2. Edit `## Status` in the task file.
3. Append exactly one line to `## Activity Log`:
   `- YYYY-MM-DD | <agent> | <OLD> → <NEW> | <one-line reason / link>`
   Use today's real date.

Never skip a stage: IMPLEMENT → REVIEW → QA → TL sign-off → PM acceptance.

## Raise a blocker (missing or conflicting business rule, access, decision)
1. Allocate `BLK-NNN`, copy `.ai/templates/blocker.md` to `.ai/planning/blockers/BLK-NNN-short-name.md`.
2. Fill Description, Why It Blocks, Options (do **not** pick one if it is a business decision), Required Decision, Owner (PM / Team Lead / Product Owner).
3. Set the affected task to `BLOCKED`, linking the BLK in the Activity Log.
4. Continue only with parts that are unblocked **and** that the TL agreed to.

## Stay in your lane
- Write only to the paths your agent owns (`.ai/README.md` § Directory ownership) and the task's `Scope (allowed paths)`.
- Communicate only through files. Chat, memory and "I assumed…" are not handoffs.
- Runtime facts (ADR-015…018):
  - QA suites and backend tests run **on the server** (`make qa-remote`, `make test-backend-remote`). The local machine only builds.
  - Live production actions (`make deploy/rollback/restart/migrate`, remote user creation) are run by the **PO/operator**. You prepare and verify; you do not work around a permission denial.
  - Never touch the dental-clinic app on the shared VPS.

## End-of-turn report (always)
- Changed files (paths)
- Statuses set (ID: OLD → NEW)
- Validation run and its result (commands + pass/fail counts)
- Open problems and blockers (IDs)
- The next agent the workflow calls for
