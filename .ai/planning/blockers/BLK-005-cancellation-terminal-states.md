# Blocker

## ID

BLK-005

## Title

Cancellation matrix and REJECTED/FAILED semantics

## Raised By / Date

project-manager (initial discovery) — 2026-09-27

## Affects

FEAT-012 Cancellation & failure, order state machine (TASK design of FEAT-008)

## Description

Undefined: which actor (customer/store/admin/system) may cancel from which status after PLACED; who may REJECT and from which status (store at PLACED?); who sets FAILED and the 'defined recovery path'; admin override transitions; refunds/reversals per case; whether DRAFT is persisted server-side.

## Why It Blocks Development

The state machine's transition table and financial reversals cannot be completed; QA scenario 'cancellation follows state rules' has no oracle.

## Options Considered (for the decision owner; agents must not pick one)

Provide a status × actor matrix (allowed / not allowed / needs reason) plus the financial effect of each cancellation/failure.

## Required Decision

Fill the cancellation/rejection/failure matrix and recovery paths.

## Owner

Product Owner (via PM)

## Status

BLOCKED

## Resolution

(pending)
