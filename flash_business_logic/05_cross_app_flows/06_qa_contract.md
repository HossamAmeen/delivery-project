# QA Business Contract

QA must test business rules, not just screens.

## Mandatory scenarios
- customer creates valid order
- invalid order rejected
- price snapshot preserved
- store processes valid states
- invalid state transition rejected
- system assigns driver
- driver has no Accept/Reject requirement
- assigned order appears to driver
- driver sees customer collection amount
- driver sees store-related fee/amount
- duplicate delivery completion is prevented
- duplicate financial transaction is prevented
- cancellation follows state rules
- notifications correspond to business events
- permissions prevent unauthorized actions

## Cross-client consistency
The same scenario should produce the same business result through:
- API
- Vue PWA
- Flutter
- Admin interface
where applicable.
