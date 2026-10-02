# Notification Logic

## Notification triggers
Notifications may be triggered by:
- order placed
- order confirmed
- order preparation changes
- order ready
- driver assigned
- pickup completed
- out for delivery
- delivered
- cancellation
- failure/reassignment
- important financial events

## Channels
Depending on platform support:
- in-app
- web push
- mobile push
- email/SMS as future integrations

## Rule
Notification delivery is not the business state itself.
The order/status/ledger record is authoritative.

Notification sending must be idempotent where duplicate notifications
would be harmful.

## Current architecture direction
Backend should use a NotificationService abstraction so Firebase credentials
can be introduced without coupling core order logic to a provider.
