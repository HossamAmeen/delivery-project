# Blocker

## ID

BLK-004

## Title

Payment methods and collection discrepancy procedure

## Raised By / Date

project-manager (initial discovery) — 2026-09-27

## Affects

FEAT-011 Money/Ledger, FEAT-010 Driver execution, REQ-053/055

## Description

Docs cover cash collection by driver but do not state whether online payment exists in MVP, and require discrepancies to be 'explicit and auditable' without a procedure (who resolves, driver liability, admin approval).

## Why It Blocks Development

Completion API, collection model and ledger entries depend on it.

## Options Considered (for the decision owner; agents must not pick one)

- A: Cash on delivery only for MVP; discrepancy recorded + flagged for admin review
- B: Cash + online payment gateway (which?)

## Required Decision

Choose MVP payment methods and the discrepancy handling procedure.

## Owner

Product Owner (via PM)

## Status

BLOCKED

## Resolution

(pending)
