---
name: pm-acceptance
description: Flash Project Manager acceptance gate — verify a feature against the feature-level Definition of Done (all tasks READY_FOR_RELEASE, QA PASS with evidence, TL final sign-off, no open Critical/High bugs, criteria traced to QA cases) before setting tasks and the feature to DONE.
---

# PM — accept a feature

Authority: `.ai/agents/project-manager.md` §5.5 and the Definition of Done in `.ai/README.md`. Model the report on `.ai/reports/pm/sprint-01-acceptance-2026-09-28.md`.

## Gate (every item needs a file you actually opened)
| Check | Where to look |
|---|---|
| Every task of the feature is `READY_FOR_RELEASE` | `## Status` in each `.ai/tasks/**/TASK-*.md` with `## Feature` = this FEAT |
| QA verdict **PASS** with evidence QA produced itself | `.ai/reports/qa/FEAT-NNN-qa-report.md` |
| Each acceptance criterion maps to ≥1 QA test case | traceability table in `qa/plans/FEAT-NNN-test-plan.md` / QA report |
| TL final review ticked | `## Sign-off` in each task + `.ai/reports/team-lead/` |
| No open Critical/High bugs | `grep -l "FEAT-NNN" .ai/reports/qa/bugs/*.md`, then check each one's Severity and Status |
| Contracts/OpenAPI/docs updated | the TL final review states it |
| Infrastructure DoD met, if Infrastructure work was Required | `.ai/agents/infrastructure.md` §7 + `.ai/reports/infrastructure/` |
| Any disclosures (for example, steps the operator ran instead of QA) are acknowledged | QA report, TL review |

## If everything passes
1. In each task: tick `PM acceptance`, set `READY_FOR_RELEASE → DONE`, and add an Activity Log line.
2. In `backlog.md`: set the feature to `DONE`.
3. Write `.ai/reports/pm/sprint-NN-acceptance-YYYY-MM-DD.md` (or append to it). For each gate item, give the file that proves it.
4. Update the sprint board and the exit-criteria result.

## If anything fails
Do **not** accept. Write the missing item in the affected task's Activity Log (status unchanged) and name the agent who must act.
