# Flash — Unified Business Logic

## Purpose
This folder is the single source of truth for Flash business behavior.

The same business rules must be respected by:
- Backend / Django REST Framework
- Customer App
- Driver App
- Store App
- Admin Dashboard
- Vue PWA
- Flutter App
- QA automation
- Product/design documents

## Architecture principle
`00_core/` defines shared business rules.
Each app folder describes how that app exposes the same rules.

No client is allowed to invent a different order state, fee calculation,
assignment rule, permission, or financial behavior.

## Product surfaces
1. Customer
2. Driver
3. Store
4. Admin

The Vue PWA and Flutter application support the customer and driver roles
with the same underlying business rules.

MVP client platform (Product Owner decision, 2026-09-27, BLK-002):
the Vue 3 PWA is the MVP web client. The Flutter application comes after the MVP.

## Critical confirmed rule
A driver does NOT manually accept or reject an order.
The system assigns the order to the driver. The assigned order then appears
in the driver's workload.

## Change management
When a business rule changes:
1. Update `00_core/`.
2. Update affected cross-app flows.
3. Update affected app behavior.
4. Update API/OpenAPI contracts.
5. Update automated tests.
6. Update the relevant product/UX documentation.
