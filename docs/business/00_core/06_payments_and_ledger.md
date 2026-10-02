# Payments, Collection, and Ledger

## Payment concepts
Flash must distinguish:
1. Customer amount
2. Amount collected by driver
3. Amount due to/settled with store
4. Driver/platform fee
5. Refund/reversal
6. Ledger adjustment

## Cash collection
When an order requires cash collection:
- the order states the amount expected
- the driver sees the expected collection
- completion records the actual collected amount
- discrepancy handling is explicit

## Ledger
Every financial event should record:
- reference/order
- actor/account
- transaction type
- amount
- currency
- direction
- timestamp
- resulting balance when applicable
- idempotency/reference key

## Idempotency
A delivery completion or financial event must not create duplicate
ledger entries if the same request is retried.
