---
name: pm-feature
description: Flash Project Manager procedure for turning a business requirement into a backlog feature (FEAT) with business-level, testable acceptance criteria, "Work needed" lines, priority, and blockers for any missing rule. Also covers requirement change requests.
---

# PM — create a feature / handle a requirement change

Authority: `.ai/agents/project-manager.md` §5.1 and §5.6.

## Create a feature
1. **Rules check first.** For every behavior the feature needs, find the rule in `.ai/business/business-logic.md` and the cited `docs/business/` file. Write down the section references; they become `Business refs`.
   - If a rule is missing or ambiguous → raise a blocker (Owner: PM or Product Owner), per the `flash-workflow` skill. Do not fill the gap.
2. Allocate `FEAT-NNN` and append an entry to `.ai/planning/backlog.md` using `.ai/templates/feature.md`.
3. **Work needed** (all four, each with a reason when N/A):
   - Backend: Required / N/A (reason)
   - Frontend: Required / N/A (reason)
   - QA: always Required
   - Infrastructure: Required if anything new must be deployed, run or configured (env var, service, worker, port, static/media path, domain). Otherwise N/A (reason).
4. **Acceptance criteria** describe observable business behavior a QA engineer can verify from outside:
   - Good: "A driver cannot see another driver's order (403/404)."
   - Bad: "Add a permission class." (That is implementation.)
   - Cover each role in `00_core/02_roles_and_permissions.md` that touches the feature, both allowed and denied.
   - Cover money, state, and cancellation effects when relevant.
5. Priority: P0 = product cannot function without it · P1 = MVP · P2 = soon after MVP · P3 = later.
6. List `Dependencies` (FEAT/BLK) and `Open questions → BLK-NNN`.

## Requirement change
1. Log it in `.ai/business/requirements.md` → Change Log (what, why, requested by, date).
2. Ask the TL for technical impact (the TL answers in `.ai/reports/team-lead/`).
3. Only after **Product Owner approval**, update in this order:
   `docs/business/00_core/` → `05_cross_app_flows/` → app folders → `.ai/business/business-logic.md` → `requirements.md`.
4. Add an Activity Log line to each affected task, and tell QA which regression areas to re-test.

## Never
Never write code, choose libraries, design APIs or decompose into TASKs. Those belong to the TL.
