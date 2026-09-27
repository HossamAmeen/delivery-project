# Blocker

## ID

BLK-001

## Title

Login identifier and authentication method per role

## Raised By / Date

project-manager (initial discovery) — 2026-09-27

## Affects

FEAT-002 Identity & Accounts; TASK-003 (USERNAME_FIELD / JWT token request shape)

## Description

The business docs say Customers can register/login and other roles login, but not with what: email, phone number, username, or phone + OTP.

## Why It Blocks Development

The custom User model's USERNAME_FIELD, the JWT token request contract, registration validation, and uniqueness constraints all depend on it. OTP would add an SMS provider and sensitive-endpoint throttling.

## Options Considered (for the decision owner; agents must not pick one)

- A: Email + password for all roles
- B: Phone + password for all roles
- C: Phone + OTP for customers/drivers, email + password for store/admin
- D: Other

## Required Decision

Choose the identifier (and whether it is unique across roles), whether OTP is required in MVP, and whether email/phone verification is required.

## Owner

Product Owner (via PM)

## Status

BLOCKED

## Resolution

(pending)
