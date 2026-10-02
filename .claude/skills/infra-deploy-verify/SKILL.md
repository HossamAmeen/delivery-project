---
name: infra-deploy-verify
description: Flash Infrastructure procedure for a production release — pre-flight gates (CI/QA/TL/approval), dry runs, handing live make deploy/rollback/restart/migrate to the PO/operator, post-deploy verification with make status/health/logs and smoke QA, dental non-interference, and the deployment report with evidence.
---

# Infrastructure — release and verify a deployment

Authority: `.ai/agents/infrastructure.md` §5–8, ADR-013/015/017. Model the report on `.ai/reports/infrastructure/FEAT-004-deployment-report.md` and its `FEAT-004-deploy-logs/`.

## 1. Pre-flight (all of these, or there is no deploy)
- [ ] The release content has a TL-reviewed change and a QA PASS. Production also needs explicit PO approval
- [ ] The backend suite is green on the exact commit: `make test-backend-remote REF=<sha>`
- [ ] The working tree is clean (`git status --short`). A dirty tree needs `ALLOW_DIRTY=1` plus the PO's explicit OK
- [ ] Migrations in the release are backward-compatible with the current release (ADR-013). Note which ones apply
- [ ] Baseline captured:
  - `make status` (current release, `PREVIOUS`, disk, certificate)
  - `make health`
  - the dental URLs' status codes, for the non-interference comparison

## 2. Dry runs
```bash
make deploy DRY_RUN=1
make rollback DRY_RUN=1
```
Save the output to `.ai/reports/infrastructure/<FEAT>-deploy-logs/NN-*.txt`, with secrets redacted.

## 3. Live actions are the operator's
The permission policy denies agents `make deploy|rollback|restart|migrate|setup-server|tls` and remote user creation. **Do not try to work around this.**
Hand the PO the exact commands, in order, with what each one does and what to watch for, for example:
```
make deploy            # build → new release → backup + migrate → switch → restart → health (auto-rollback on failure)
make rollback [TO=<id>] [RESTORE_DB=auto|always|never]   # only if needed
```

## 4. Post-deploy verification (you run these)
```bash
make status            # new release ID and SHA, PREVIOUS set, MIGRATION_STATE
make health            # local + public HTTPS + web + unit + nginx -t
make logs LINES=200    # no tracebacks; workers up
make qa-remote ARGS="-m 'smoke or deploy'"   # or ask QA; dental non-interference included
```
- Compare dental's status codes with the baseline. Any change is a stop-the-line incident.
- If the health check fails, ask the operator to roll back immediately (`make rollback`), then verify again.

## 5. Report → `.ai/reports/infrastructure/<FEAT>-deployment-report.md`
Include:
- a timeline in UTC, with the actor for each step (**you** vs the **operator**)
- release ID and SHA, previous release, migration state, backup path
- every command with a link to its evidence file
- the health and smoke results
- the dental comparison
- the rollback readiness
- open issues

State plainly anything you did not observe yourself. Update the Activity Log of the affected tasks.
