# Flash — Roadmap

Owner: PM. Sprint length is **2 weeks** (proposed; confirm with the Product Owner). Dates are indicative.
The sequence follows dependency order and blocker readiness. Every phase ends with PM acceptance of its features.

| Phase | Sprint | Goal | Features | Gate / blockers needed |
|---|---|---|---|---|
| 0. Foundation + live deployment (DONE 2026-09-28) | S1 (closed early, 2026-09-27 → 09-28) | Backend foundation and Vue PWA shell, deployed over HTTPS to the PO's shared VPS (systemd) and QA-verified on the server | FEAT-001, FEAT-003, FEAT-004 | none (BLK-001/002/011 RESOLVED 2026-09-27); CI waits on BLK-012 |
| 1. Identity + CI | S2 (start date on PO confirmation; `sprints/sprint-02.md` DRAFT) | Users register/log in (username + password) by role and see their profile; CI once the git provider is known | FEAT-002, deferred FEAT-004 CI criteria | **BLK-007 (hard gate)**, BLK-012 (CI only) |
| 2. Stores & catalog | S3 | Stores manage catalog; customers browse; audit trail exists | FEAT-005, FEAT-007, FEAT-016 | BLK-008 |
| 3. Ordering | S4–S5 | Customer places an order; store processes it to READY_FOR_PICKUP with snapshots | FEAT-008 | BLK-003, BLK-005 (transition table), BLK-008, BLK-009 |
| 4. Assignment & delivery | S5–S6 | System assigns a driver; driver picks up and delivers | FEAT-006, FEAT-009, FEAT-010, FEAT-014 | BLK-006 |
| 5. Money | S6 | Collection, 4-amount driver display, idempotent ledger | FEAT-011 | BLK-003, BLK-004 |
| 6. Exceptions & notifications | S7 | Cancellation/reject/fail flows; notifications for business events | FEAT-012, FEAT-013 | BLK-005, BLK-010 |
| 7. Admin MVP | S8 | Admin dashboard MVP per `04_admin_dashboard/mvp_scope.md` | FEAT-015 | ADR-011 (BLK-002 resolved) |
| 8. MVP hardening & release | S9 | Full regression, cross-client consistency, performance, production go-live review (separate prod env? PostgreSQL/Redis?) | — | PO decision on the production environment |
| Later | — | Flutter app; advanced admin (analytics, maps, reconciliation) | FEAT-017, … | — |

## Infrastructure track
The Infrastructure agent works in every sprint, alongside feature work:
- S1: systemd deploy over SSH to the shared VPS (backend + PWA), nginx + Let's Encrypt, health check, rollback, SQLite backups, dental-clinic non-interference. Local Docker is optional developer tooling only.
- S2: CI pipelines (backend, frontend, deploy) once BLK-012 is resolved
- S3–S8: keep CI/deploy current with each feature's runtime needs (Celery/Redis when notifications or assignment need them, which needs a PO decision because Redis is excluded for now; Firebase credentials; media storage)
- S9: production go-live checklist

## Critical path
FEAT-001 → FEAT-002 → FEAT-005 → FEAT-008 → FEAT-009 → FEAT-010 → FEAT-011.

**BLK-007 (onboarding)** is the next gate: sprint-02 cannot be planned without it.
**BLK-003 (pricing/fees)** is the highest-risk unknown. It must be resolved before Sprint 4 planning (≈ 2026-10-23, earlier if the sprints keep closing early), or Phase 3 slips.

## Live environment
The shared VPS runs release `20260927-232246` (`d6669b6`): `https://delivery.hossam-ameen.online` (PWA) and `https://api.delivery.hossam-ameen.online` (API). One environment; operator-triggered deploys; SQLite; no CI yet.

## Change log
| Date | Change | Reason |
|---|---|---|
| 2026-09-27 | Initial roadmap | Project discovery |
| 2026-09-27 | Infrastructure track added; FEAT-004 is P0 for S2 | Infrastructure agent introduced |
| 2026-09-27 | FEAT-004 and FEAT-003 pulled into S1; S2 refocused on FEAT-002 + CI; S9 gate changed | PO decisions: BLK-001/002/011 resolved, deploy now, QA on the server |
| 2026-09-28 | S1 closed and accepted (FEAT-001/003/004); S2 marked DRAFT pending BLK-007; live environment noted | Sprint-01 acceptance |
