# Cross-App Order Flow

Customer:
Create order
  |
  v
Backend validates cart/address/pricing
  |
  v
PLACED
  |
  v
Store receives order
  |
  v
CONFIRMED
  |
  v
PREPARING
  |
  v
READY_FOR_PICKUP
  |
  v
Assignment service
  |
  v
Driver assigned automatically
  |
  v
ASSIGNED
  |
  v
Driver picks up
  |
  v
PICKED_UP
  |
  v
OUT_FOR_DELIVERY
  |
  v
Customer receives order
  |
  v
DELIVERED

Every state change is reflected consistently across all relevant apps.
