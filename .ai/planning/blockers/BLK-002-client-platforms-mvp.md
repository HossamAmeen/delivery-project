# Blocker

## ID

BLK-002

## Title

Which client apps are in MVP and on which platform

## Raised By / Date

project-manager (initial discovery) — 2026-09-27

## Affects

ADR-008, ADR-011, FEAT-003 Frontend foundation, all frontend work

## Description

Docs mention a Vue PWA (customer + driver), Flutter (customer + driver), a Store app and an Admin dashboard, but not which are MVP, their order, or the platform for Store/Admin.

## Why It Blocks Development

Frontend scaffolding, routing structure and the frontend stack ADR cannot be accepted. Contract priorities depend on which clients come first.

## Options Considered (for the decision owner; agents must not pick one)

- A: Vue PWA with role areas customer/driver/store/admin; Flutter later (TL-recommended)
- B: Vue PWA customer/driver; Admin on Django Jazzmin; Store in Vue
- C: Flutter first for customer/driver

## Required Decision

Confirm MVP client list and order; confirm Vue 3 + TS stack (ADR-008) and Store/Admin surface (ADR-011).

## Owner

PM + Team Lead

## Status

RESOLVED

## Resolution

- **Decision (quoted):** "BLK-002 client platforms → RESOLVED: Vue 3 PWA scaffold (Vite) is the MVP web client served at the web domain; Flutter later. So FEAT-003 is IN scope for sprint-01 (not conditional any more)."
- **Decided by:** Product Owner, via orchestrator. **Date:** 2026-09-27. Recorded by PM.
- **Consequences:**
  - FEAT-003 (Vue PWA foundation) is unconditionally in sprint-01. The PWA is served at `WEB_DOMAIN=delivery.hossam-ameen.online` (see BLK-011).
  - Flutter (FEAT-017) is after the MVP.
  - ADR-008 (Vue 3 + Vite stack) can be accepted by the TL.
- **Still open for the TL (technical, not a business rule):** ADR-011, meaning whether the Store and Admin MVP surfaces are role areas of the same Vue PWA. The PO named one MVP web client. The TL records the ADR, and the PM escalates only if it needs a second client.
- **Documents updated:** `.ai/business/business-logic.md` §1, `.ai/business/requirements.md` (Change Log), `.ai/planning/backlog.md` (FEAT-003, FEAT-017), `.ai/planning/roadmap.md`, `.ai/planning/sprints/sprint-01.md`.
