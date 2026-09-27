# Blocker

## ID

BLK-006

## Title

MVP driver assignment strategy and availability model

## Raised By / Date

project-manager (initial discovery) — 2026-09-27

## Affects

FEAT-009 Assignment

## Description

Docs list factors that MAY affect eligibility but no MVP algorithm; no driver availability model (online/offline, shifts), no service areas, no behavior when no driver is eligible, no reassignment policy trigger, no max concurrent orders per driver. Also confirm assignment starts only at READY_FOR_PICKUP (not earlier while preparing).

## Why It Blocks Development

The assignment service and its tests need concrete eligibility and fallback behavior.

## Options Considered (for the decision owner; agents must not pick one)

- A: Round-robin/least-loaded among online drivers; if none, order waits in queue and admin is alerted; retry on driver going online
- B: Nearest driver (requires location tracking)

## Required Decision

Define MVP eligibility, selection, no-driver fallback, reassignment triggers, and assignment timing.

## Owner

Product Owner (via PM) + Team Lead

## Status

BLOCKED

## Resolution

(pending)
