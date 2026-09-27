# Flash — Roadmap

Owner: PM. Sprint length is **2 weeks** (proposed; confirm with the Product Owner). Dates are indicative.
The sequence follows dependency order and blocker readiness. Every phase ends with PM acceptance of its features.

| Phase | Sprint | Goal | Features | Gate / blockers needed |
|---|---|---|---|---|
| 0. Foundation | S1 (2026-09-28 → 10-09) | A production-grade DRF skeleton everyone can build on, plus the QA harness | FEAT-001, FEAT-003 (if BLK-002 resolved) | none for FEAT-001 |
| 1. Identity & delivery pipeline | S2 | Users can authenticate by role; staging deployable over SSH in both modes, with rollback | FEAT-002, FEAT-004, FEAT-003 (if deferred) | BLK-001, BLK-007, BLK-002, BLK-011, BLK-012 |
| 2. Stores & catalog | S3 | Stores manage catalog; customers browse; audit trail exists | FEAT-005, FEAT-007, FEAT-016 | BLK-008 |
| 3. Ordering | S4–S5 | Customer places an order; store processes it to READY_FOR_PICKUP with snapshots | FEAT-008 | BLK-003, BLK-005 (transition table), BLK-008, BLK-009 |
| 4. Assignment & delivery | S5–S6 | System assigns a driver; driver picks up and delivers | FEAT-006, FEAT-009, FEAT-010, FEAT-014 | BLK-006 |
| 5. Money | S6 | Collection, 4-amount driver display, idempotent ledger | FEAT-011 | BLK-003, BLK-004 |
| 6. Exceptions & notifications | S7 | Cancellation/reject/fail flows; notifications for business events | FEAT-012, FEAT-013 | BLK-005, BLK-010 |
| 7. Admin MVP | S8 | Admin dashboard MVP per `04_admin_dashboard/mvp_scope.md` | FEAT-015 | BLK-002 |
| 8. MVP hardening & release | S9 | Full regression, cross-client consistency, performance, production deploy | — | BLK-011 |
| Later | — | Flutter app; advanced admin (analytics, maps, reconciliation) | FEAT-017, … | — |

## Infrastructure track
The Infrastructure agent works in every sprint, alongside feature work:
- S1: local Docker, backend CI
- S2: SSH deploy, both modes, staging, rollback, Nginx/systemd templates, frontend CI
- S3–S8: keep CI/deploy current with each feature's runtime needs (Celery/Redis when notifications or assignment need them, Firebase credentials, media storage)
- S9: production go-live checklist

## Critical path
FEAT-001 → FEAT-002 → FEAT-005 → FEAT-008 → FEAT-009 → FEAT-010 → FEAT-011.

**BLK-003 (pricing/fees)** is the highest-risk unknown. It must be resolved before Sprint 4 planning (≈ 2026-10-23), or Phase 3 slips.

## Change log
| Date | Change | Reason |
|---|---|---|
| 2026-09-27 | Initial roadmap | Project discovery |
| 2026-09-27 | Infrastructure track added; FEAT-004 is P0 for S2 | Infrastructure agent introduced |
