# Blocker

## ID

BLK-003

## Title

Pricing, fees and store/driver amount model

## Raised By / Date

project-manager (initial discovery) — 2026-09-27

## Affects

FEAT-008 Ordering, FEAT-011 Money/Ledger, REQ-031/051/052/054, driver order display

## Description

Order total structure is recommended but no formula exists: how delivery fee is computed; which platform/store/customer fees exist and who pays; discounts; what exactly the 'store-related amount' is (does the driver pay the store the subtotal at pickup? minus commission?); how the driver fee is earned; which ledger accounts exist (store, driver, platform, customer?); rounding.

## Why It Blocks Development

Order snapshots, customer totals, driver money display (4 separate amounts), completion and every ledger entry depend on these definitions. Implementing any guess would be an invented business rule.

## Options Considered (for the decision owner; agents must not pick one)

Provide a worked example order with every amount (subtotal, delivery fee, fees, discounts, customer total, amount collected, amount to store, driver fee, platform revenue).

## Required Decision

Define the fee formula(s), the store/driver money relationship, the ledger accounts, and rounding rules, with at least 3 worked examples (cash order, fee-only order, cancelled order).

## Owner

Product Owner (via PM)

## Status

BLOCKED

## Resolution

(pending)
