# Task

## ID
TASK-008

## Title
QA test strategy, Sprint-1 test plan & black-box harness

## Feature
FEAT-001 — Backend Platform Foundation

## Description
Create the QA foundation: overall strategy, FEAT-001 test plan with traceability, and the `qa/` pytest + httpx harness that runs against a running backend (ADR-007).

## Business Requirement
REQ-002, REQ-006; `05_cross_app_flows/06_qa_contract.md`; FEAT-001 criteria 1–10

## Agent
QA

## Scope (allowed paths)
- `qa/**`

## Dependencies
- none to start (plan from contracts); harness execution needs TASK-006

## Acceptance Criteria

- [ ] `qa/plans/test-strategy.md`: levels, locations, environments, data strategy, regression policy, severity rules, evidence rules, cross-client consistency approach for the 15 QA-contract scenarios.
- [ ] `qa/plans/FEAT-001-test-plan.md`: test cases traced to FEAT-001 criteria 1–10 (ID, preconditions, steps, expected, level, priority).
- [ ] `qa/` harness: `pyproject`/requirements, `conftest.py` with base URL + credentials from env (`QA_BASE_URL`, `QA_HEALTH_TOKEN`, …), envelope assertion helpers, markers `smoke`, `regression`, `security`, `ratelimit`.
- [ ] `qa/README.md`: how to run against local Docker.

## Technical Notes

- Never import backend code; HTTP only.
- Rate-limit tests must use a backend started with low test limits (document the env to use).

## Testing Requirements

- The harness self-test: a smoke test against `/api/health/` that passes on a healthy backend.

## Plan Review Required
No

## Status

TODO

## Activity Log
- 2026-09-27 | team-lead | — → TODO | created from sprint-01 technical plan

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

## QA Log

## Sign-off
- TL final review: ☐
- QA verdict: ☐
- PM acceptance: ☐
