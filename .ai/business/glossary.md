# Glossary

Use these terms in the backend, frontend, mobile, admin, QA and docs. Source: `flash_business_logic/00_core/10_shared_terms.md`, extended.

## Business
| Term | Meaning |
|---|---|
| Customer | The end user who places a delivery order |
| Store | A merchant/business that receives and prepares orders (pharmacy, supermarket, flower shop, restaurant, …) |
| Driver | The delivery person who executes an order the system assigned |
| Admin | A platform operator |
| System | Backend automation (assignment, pricing, transitions) acting without a human actor |
| Order | A delivery transaction from one customer, fulfilled by a store and a driver |
| Order Item | A line in an order, with a product snapshot (name, unit price, quantity, line total) |
| Snapshot | Values copied onto the order when it is created/confirmed so later catalog or fee changes do not affect it |
| Status / Transition | An order lifecycle state / a validated backend operation that moves between states |
| Allowed transitions | The transitions the requesting actor may perform now, computed by the backend and returned to clients |
| Status History | An append-only record of every transition (from, to, actor, timestamp, reason) |
| Assignment | The system relationship between an order and a driver. Created by the system, never accepted or rejected by the driver |
| Reassignment | Replacing an assignment. The previous one is kept in history |
| Active workload | The driver's currently assigned, not-yet-finished orders |
| Category | A store-defined grouping of products |
| Product / Item | A sellable catalog entry of a store |
| Active / Inactive | Product lifecycle (configured vs retired) |
| Available / Unavailable | Temporary orderability of an active product |
| Subtotal | Σ line totals |
| Delivery fee | The fee for delivery (formula TBD, BLK-003) |
| Customer total | The amount the customer pays: subtotal + fees − discounts |
| Collection | Money the driver collects from the customer |
| Expected / Actual collection | The amount due from the customer vs the amount recorded at completion |
| Discrepancy | A difference between the expected and actual collection. It must be explicit and auditable |
| Store-related amount | The amount payable to or settled with the store for an order (exact definition TBD, BLK-003) |
| Driver / platform fee | The fee attributed to the driver or platform for an order |
| Ledger / Ledger entry | The append-only financial event history. Balances are derived from it |
| Idempotency key | A unique reference so that a retried command does not duplicate effects |
| Audit log | A record of important actions: actor, action, target, before/after, time |

## Engineering process
| Term | Meaning |
|---|---|
| PO | Product Owner: the human who approves business-rule changes |
| FEAT / TASK / BUG / BLK / ADR / REQ | Artifact IDs (see `.ai/README.md`) |
| DoD | Definition of Done (`.ai/README.md` and `DRF_SKILL.md` §58) |
| Plan review | TL approval of an implementation plan before coding |
| Standard envelope | `{success, message, data}` / `{success, message, errors}` (DRF_SKILL §19) |
| Contract | The documented request/response of an endpoint in `architecture/api-contracts.md` |
