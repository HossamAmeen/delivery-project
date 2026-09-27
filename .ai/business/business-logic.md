# Flash — Business Logic (Agent Digest)

> **Read this before implementing any business functionality.**
> This is a structured digest of `flash_business_logic/`, the canonical detailed source (ADR-004).
> Each rule cites its source as `[core/03]` = `flash_business_logic/00_core/03_order_lifecycle.md`,
> `[flow/06]` = `05_cross_app_flows/06_qa_contract.md`, `[driver]` = `02_driver_app/`, and so on.
>
> **UNDEFINED** marks a rule the business has not specified yet. Do not implement a guess.
> Follow the linked blocker (`.ai/planning/blockers/`).

Last synced with `flash_business_logic/`: 2026-09-27. Also includes PO decisions of 2026-09-27 (BLK-001, BLK-002) that are not yet mirrored into `flash_business_logic/`.

---

## 1. Product
Flash is a delivery platform. A **Customer** orders items from a **Store** (pharmacy, supermarket, flower shop, restaurant, other). The **system** assigns a **Driver** who picks up and delivers the order and may collect money from the customer. An **Admin** operates the platform. [core/01]

Product surfaces: Customer app, Driver app, Store app, Admin dashboard. The Vue PWA and Flutter support the customer and driver roles with the same rules. [README]

**MVP client platform (PO decision 2026-09-27, BLK-002):** the Vue 3 PWA (Vite) is the MVP web client, served at the web domain. Flutter comes after the MVP. Whether Store and Admin are role areas of that PWA is ADR-011 (TL).

## 2. Actors & roles
| Role | Summary | Source |
|---|---|---|
| Customer | Creates delivery orders, tracks them, handles customer-side payment/collection | [core/01] |
| Store | Business with categories and products; receives and prepares orders | [core/01], [core/07] |
| Driver | Executes orders the system assigns; **never accepts or rejects** | [core/01], [core/04] |
| Admin | Manages users, stores, drivers and orders; monitors operations and finance | [core/01] |
| System | Assigns drivers, calculates prices and fees, enforces transitions | [core/04], [core/05] |

- One user account per role, or several roles per account: **UNDEFINED** → BLK-007
- Login identifier: **username + password for every role** (PO decision 2026-09-27, BLK-001). Django default `USERNAME_FIELD = "username"`, so a username is unique across all users. No OTP in the MVP login. Collecting or verifying email/phone: **UNDEFINED** → BLK-007
- Who creates store and driver accounts (self-signup vs admin), and any approval/verification: **UNDEFINED** → BLK-007

## 3. Permissions [core/02]

### Authorization rule (applies to every API action)
1. authenticated user → 2. role → 3. object ownership/relationship → 4. allowed state transition → 5. business constraints.

| Capability | Customer | Store | Driver | Admin |
|---|---|---|---|---|
| Register / login | ✅ register+login | ✅ login | ✅ login | ✅ |
| Manage own profile | ✅ | ✅ store profile | — (UNDEFINED) | ✅ |
| Manage delivery addresses | ✅ own | — | — | view |
| Browse stores/categories/items | ✅ | own catalog | — | ✅ |
| Manage categories/products | ❌ | ✅ **own store only** | ❌ | ✅ (manage stores) |
| Create order | ✅ | ❌ | ❌ | UNDEFINED |
| View order | ✅ own | ✅ orders of own store | ✅ assigned to self | ✅ all |
| Change order status | only allowed customer transitions | PLACED→…→READY_FOR_PICKUP | allowed delivery statuses | UNDEFINED which overrides → BLK-005 |
| Cancel | only when state permits (→ BLK-005) | UNDEFINED | UNDEFINED | UNDEFINED |
| Assign driver | ❌ | ❌ (unless a future admin feature enables it) | ❌ | review assignments; manual assign UNDEFINED |
| Accept/reject assignment | ❌ | ❌ | ❌ **never** | — |
| Change prices | ❌ | own products | ❌ | — |
| Change platform fees | ❌ | ❌ | ❌ | ✅ "manage/configure business settings" |
| View financial info | own order payment/collection | amounts relevant to store | collection + store amount + fees | financial records (read-only in MVP) |
| View audit logs | ❌ | ❌ | ❌ | ✅ |

The store "can view driver/order information relevant to operations". The exact driver fields a store may see are **UNDEFINED** → BLK-007.

## 4. Entities & relationships [core/01], [core/07]
- **User** — 1:1 with CustomerProfile, DriverProfile, or a Store owner/staff link (the store staff model is **UNDEFINED** → BLK-007)
- **Store** — 1:N **StoreCategory** — 1:N **Product** (a product belongs to both a store and a category)
- **Customer** — 1:N **Address**
- **Order** — N:1 Customer, N:1 Store, N:1 delivery Address (snapshot); 1:N **OrderItem**; 1:N **OrderStatusHistory**; 1:N **DriverAssignment** (history is kept; at most one active)
- **Payment/Collection** — per order: expected vs actual collected amount
- **Store fee / Driver fee** — amounts snapshotted on the order
- **Wallet/LedgerEntry** — per account (store, driver, platform?); account model **UNDEFINED** → BLK-003
- **Notification** — per recipient user, per business event
- **AuditLog** — actor, action, target, before/after

Whether one order may contain items from several stores is **UNDEFINED**. Every document implies one store per order → confirm in BLK-008.

## 5. Catalog rules [core/07], [store/*]
- A store has many categories. Category fields: name, description?, image?, active, sort order.
- Product fields: name, description, price, image, category, active, availability, sort order.
- Product lifecycle is `ACTIVE ↔ INACTIVE`. **Availability** is separate: a product can be active but temporarily unavailable.
- Only active **and** available products are orderable. The backend validates this at order time even if the UI shows the product.
- A store may modify only its own catalog.
- Changing a product never alters existing orders (item snapshot).
- Stock/inventory quantity: not specified. Treat it as out of scope until defined.

## 6. Order lifecycle [core/03], [flow/01]

### Statuses
`DRAFT → PLACED → CONFIRMED → PREPARING → READY_FOR_PICKUP → ASSIGNED → PICKED_UP → OUT_FOR_DELIVERY → DELIVERED`
Terminal alternatives: `CANCELLED`, `FAILED`, `REJECTED`.
Status names live in one backend enum and are exposed through OpenAPI.

### Transitions (defined)
| From → To | Actor | Source |
|---|---|---|
| DRAFT → PLACED | Customer | [core/03] |
| DRAFT → CANCELLED (or edit) | Customer | [core/03] "may edit/cancel before placement" |
| PLACED → CONFIRMED | Store / system | [core/03], [store] |
| CONFIRMED → PREPARING | Store | [store] |
| PREPARING → READY_FOR_PICKUP | Store | [store] |
| READY_FOR_PICKUP → ASSIGNED | System (assignment service) | [core/04] |
| ASSIGNED → PICKED_UP | Driver | [core/03], [driver] |
| PICKED_UP → OUT_FOR_DELIVERY | Driver (implied by "update delivery progress") | [driver] |
| OUT_FOR_DELIVERY → DELIVERED | Driver ("complete delivery") | [driver] |

### Transitions (UNDEFINED → BLK-005)
- Which actor may cancel from which status after PLACED. What happens to an assigned driver or a prepared order on cancellation.
- `REJECTED`: who can reject (the store at PLACED?) and from which statuses.
- `FAILED`: who sets it, from which statuses, and the "defined recovery path" (return to store? reassign? refund?).
- Admin override transitions.
- Is DRAFT persisted server-side, or is the cart client-only until placement?

### Every transition must [core/03]
Validate the current state, the actor and the required data. Write status history. Trigger notifications and financial operations. Be idempotent where appropriate. A transition is a backend operation, never a plain field update.

## 7. Assignment [core/04], [flow/02]
1. The order becomes eligible. It is eligible when it reaches **READY_FOR_PICKUP**, per the flow docs.
2. The backend assignment service selects an eligible driver.
3. It creates the assignment record → the order becomes ASSIGNED → the driver is notified → the order appears in the driver's active workload.
4. The store and admin can see the assignment. The customer sees driver info "when appropriate".
- **No Accept/Reject step exists.**
- Eligibility *may* consider: active status, availability, service area, current workload, operational constraints, strategy. The concrete MVP algorithm is **UNDEFINED** → BLK-006.
- Reassignment: the backend decides whether it is allowed. The previous assignment is kept in history, the new one is recorded, and notifications are updated.
- What happens when no eligible driver exists (queue, retry, admin alert) is **UNDEFINED** → BLK-006.
- The driver availability model (online/offline toggle? shifts?) is **UNDEFINED** → BLK-006.
- No client implements assignment logic.

## 8. Money [core/05], [core/06], [flow/03]

### Principles
- Use Decimal. Never float. Persist the currency explicitly. The backend is authoritative, and the UI may only display.
- Persist a snapshot at order creation/confirmation: item price, quantity, line total, subtotal, delivery fee, discounts, customer total, store-related amount, driver-related fee/amount, currency.
- Never recalculate historical totals from current prices.

### Order total (structure recommended, formula UNDEFINED → BLK-003)
`subtotal + delivery_fee + applicable platform/store/customer fees − applicable discounts = customer_total`

### Confirmed relationships
- The driver has an amount/fee payable to the store according to the business model.
- The driver may collect money from the customer.
- The driver order view shows these **separately**: amount to collect, store-related amount/fee, driver/platform fee, order total. [driver/order_display_rules]

### UNDEFINED → BLK-003 / BLK-004
- How the delivery fee is calculated (flat, distance, zone, per store)
- Which platform fees exist and who pays them
- Discounts/promotions
- Currency and precision
- The exact definition of the "store-related amount": does the driver pay the store the subtotal at pickup? Minus a commission?
- Payment methods: cash-on-delivery only? online payment?
- When the snapshot is taken: at PLACED or at CONFIRMED (both are mentioned)
- Collection discrepancy handling (the docs require it to be "explicit and auditable", but no procedure is given)
- Refund/reversal rules on cancellation

### Ledger [core/06]
Every balance-affecting event → a ledger entry with: reference/order, actor/account, transaction type, amount, currency, direction, timestamp, resulting balance (when applicable), idempotency/reference key.
Balances are derived and reconciled from ledger rows, never silently mutated.
The same completion or financial request, retried, must not create duplicate entries.

## 9. Delivery completion [driver], [core/06]
Completion validates:
- the driver owns the assignment
- the order is in a completable state
- the required collection information is present
- no duplicate completion exists

It records the **actual collected amount** against the expected amount, creates the ledger entries, and finalizes the financial records.

## 10. Notifications [core/08], [flow/05]
- Triggers: placed, confirmed, preparation changes, ready, driver assigned, picked up, out for delivery, delivered, cancellation, failure/reassignment, important financial events.
- Channels: in-app, web push, mobile push. Email/SMS are future.
- The notification is **not** the state. The order, status and ledger records are authoritative.
- Emit only after the business transaction commits. A delivery failure must not roll the transaction back.
- Be idempotent where a duplicate notification would be harmful.
- Use a backend `NotificationService` abstraction so a provider (Firebase) can be added later.
- The recipient matrix per event is partly defined ([flow/05] examples). The full matrix is **UNDEFINED** → BLK-010.

## 11. Audit & concurrency [core/09]
- Audited: status changes, assignment changes, financial changes, admin changes, catalog changes, cancellation/reversal.
- Race-safe: assignment, status transitions, delivery completion, ledger creation, and inventory once it exists.
- Retrying a command must not duplicate its business effects.

## 12. Validations (known)
- Order creation: the cart, address and pricing are validated by the backend [flow/01]. Products must be active and available [core/07]. The address is required.
- Status change: current state, actor, required data [core/03].
- Completion: the four checks in §9.
- Catalog: the store owns the category and product.

## 13. Restrictions (summary)
- No client decides: state, cancellation eligibility, assignment, prices, fees, totals or permissions.
- The store cannot: modify historical item prices, rewrite ledger records, create invalid transitions, or bypass assignment. [store]
- The customer cannot: assign or accept/reject drivers, alter totals, or force a transition. [customer]
- The driver cannot: accept/reject, reassign, change pricing or fees, or modify the catalog. [core/02]
- Admin actions are permission-protected and audited. [admin]

## 14. Admin MVP [admin/mvp_scope]
The MVP includes:
- dashboard overview
- orders list and details
- stores, drivers and customers lists/details
- basic search/filter (order ID, status, store, driver, customer, date)
- basic operational status
- basic read-only financial visibility

Deferred: advanced analytics, deep reconciliation, configurable assignment rules, reporting, audit explorer, maps, bulk operations. "The MVP should not become an ERP."

## 15. Mandatory QA scenarios [flow/06]
1. valid order is created
2. invalid order is rejected
3. price snapshot is preserved
4. store processes valid states
5. invalid transition is rejected
6. system assigns the driver
7. there is no driver accept/reject
8. the assigned order appears to the driver
9. the driver sees the collection amount
10. the driver sees the store amount
11. duplicate completion is prevented
12. duplicate financial transaction is prevented
13. cancellation follows the state rules
14. notifications match business events
15. permissions block unauthorized actions

The same scenario must give the same result through the API, the Vue PWA, Flutter and Admin.

## 16. Edge cases to design and test for
- A product is deactivated or made unavailable between cart and placement → the order is rejected.
- A product's price changes after the order → the order keeps the snapshot.
- Two concurrent transitions on one order → only one wins, and the other gets a clean error.
- A duplicate completion or ledger request is retried → no duplicate effect.
- Two orders are assigned to the "same last available driver" at once → the assignment is race-safe.
- The driver becomes unavailable after assignment → reassignment with history (policy → BLK-006).
- A notification provider is down → the business state still commits.
- A store tries to access another store's catalog or orders → denied.
- The collected amount ≠ the expected amount → an explicit discrepancy record (procedure → BLK-004).
- Cancellation at every status × every actor → the matrix is pending (BLK-005).
