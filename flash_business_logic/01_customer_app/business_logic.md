# Customer App Business Logic

## Main flow
Login/Register
-> Browse stores
-> Browse categories
-> Browse products
-> Build order
-> Confirm delivery address
-> Review total
-> Place order
-> Track order
-> Receive delivery
-> View history

## Customer order behavior
Customer can see:
- store
- items
- quantities
- prices
- subtotal
- delivery fee
- applicable discounts/fees
- final total
- order status
- driver information when assignment is available
- relevant collection/payment information

## Customer cannot
- manually assign a driver
- accept/reject driver assignment
- alter backend-calculated totals
- force an invalid status transition

## Cancellation
The app must show cancellation only when the current order state allows it.
The backend is authoritative.

## Tracking
The customer sees the current backend status and status history relevant
to the customer. Tracking is a projection of the shared order lifecycle.
