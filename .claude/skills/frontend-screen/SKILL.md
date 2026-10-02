---
name: frontend-screen
description: Flash Frontend Developer procedure for implementing an assigned screen/route in the Vue 3 + Pinia PWA (frontend/) — contract-only endpoints, no client business logic (allowed_transitions, backend totals), the four UI states, envelope errors, driver money display, VITE_* config, unit tests, and the lint/type-check/test/build gate.
---

# Frontend — implement a screen

Authority: `.ai/agents/frontend.md`. Stack: Vue 3 + Pinia + vue-router + Vitest, PWA (BLK-002 resolved, ADR-008/011).

## 0. Before coding
- Read:
  - the task
  - the matching app folder in `docs/business/` (`01_customer_app/`, `02_driver_app/`, `03_store_app/` or `04_admin_dashboard/`)
  - `.ai/architecture/api-contracts.md`
- You may only call endpoints documented in `api-contracts.md`. If an endpoint or field is missing or wrong, raise a blocker (Owner: TL) and set `BLOCKED`. Never invent an endpoint or field.
- Reuse what already exists before creating anything:
  - `src/api/client.ts` (envelope unwrap, JWT refresh), `src/api/errors.ts`
  - `src/components/state/{Loading,Empty,Error,Unavailable}State.vue`
  - `src/components/RoleAreaShell.vue`, `src/app/roles.ts`
  - `src/i18n/` (all copy goes through i18n), `src/stores/`, `src/config/env.ts`
- Set `IN_PROGRESS`. If `Plan Review Required: Yes`, write the plan and wait for APPROVED.

## 1. Rules every screen follows
- **No business logic.**
  - Action buttons come only from the backend's `allowed_transitions`.
  - Cancel is shown only when the backend allows it.
  - Totals and fees are displayed exactly as returned, never recomputed or re-rounded. Money arrives as strings with a currency; format it for display only.
- **Driver screens:**
  - no Accept/Reject control; assigned orders appear automatically
  - order details show **four separately labelled amounts** (`02_driver_app/order_display_rules.md`):
    1. to collect from the customer
    2. store-related amount
    3. driver/platform fee
    4. order total
- **Every list and data view** has loading, empty, error and unavailable/closed states.
- **Forms:** client validation is a convenience only. Always render the backend's field `errors` from the envelope.
- **Errors:**
  - 401: refresh once, then log out (the client already does this)
  - 403, 404 and 429 each get a user-facing state
- Layouts are mobile-first and responsive. Use the brand assets from `docs/design/`.
- Runtime config comes only from `VITE_*` variables (via `src/config/env.ts`). Report any new variable to the TL so Infrastructure is told.
- No new framework or major library without an ADR.

## 2. Tests (`__tests__/` next to the code; E2E belongs to QA)
Cover:
- formatting
- API client handling
- each UI state rendering
- buttons that are driven by `allowed_transitions`
- rendering of envelope errors

## 3. Validate (local build gate, allowed by ADR-018)
```bash
cd frontend && npm run lint && npm run type-check && npm run test:unit && npm run build-only
```

## 4. Finish
Fill in the Completion Report:
- the screens and states covered
- the endpoints used, and any contract assumptions
- the commands you ran, with their results
- remaining problems

Then set `READY_FOR_REVIEW`. Never touch `backend/`, `deploy/` or `.github/`.
