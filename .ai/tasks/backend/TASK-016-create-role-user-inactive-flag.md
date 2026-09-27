# Task

## ID
TASK-016

## Title
`create_role_user --inactive` so `make seed-qa-users` can seed an inactive QA user

## Feature
FEAT-001 — Backend Platform Foundation (criterion 6: inactive user gets the same 401 `INVALID_CREDENTIALS`)

## Description
QA (TASK-008) needs a live inactive user, `qa_inactive`, to verify on the server that login by an inactive user returns the same 401 `INVALID_CREDENTIALS` body as a wrong password (api-contracts § Identity). `create_role_user` (TASK-003) cannot create or keep an inactive user today (no flag; `--update` never touches `is_active`). Add an `--inactive` flag with the same desired-state semantics as `--staff`.

## Business Requirement
REQ-010, REQ-011; api-contracts.md § Identity (APPROVED: "same response for unknown user, wrong password **and inactive user**"); FEAT-001 criterion 6; ADR-018 (`make seed-qa-users`)

## Agent
Backend

## Scope (allowed paths)
- `backend/apps/users/management/commands/create_role_user.py`
- `backend/apps/users/tests/test_commands.py`

## Dependencies
- TASK-003 reviewed (same file; start after the TL records the TASK-003 verdict so the two changes are not mixed in one review)
- Consumer: TASK-013 `seed-qa-users.sh` (seeds `qa_inactive`), TASK-014 (executes it)

## Acceptance Criteria

- [ ] `create_role_user --username U --role ROLE [--staff] [--superuser] [--inactive] [--update] [--password-stdin]`: without `--inactive` the user is active; with it `is_active=False`. With `--update` the flags are the desired state (omitting `--inactive` re-activates the user), like `--staff`.
- [ ] `--inactive` together with `--superuser` or `--staff` is refused (`CommandError`); an inactive QA user is a plain role user.
- [ ] The success line says `(inactive)` among the flags; the password is still never printed and never read from argv.
- [ ] Tests on the server via `make test-backend-remote WORKTREE=1`: create inactive, update active → inactive → active, refused combinations, output without password; total coverage stays ≥ 80%.

## Technical Notes

- No model or migration change (`is_active` is Django's field). No API change.
- `make seed-qa-users` (TASK-013) will call it as `create_role_user --username qa_inactive --role CUSTOMER --inactive --update --password-stdin` and write `QA_INACTIVE_USERNAME` / `QA_INACTIVE_PASSWORD` to `/srv/flash/qa/credentials.env`.

## Testing Requirements

- Command tests as listed in the criteria.

## Plan Review Required
No — small, fully specified change to an existing command

## Status

READY_FOR_RELEASE

## Activity Log
- 2026-09-27 | team-lead | — → TODO | created from QA TASK-008 request (qa_inactive for TC-001-JWT-07); small follow-up to TASK-003
- 2026-09-27 | backend | TODO → IN_PROGRESS | started; TASK-003 approved by the TL (committed 0a5f845)
- 2026-09-27 | backend | IN_PROGRESS → READY_FOR_REVIEW | `--inactive` added + 8 tests; server run 20260927-204538-13225 green (246 passed, coverage 98.43%)
- 2026-09-27 | team-lead | READY_FOR_REVIEW → REVIEW | code review started
- 2026-09-27 | team-lead | REVIEW → READY_FOR_QA | code review APPROVED; TL server run 20260927-204950-16782 (worktree): 246 passed, coverage 98.43%
- 2026-09-28 | qa | READY_FOR_QA → QA_IN_PROGRESS | FEAT-001 verification on the server started (TASK-009)
- 2026-09-28 | qa | QA_IN_PROGRESS → QA_IN_PROGRESS | QA verdict PASS ticked; status left for TL final review (.ai/reports/qa/FEAT-001-qa-report.md; server runs 20260927-225552-109762 (API regression), 20260927-225436-108557 (ratelimit), backend audit 20260927-225853-111545)
- 2026-09-28 | team-lead | QA_IN_PROGRESS → READY_FOR_RELEASE | TL final review signed off (QA PASS in .ai/reports/qa/FEAT-001-qa-report.md; no unreviewed changes)

## Implementation Plan
(not required)

## Completion Report
- Files changed: `backend/apps/users/management/commands/create_role_user.py` (new `--inactive` flag: `is_active = not inactive`, desired state on `--update` like `--staff`; `--inactive` with `--staff`/`--superuser` → `CommandError` before any DB write; success line lists `(inactive)`; help text updated), `backend/apps/users/tests/test_commands.py`.
- Tests added (8): active by default; create inactive via `--inactive --update --password-stdin` (the exact TASK-013 call) with `(inactive)` in the output and no password; update active → inactive → active; refused combinations `--staff`, `--superuser`, both (parametrized, no user created); refusal leaves an existing user untouched; the seeded inactive user gets 401 `INVALID_CREDENTIALS` on `/api/auth/token/`. The existing command tests are unchanged and still pass (the password is still never read from argv or printed).
- Validation commands run + results (server, `make test-backend-remote WORKTREE=1`, run `20260927-204538-13225`, Python 3.13.15, HEAD 0a5f845 + uncommitted worktree):
  ```
  ruff-check      PASS   (All checks passed!)
  ruff-format     PASS
  check           PASS
  makemigrations  PASS
  pytest          PASS   246 passed in 4.59s
  coverage        TOTAL 98.43% (gate 80%); create_role_user.py 100%
  == exit code: 0
  ```
  No local run (local static-check venv was not available; ruff/format were verified by the server run).
- Contract/OpenAPI changes: none (no model, migration or API change). Command contract for TASK-013: `create_role_user --username U --role ROLE [--staff] [--superuser] [--inactive] [--update] [--password-stdin]`.
- Known limitations / remaining problems: none.

## Review Log
(team-lead)

### Review — 2026-09-27 — team-lead — code

**Verdict:** APPROVED

**Checked:**
- [x] Scope: only `create_role_user.py` and `apps/users/tests/test_commands.py`; no model, migration or API change
- [x] Business rules: none invented (inactive = Django `is_active=False`, the contract's "inactive user" case)
- [x] Behaviour per the criteria: `--inactive` sets `is_active=False`; desired-state with `--update` (omitting it re-activates); refused with `--staff`/`--superuser` (`staff` already includes `--superuser`); `(inactive)` in the success line; password still only from stdin/env, never printed
- [x] Tests meaningful (+8); validation passes on the server; `makemigrations --check` clean
- [x] No secrets; DRF_SKILL-compliant; matches TASK-013's `seed-qa-users` detection (`create_role_user --help` contains `--inactive`)

**Findings:** none.

**Commands run:** `make test-backend-remote WORKTREE=1` (uncommitted worktree on top of `0a5f845`), run `20260927-204950-16782`, Python 3.13.15:
```
ruff-check PASS · ruff-format PASS · check PASS · makemigrations PASS
pytest PASS — 246 passed in 4.07s (238 + 8 new); coverage TOTAL 776 stmts, 7 miss → 98.43% (gate 80%)
== exit code: 0      make EXIT 0
```

### Review — 2026-09-28 — team-lead — final

**Verdict:** APPROVED — TL final sign-off.
- QA evidence exists: QA verdict PASS ticked, report `.ai/reports/qa/FEAT-001-qa-report.md` with server run ids.
- No unreviewed changes after the TL code review: backend/ (reviewed on the worktree, committed as f85848b; `git diff f85848b HEAD -- backend` empty).
- Contracts/OpenAPI/docs: as recorded in the code review (api-contracts and ADRs updated in the same session; OpenAPI validated by `spectacular --validate` in the server suite and by QA TC-001-DOC-01..08 where applicable).
- Open bugs against this task: none (BUG-001 is TASK-004, BUG-002 is TASK-013; both Low).

## QA Log
- 2026-09-28 | qa | PASS | .ai/reports/qa/FEAT-001-qa-report.md; server runs 20260927-225552-109762 (API regression), 20260927-225436-108557 (ratelimit), backend audit 20260927-225853-111545

## Sign-off
- TL final review: ☑ (team-lead, 2026-09-28)
- QA verdict: ☑ PASS (.ai/reports/qa/FEAT-001-qa-report.md; server runs 20260927-225552-109762 (API regression), 20260927-225436-108557 (ratelimit), backend audit 20260927-225853-111545)
- PM acceptance: ☐
