# Order Lifecycle

The exact status names should be centralized in the backend enum/constant
and exposed through OpenAPI.

Recommended lifecycle:

DRAFT
  -> PLACED
  -> CONFIRMED
  -> PREPARING
  -> READY_FOR_PICKUP
  -> ASSIGNED
  -> PICKED_UP
  -> OUT_FOR_DELIVERY
  -> DELIVERED

Alternative terminal states:
CANCELLED
FAILED
REJECTED

## Rules

### DRAFT
Customer may edit/cancel before placement.

### PLACED
Order is submitted to the platform.
Pricing and order snapshot data must be persisted.

### CONFIRMED
Store/system confirms the order for processing.

### PREPARING
Store is preparing the order.

### READY_FOR_PICKUP
Order is ready for driver pickup.

### ASSIGNED
System assigns a driver.
Driver does not manually accept/reject.

### PICKED_UP
Driver has collected the order from the store.

### OUT_FOR_DELIVERY
Driver is delivering to the customer.

### DELIVERED
Delivery completed.
Final collection/financial records must be finalized.

### CANCELLED
Order is cancelled according to cancellation rules.
Financial reversal/refund behavior must be recorded when applicable.

### FAILED
Delivery/process failed and requires the defined recovery path.

## State transition principle
A status transition is a backend business operation, not merely a UI field update.

Every transition must:
- Validate current state
- Validate actor
- Validate required data
- Write status history
- Trigger required notifications
- Trigger required financial operations
- Be idempotent where appropriate
