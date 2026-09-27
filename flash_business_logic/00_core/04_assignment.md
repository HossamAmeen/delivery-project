# Driver Assignment Logic

## Core rule
The driver does not see an order as a request requiring Accept/Reject.

The platform/system assigns the order directly.

## Assignment flow

1. Order reaches the state eligible for assignment.
2. Assignment service determines an eligible driver.
3. Driver assignment is created.
4. Order status moves to ASSIGNED.
5. Driver receives notification.
6. Order appears in driver's active workload.
7. Driver executes the delivery.

## Driver eligibility
Eligibility may consider:
- Driver active status
- Driver availability
- Geographic/service area
- Current workload
- Operational constraints
- Platform assignment strategy

The exact algorithm is an implementation/configuration concern and must not
be duplicated in clients.

## Reassignment
If a driver becomes unavailable or an assignment fails:
- backend decides whether reassignment is allowed
- previous assignment is retained in history
- new assignment is recorded
- driver notifications are updated

## Important
No frontend should implement its own assignment algorithm.
The backend is authoritative.
