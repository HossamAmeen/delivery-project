---
name: qa-verify
description: Flash QA verification on the server — QA_IN_PROGRESS, run the plan and full regression via make qa-remote against the deployed HTTPS URLs, audit the developer suite with make test-backend-remote, write the FEAT QA report with own evidence and PASS/FAIL, file BUG reports, re-test fixes, and tick the QA verdict.
---

# QA — verify, report, bugs, re-test

Authority: `.ai/agents/qa.md` §5, ADR-018. **QA runs on the server, never locally.** Model the report on `.ai/reports/qa/FEAT-004-qa-report.md`.

## Verify (implementation tasks are `READY_FOR_QA`)
1. Set each task to `QA_IN_PROGRESS` and add an Activity Log line.
2. Record the environment:
   - `make status`: release ID and git SHA under test
   - `make health`
3. Run, in this order (results land in `qa/.results/latest/`):
   ```bash
   make qa-remote ARGS="--collect-only -q"
   make qa-remote ARGS="-m 'smoke or deploy'"
   make qa-remote ARGS="<the feature's new tests, e.g. -k FEAT-NNN or the file paths>"
   make qa-remote ARGS="-m 'regression and not e2e'"   # full regression
   make qa-remote ARGS="-m e2e"                        # when the feature has a UI
   make test-backend-remote REF=<deployed sha>         # audit of the developer suite; not your verification
   make throttle-reset && make qa-remote ARGS="-m ratelimit"; make throttle-reset   # always LAST
   ```
4. Then test exploratory edge cases by hand. Record each request (method, path, status) as evidence.
5. If you are denied a live action (`deploy`, `rollback`, `restart`, `migrate`), do **not** work around it. Ask the operator to run it. Then verify the outcome from the server's records (`make status`, `make logs`, release metadata), and **disclose this** in the report.

## Report → `.ai/reports/qa/FEAT-NNN-qa-report.md`
Include:
- the verdict (**PASS / FAIL**) at the top
- scope: the tasks verified and the plan link
- the environment table: server, release, SHA, runners
- for each case: PASS / FAIL / SKIP (with the reason)
- the commands you ran and their summarized output (collected/passed/failed/deselected counts, run IDs)
- bugs
- coverage gaps
- disclosures

A PASS requires evidence **you** produced. A developer's claim or a developer's tests never count.

## Bugs
For each failure:
1. Allocate `BUG-NNN` and create `.ai/reports/qa/bugs/BUG-NNN-short.md` from `.ai/templates/bug-report.md`. Include:
   - the business rule violated
   - exact reproduction steps
   - expected vs actual result
   - environment (release/SHA)
   - evidence
   - severity (see the template's definitions)
   - Suggested Area. A deployment defect has Suggested Area `Infrastructure`
2. Set the task to `QA_FAILED`. The TL routes it.

## Re-test (the fixed task is back at `READY_FOR_QA`)
1. Re-run the failing cases plus the full regression.
2. Mark each bug `VERIFIED` or `REOPENED`, with evidence and an Activity Log line.

## PASS
1. In each task, tick `QA verdict: PASS (<report link>)` in `## Sign-off` and add an Activity Log line.
2. **Leave the status as it is.** The TL's final review moves it to `READY_FOR_RELEASE`.

Never edit `backend/`, `frontend/`, `mobile/`, `deploy/` or `.github/`.
