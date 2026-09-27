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

BLOCKED

## Resolution

(pending)
