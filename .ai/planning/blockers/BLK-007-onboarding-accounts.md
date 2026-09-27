# Blocker

## ID

BLK-007

## Title

Account onboarding, store staff model and data visibility

## Raised By / Date

project-manager (initial discovery) — 2026-09-27

## Affects

FEAT-002 Identity & Accounts, FEAT-005 Store profile, FEAT-006 Driver management

## Description

Who creates Store and Driver accounts (self-signup vs admin), approval/verification requirements; can a store have several staff users; can one user hold multiple roles; which driver/customer fields each role may see; history retention period.

## Why It Blocks Development

User/profile models, registration endpoints and permission scoping depend on it.

## Options Considered (for the decision owner; agents must not pick one)

- A: Customers self-register; stores and drivers are created by admin; one role per account; one owner user per store (MVP)

## Required Decision

Confirm onboarding per role, store staff model, role multiplicity, cross-role data visibility and retention.

## Owner

Product Owner (via PM)

## Status

BLOCKED

## Resolution

(pending)
