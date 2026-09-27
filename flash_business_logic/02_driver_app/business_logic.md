# Driver App Business Logic

## Main screen
The driver sees assigned/active delivery orders.

There is NO Accept/Reject action for an assigned order.

## Order card/details must expose
- order identifier
- store
- customer delivery information required for execution
- order items/summary as needed
- amount to collect from customer
- amount/fee due to store or associated driver fee
- delivery status
- relevant timestamps

## Driver flow
Login
-> Active assignments
-> Open assigned order
-> Go to store
-> Pickup
-> Deliver
-> Collect required amount
-> Complete delivery

## Assignment
When backend assigns an order:
- it appears automatically
- driver receives notification
- driver cannot reject it through a normal Accept/Reject action

## Completion
Completion must validate:
- driver owns the assignment
- order is in a completable state
- required collection information exists
- no duplicate completion exists

## History
Completed/cancelled/failed assignments remain visible in history according
to retention rules.
