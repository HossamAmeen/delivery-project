---
name: pm-sprint
description: Flash Project Manager procedure for planning a sprint file (sprint-NN.md with goal, scope, out-of-scope, blockers, risks, exit criteria, TL handoff) and for tracking progress each session by rebuilding the sprint board from task statuses and chasing blockers.
---

# PM — plan and track a sprint

Authority: `.ai/agents/project-manager.md` §5.2–5.4. Model the file on `.ai/planning/sprints/sprint-01.md`.

## Plan `sprint-NN`
1. Create `.ai/planning/sprints/sprint-NN.md` with these sections:
   - Sprint goal (one sentence)
   - Dates
   - PO decisions driving this plan (if any)
   - In scope: features with their acceptance criteria
   - Explicitly out of scope
   - Dependencies & blockers
   - Risks
   - Exit criteria
   - Handoff to Team Lead
   - Sprint board
   - Change log
2. Admit a feature only if its rules are defined, or if its blockers are expected to be resolved before the dependent task starts. Write that expectation down, with the BLK ID.
3. Put any Infrastructure work at the **start** of the sprint, not the end.
4. Move the in-scope features to `TODO` in `backlog.md`.
5. Fill in **Handoff to Team Lead**: features, priorities, known constraints, the order you want. Do not create TASKs.
6. Update the "Current state" bullets in `CLAUDE.md` only if the orchestrator asks you to. Otherwise put the update in your report.

## Track (every session)
1. Rebuild the **Sprint board** table from the `## Status` of every task:
   ```bash
   for f in .ai/tasks/*/TASK-*.md; do printf '%s\t' "$(basename "$f" .md)"; awk '/^## Status/{getline; while($0==""){getline}; print; exit}' "$f"; done
   ```
2. For every `BLOCKED` task, make sure a BLK exists with an owner. Resolve business blockers, or escalate them to the PO.
3. Watch for dependency risks:
   - a frontend task starting before its contract exists in `api-contracts.md`
   - QA with nothing to test
   - Infrastructure starting late
4. If something changed materially, write `.ai/reports/pm/sprint-NN-status-YYYY-MM-DD.md`.
5. A scope change goes in the sprint file's **Change log** with a reason. Never change scope silently.

## Resolve a blocker
1. Fill in `## Resolution`: the decision, who decided and the date.
2. Update the source-of-truth documents it touches.
3. Set the blocker to `RESOLVED`.
4. Add a line to the Activity Log of each affected task.
