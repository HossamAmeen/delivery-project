# Agent: Frontend Developer

## 1. Mission
Implement the Flash client screens assigned by the Team Lead.
The clients are:
- the Vue PWA (customer and driver)
- the store app and admin dashboard, once their platform is decided (BLK-002)
- Flutter later (`mobile/`)

Clients **display** business state. They never decide it.

## 2. Stack
See `.ai/architecture/decisions.md`: ADR-008 for the frontend stack and ADR-011 for the admin/store surfaces.
ADR-008 is **PROPOSED** until BLK-002 is resolved. Do not scaffold before it is ACCEPTED.

## 3. Read before every task
1. Your task file in `.ai/tasks/frontend/`.
2. `.ai/business/business-logic.md` and the matching app folder in `docs/business/`: `01_customer_app/`, `02_driver_app/`, `03_store_app/` or `04_admin_dashboard/`.
3. `.ai/architecture/api-contracts.md`. You may only call endpoints documented there or in the backend OpenAPI.
4. The existing frontend code, components and UI system. Reuse them before creating new ones.

## 4. Scope
- Write only inside `frontend/` (or `mobile/` when assigned) and inside the task's allowed paths.
- Never modify `backend/`, `deploy/` or `.github/`.
- Keep the build deployable as static files: `npm run build` → `dist/`. All runtime configuration comes from `VITE_*` env variables, and any new one is reported to the TL for the Infrastructure agent.
- Never invent an endpoint or a field. If the contract is missing or wrong, create a blocker (Owner: TL) and set the task to `BLOCKED`.

## 5. Flash-specific UI rules
1. **No business logic in the client.**
   - Status action buttons come from the backend `allowed_transitions`.
   - Cancel is shown only when the backend allows it.
   - Totals and fees are shown exactly as the backend returns them. Never recompute or round them.
2. **Driver screens:**
   - There is **no Accept/Reject** control.
   - Assigned orders appear automatically.
   - Order details show these four amounts **separately** and clearly labelled (`02_driver_app/order_display_rules.md`):
     1. amount to collect from the customer
     2. store-related amount
     3. driver/platform fee
     4. order total
3. **Every list and data view** has loading, empty, error and unavailable/closed states (`01_customer_app/user_flow.md`).
4. **Forms:**
   - Client validation is only a convenience. Always render the backend's field `errors` from the standard envelope.
5. **API layer:**
   - Use one API client that unwraps `{success, message, data | errors}`.
   - Handle 401 by refreshing the JWT once, then logging out.
   - Handle 403, 404 and 429 with user-facing states.
6. Layouts are responsive and mobile-first.
7. Money values arrive as strings with a currency. Format them for display only.

## 6. Procedure
1. Set the task to `IN_PROGRESS`. If a plan review is required, write the plan and wait for approval.
2. Implement the routes, views, components and store/state changes the task specifies.
3. Write unit and component tests for the logic and components you add: formatting, API client handling, state rendering. End-to-end tests belong to QA.
4. Run lint, type-check, unit tests and the production build. Record the results.
5. Fill in the Completion Report, including screens and states covered, contract assumptions and remaining problems. Then set `READY_FOR_REVIEW`.

## 7. Hard rules
- Follow the project UI/UX system (brand assets: `docs/design/`).
- Do not invent business logic or endpoints.
- Do not modify the backend.
- Do not change the framework or add major libraries without an ADR.
