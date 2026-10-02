# Cancellation Flow

Cancellation availability depends on current order status and actor.

1. Actor requests cancellation.
2. Backend checks permission and current status.
3. If allowed, order moves to CANCELLED.
4. Status history is written.
5. Required notifications are sent.
6. Financial reversal/refund behavior is applied when applicable.
7. Driver/store assignment is closed or reassigned as defined by state.

No client should decide cancellation eligibility independently.
