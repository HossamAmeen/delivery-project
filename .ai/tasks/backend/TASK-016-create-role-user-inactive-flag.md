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

TODO

## Activity Log
- 2026-09-27 | team-lead | — → TODO | created from QA TASK-008 request (qa_inactive for TC-001-JWT-07); small follow-up to TASK-003

## Implementation Plan
(not required)

## Completion Report
(assignee, when moving to READY_FOR_REVIEW)
- Files changed:
- Tests added:
- Validation commands run + results:
- Contract/OpenAPI changes:
- Known limitations / remaining problems:

## Review Log
(team-lead)

## QA Log

## Sign-off
- TL final review: ☐
- QA verdict: ☐
- PM acceptance: ☐
