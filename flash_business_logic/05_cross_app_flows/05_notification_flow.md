# Notification Flow

Business event
  -> backend transaction succeeds
  -> notification event emitted
  -> notification provider
  -> target app

Examples:
- Driver assigned -> Driver + relevant Store/Admin/Customer
- Order confirmed -> Customer
- Ready for pickup -> Assignment/Driver flow
- Out for delivery -> Customer
- Delivered -> Customer/Store/Admin as configured

Notification delivery failure must not silently roll back the business
transaction unless a future explicit business requirement says so.
