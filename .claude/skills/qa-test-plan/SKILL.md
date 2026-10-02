---
name: qa-test-plan
description: Flash QA procedure for writing a feature test plan (qa/plans/FEAT-NNN-test-plan.md) traced to acceptance criteria and 06_qa_contract.md, with per-role positive/negative permission cases, and for adding black-box pytest+httpx / Playwright tests in qa/ using the existing harness and markers.
---

# QA — test plan and tests

Authority: `.ai/agents/qa.md`, `qa/README.md`, `qa/plans/test-strategy.md`, and ADR-007/018. Start as soon as the TL creates your QA task. You do not need to wait for code.

## Plan → `qa/plans/FEAT-NNN-test-plan.md` (model it on the existing FEAT-001/003/004 plans)
1. Read:
   - the feature's acceptance criteria (in `backlog.md` and the sprint file)
   - `business-logic.md` and the cited sections
   - `docs/business/05_cross_app_flows/06_qa_contract.md`
   - `api-contracts.md`
   - the implementation tasks' Completion Reports
2. **Traceability table:** each AC and each relevant `06_qa_contract.md` item maps to ≥1 test case ID (`TC-NNN-<AREA>-NN`).
3. **Case table:** ID | preconditions | steps | expected result | level (api / flow / e2e / smoke / deploy) | priority | marker.
4. **Permissions:** every role in `00_core/02_roles_and_permissions.md` gets a **positive and a negative** case for each endpoint. Never skip these.
5. Also cover, where relevant:
   - validation, and the error envelope shape
   - 404
   - 429 (marked `ratelimit`)
   - idempotency (duplicate request)
   - concurrency
   - state transitions, both allowed and forbidden per actor
   - money values: string + currency, exactly as the business rule says
6. Data setup: the seeded QA users (`qa_customer`, `qa_driver`, `qa_store`, `qa_admin` via `make seed-qa-users`) plus any data the cases need, and how you create it through the API.

## Tests (black-box; never import backend or frontend code)
| Level | Location |
|---|---|
| API contract | `qa/api/test_*.py` |
| Multi-actor flows | `qa/api/flows/` |
| PWA E2E (Playwright, Chromium) | `qa/e2e/` |
| Post-deploy smoke/runtime | `qa/smoke/` |

- Reuse `qa/harness/` (`config`, `http`, `envelope`, `pwa`, `secrets`) and `qa/conftest.py` fixtures.
- Markers are strict: `smoke`, `regression`, `security`, `ratelimit`, `deploy`, `e2e`. Add `regression` to anything that should run on every release.
- Follow the rules in `qa/README.md`:
  - one login per role per session
  - `/api/auth/*` calls are paced by `AuthPacer`
  - never retry a 429
  - never print secrets or bodies
- Local syntax check only: `pytest --collect-only` in a scratch venv, or `make qa-remote ARGS="--collect-only -q"`. **Never run the suite locally.**
- Do not weaken an expected result because the implementation disagrees. If the rule itself is unclear, raise a blocker to the PM.
