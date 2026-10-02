# Audit and Concurrency

## Audit
Important actions should be auditable:
- order status changes
- assignment changes
- financial changes
- admin changes
- catalog changes
- cancellation/reversal

## Concurrency
Critical operations must be protected against race conditions:
- assignment
- order status transitions
- delivery completion
- financial ledger creation
- inventory/availability updates when implemented

## Idempotency
Retrying the same command must not produce duplicate business effects.

## Backend authority
The backend is the only authoritative source for:
- state
- assignment
- pricing
- fees
- financial totals
- permissions
