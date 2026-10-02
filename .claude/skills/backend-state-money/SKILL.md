---
name: backend-state-money
description: Flash backend patterns for the high-risk areas — order state transitions through transition_order (atomic, locked, history, on_commit notifications, idempotent, allowed_transitions), Decimal money and snapshots, immutable idempotent ledger entries, system-only assignment, audit, and the concurrency tests that prove them (with the SQLite/ADR-017 caveat).
---

# Backend — state, money, ledger, assignment

Authority: `.ai/agents/backend.md` §5, ADR-005/006, `architecture.md`. The business rules come from `docs/business/00_core/03…06,09` and `05_cross_app_flows/`. Cite the exact section in code comments or the task. Never invent a status, fee or transition.

## State transitions
- Use one entry point: `orders.services.transition_order(order_id, to_status, actor, payload, idempotency_key)`. Never change status through a generic serializer `update`, the admin, or `queryset.update()`.
- Inside the function, in this order:
  1. `transaction.atomic()`
  2. `select_for_update()` on the order
  3. guard the current state and the actor's role/relationship (authenticated → role → ownership → allowed transition → business constraints)
  4. validate the payload
  5. update the order
  6. write an `OrderStatusHistory` row (from, to, actor, timestamp, reason)
  7. trigger financial side effects
  8. schedule notifications with `transaction.on_commit(...)`
- **Idempotent:** a retry with the same `idempotency_key` returns the same result and creates no second history or ledger row.
- Status names live in **one enum** that is exposed in OpenAPI. Order responses include `allowed_transitions` computed **for the requesting actor**.

## Money
- Use `DecimalField` and `Decimal` only, never float. Store the currency explicitly. Serialize as strings.
- Snapshot order and item prices and fees when the order is created or confirmed. Never recompute them from the current catalog.

## Ledger
- Every balance-affecting event creates **one** entry with a reference/idempotency key that has a **DB unique constraint**. A duplicate insert is a no-op, not a second entry.
- Ledger rows are never updated or deleted. A correction is a new entry.

## Assignment
- The system assigns orders. There is **no** driver accept/reject endpoint.
- Reassignment keeps the assignment history rows.

## Notifications and audit
- Notifications go through `NotificationService`. A failed notification must never roll back the business transaction (`on_commit` plus catch and log).
- Status, assignment, financial, admin and catalog changes are auditable (who, what, when).

## Concurrency (ADR-017 caveat)
- The DB is SQLite with `transaction_mode=IMMEDIATE` and WAL. **`select_for_update()` is a no-op on SQLite.** Keep the call (it becomes effective on PostgreSQL), but do not rely on it alone. Lean on the IMMEDIATE write lock, unique constraints and idempotency keys.
- ADR-017's revisit trigger: before FEAT-009 (assignment concurrency) or the ledger (FEAT-011+), the TL must raise the PostgreSQL ADR. If your task is that work and no such ADR exists, raise a blocker to the TL.
- Required tests:
  - a duplicate request with the same idempotency key produces exactly one row
  - two competing transitions: one wins and the other gets a clean 409 or validation error, never a corrupted state
  - an invalid transition for each wrong actor or role is rejected
  - a notification failure leaves the transition committed
