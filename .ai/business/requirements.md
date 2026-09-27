# Requirements Catalog

Owner: PM. Every requirement traces to its source. Features in `planning/backlog.md` reference these IDs.
Status: `DEFINED` (ready for design) · `PARTIAL` (usable, but has open points) · `BLOCKED` (waiting on BLK).

## Platform / non-functional
| ID | Requirement | Source | Status |
|---|---|---|---|
| REQ-001 | The backend is the single authority for state, assignment, pricing, fees, totals and permissions | core/09, README | DEFINED |
| REQ-002 | The backend follows the DRF engineering standard (settings, env, JWT, OpenAPI, health, throttling, tests, Docker, deploy) | DRF_SKILL.md | DEFINED |
| REQ-003 | Every API action validates authentication → role → ownership → transition → business constraints | core/02 | DEFINED |
| REQ-004 | Important actions are audited (status, assignment, finance, admin, catalog, cancellation) | core/09 | DEFINED |
| REQ-005 | Assignment, transitions, completion and ledger are race-safe and idempotent | core/09, core/06 | DEFINED |
| REQ-006 | Public APIs are rate limited; auth endpoints are stricter | DRF_SKILL §61–83 | DEFINED |
| REQ-007 | Localization, language(s), RTL, timezone | — | BLOCKED (BLK-009) |
| REQ-008 | The system is deployed to the PO's shared VPS: systemd mode, nginx + Let's Encrypt TLS, `api.delivery.hossam-ameen.online` (API) and `delivery.hossam-ameen.online` (web), SQLite, no Redis/Docker, operator-triggered deploy, with health check and rollback. It never disturbs the co-hosted dental-clinic app | PO decision 2026-09-27 (BLK-011) | DEFINED |
| REQ-009 | QA and backend test suites run on the server against the deployed instance, not on the local machine | PO decision 2026-09-27 | DEFINED |

## Identity & accounts
| ID | Requirement | Source | Status |
|---|---|---|---|
| REQ-010 | Roles: Customer, Driver, Store, Admin | core/01–02 | DEFINED |
| REQ-011 | Customer can register and log in; the other roles can log in. Every role logs in with **username + password** (no OTP in the MVP) | core/02; PO decision 2026-09-27 (BLK-001) | PARTIAL (email/phone collection & verification, onboarding → BLK-007) |
| REQ-012 | Customer manages their profile and delivery addresses | core/02 | PARTIAL (address fields/geo → BLK-008) |
| REQ-013 | Store manages the store profile | core/02, store | PARTIAL (store fields, opening hours → BLK-008) |
| REQ-014 | Admin manages users, stores and drivers | core/02, admin | PARTIAL (onboarding → BLK-007) |

## Catalog
| ID | Requirement | Source | Status |
|---|---|---|---|
| REQ-020 | Store creates/edits/deactivates categories (name, description?, image?, active, sort order) | core/07, store | DEFINED |
| REQ-021 | Store creates/edits/deactivates products (name, description, price, image, category, active, availability, sort order) | core/07, store | DEFINED |
| REQ-022 | Availability is separate from the active lifecycle | store/categories_and_products | DEFINED |
| REQ-023 | Customers browse stores → categories → products; only active and available products are orderable | customer, core/07 | DEFINED |
| REQ-024 | A store can modify only its own catalog | core/02 | DEFINED |

## Ordering & lifecycle
| ID | Requirement | Source | Status |
|---|---|---|---|
| REQ-030 | The customer builds an order, confirms the address, reviews the backend-calculated total, and places the order | customer | PARTIAL (single store? DRAFT persisted? → BLK-008) |
| REQ-031 | The order stores item and financial snapshots | core/05, core/07 | PARTIAL (formula → BLK-003) |
| REQ-032 | Lifecycle DRAFT…DELIVERED + CANCELLED/FAILED/REJECTED, centralized enum, exposed in OpenAPI | core/03 | PARTIAL (terminal-state rules → BLK-005) |
| REQ-033 | Store processes PLACED → CONFIRMED → PREPARING → READY_FOR_PICKUP | store | DEFINED |
| REQ-034 | Every transition validates, writes history, notifies, triggers finance, is idempotent | core/03 | DEFINED |
| REQ-035 | The customer tracks the current status and relevant history | customer | DEFINED |
| REQ-036 | Cancellation according to the state/actor rules, with financial reversal where applicable | core/03, flow/04 | BLOCKED (BLK-005, BLK-004) |
| REQ-037 | APIs expose the allowed transitions/actions per actor; clients never compute them | driver/order_display_rules, customer | DEFINED |

## Assignment & delivery
| ID | Requirement | Source | Status |
|---|---|---|---|
| REQ-040 | The system assigns an eligible driver when the order is READY_FOR_PICKUP; there is no driver accept/reject | core/04, flow/02 | PARTIAL (algorithm → BLK-006) |
| REQ-041 | The assigned order appears in the driver's active workload, and the driver is notified | driver | DEFINED |
| REQ-042 | Reassignment keeps history | core/04 | PARTIAL (policy → BLK-006) |
| REQ-043 | The driver updates PICKED_UP → OUT_FOR_DELIVERY → DELIVERED | driver | DEFINED |
| REQ-044 | Completion validates ownership, completable state, collection info and no duplicate | driver | DEFINED |
| REQ-045 | The driver sees the history of completed/cancelled/failed orders | driver | PARTIAL (retention → BLK-007) |

## Money
| ID | Requirement | Source | Status |
|---|---|---|---|
| REQ-050 | Decimal money, explicit currency, backend authoritative | core/05 | PARTIAL (currency → BLK-009) |
| REQ-051 | Order total structure: subtotal + delivery fee + fees − discounts | core/05 | BLOCKED (BLK-003) |
| REQ-052 | The driver sees 4 separate amounts: to collect, store amount, driver/platform fee, total | driver/order_display_rules | PARTIAL (definitions → BLK-003) |
| REQ-053 | Completion records the actual collection; discrepancies are explicit | core/06 | PARTIAL (procedure → BLK-004) |
| REQ-054 | Ledger entry for every balance-affecting event; idempotent; balances derived | core/06 | PARTIAL (accounts model → BLK-003) |
| REQ-055 | Payment methods | — | BLOCKED (BLK-004) |

## Notifications
| ID | Requirement | Source | Status |
|---|---|---|---|
| REQ-060 | NotificationService abstraction; emit after commit; failures do not roll back | core/08, flow/05 | DEFINED |
| REQ-061 | In-app notifications for lifecycle events | core/08 | PARTIAL (recipient matrix → BLK-010) |
| REQ-062 | Web/mobile push (Firebase) | core/08 | BLOCKED (BLK-010, credentials) |

## Admin dashboard (MVP)
| ID | Requirement | Source | Status |
|---|---|---|---|
| REQ-070 | Overview: orders, active deliveries, stores, drivers, customers, alerts, financial summary | admin | PARTIAL (surface/platform → BLK-002) |
| REQ-071 | Orders list/details with filters (ID, status, store, driver, customer, date) | admin/mvp_scope | DEFINED |
| REQ-072 | Stores, drivers, customers lists/details | admin/mvp_scope | DEFINED |
| REQ-073 | Read-only financial summaries | admin | PARTIAL (BLK-003) |
| REQ-074 | Admin actions are permission-protected and audited | admin | DEFINED |

## Out of scope (MVP), per the business docs
Advanced analytics, deep reconciliation, configurable assignment rules, advanced reporting, audit explorer, operational maps, bulk operations, email/SMS notifications, inventory/stock quantities.

## Change Log
| Date | Change | Requested by | Approved by | Docs updated |
|---|---|---|---|---|
| 2026-09-27 | Initial catalog created from `flash_business_logic/` | PM (setup) | — | — |
| 2026-09-27 | Login identifier = username + password for all roles (REQ-011) | Product Owner | Product Owner | BLK-001, business-logic §2, backlog |
| 2026-09-27 | MVP client = Vue 3 PWA (Vite) at the web domain; Flutter later | Product Owner | Product Owner | BLK-002, business-logic §1, backlog, roadmap |
| 2026-09-27 | REQ-008 added: hosting and deployment on the shared VPS (systemd, SQLite, no Redis, TLS, two domains) | Product Owner | Product Owner | BLK-011, backlog FEAT-004, sprint-01 |
| 2026-09-27 | REQ-009 added: QA runs on the server, not locally | Product Owner | Product Owner | sprint-01, backlog FEAT-001/003/004 |
