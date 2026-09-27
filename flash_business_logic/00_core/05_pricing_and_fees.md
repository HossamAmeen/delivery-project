# Pricing, Fees, and Money Rules

## Money principles
- Never use floating point for financial calculations.
- Use Decimal on the backend.
- Persist currency explicitly.
- Persist calculated monetary snapshots on the order.
- Do not recalculate historical order totals from current catalog prices.

## Order total
Recommended components:

subtotal
+ delivery_fee
+ applicable platform/store/customer fees
- applicable discounts
= customer_total

The final structure is configurable and must be defined centrally.

## Driver/store financial relationship
A confirmed product requirement is that:
- the driver has an amount/fee payable to the store according to the business model
- the driver may also collect money from the customer

These amounts must be visible wherever operationally required,
especially in the driver order details and relevant admin/store views.

## Financial snapshots
At order creation/confirmation, store:
- item price snapshot
- quantity
- line total
- subtotal
- delivery fee
- discounts
- customer total
- store-related amount
- driver-related fee/amount
- currency

## Ledger principle
Any money movement that affects a balance must create a ledger entry.
Balances should be derived/reconciled from ledger records rather than being
silently mutated without an audit trail.

## No hidden calculation
The UI may display a calculation, but the backend remains authoritative.
