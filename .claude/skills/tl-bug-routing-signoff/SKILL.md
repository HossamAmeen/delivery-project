---
name: tl-bug-routing-signoff
description: Flash Team Lead procedure for QA_FAILED bug routing (confirm area, ASSIGNED, back to IN_PROGRESS, re-review before re-test) and for the final review after QA PASS (evidence exists, no unreviewed changes since review, contracts/OpenAPI/docs updated) that moves tasks to READY_FOR_RELEASE.
---

# TL — bug routing and final sign-off

Authority: `.ai/agents/team-lead.md` §5.5–5.6. Model the review on `.ai/reports/team-lead/sprint-01-final-review.md`.

## Route bugs (task is `QA_FAILED`)
1. Read each `BUG-NNN` that QA linked. Check that the violated rule really exists, and confirm or correct the `Suggested Area`.
   - If QA's expectation is not backed by any business rule, do not route the bug. Raise a blocker to the PM.
2. Set the bug `OPEN → ASSIGNED`. In the bug's Activity Log, name the developer agent and the task.
3. Set the task `QA_FAILED → IN_PROGRESS` and add an Activity Log line that links the bugs.
4. The fix then goes through the `tl-review` skill again before QA re-tests it (`READY_FOR_QA`).
5. `WONT_FIX` needs the PM and the TL together, with a written reason.

## Final review (QA ticked `QA verdict: PASS`)
Check each item and write down the file or commit that proves it:
- [ ] The QA report exists with PASS, and its evidence was produced by QA (look at `.ai/reports/qa/FEAT-NNN-qa-report.md`)
- [ ] All linked bugs are `VERIFIED`. No open Critical/High bugs remain
- [ ] **No unreviewed changes since your code review.** Compare the commit QA tested with the commit you reviewed, for example with `git log --oneline <reviewed-sha>..<qa-sha> -- <paths>`. Any new change goes back through review
- [ ] `api-contracts.md` matches the implementation and OpenAPI. Contracts that were `DRAFT (TASK-NNN)` are now `ACTIVE`
- [ ] Docs are updated: `.ai/`, READMEs, `deploy/README.md` if infrastructure changed
- [ ] Note any disclosures the PM must know about, such as steps the operator ran instead of QA

If every item passes:
1. Tick `TL final review` in `## Sign-off`.
2. Set the task to `READY_FOR_RELEASE` and add an Activity Log line.
3. Write or append `.ai/reports/team-lead/sprint-NN-final-review.md`.

The next agent is the PM (`pm-acceptance`).
