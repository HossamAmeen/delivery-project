# Blocker

## ID

BLK-012

## Title

Git hosting provider and CI platform

## Raised By / Date

team-lead (Infrastructure agent introduced) — 2026-09-27

## Affects

TASK-011 Backend CI; ADR-014; FEAT-003 frontend CI; FEAT-004 deploy pipeline

## Description

The project is not a git repository, and no remote or provider is known (GitHub, GitLab, Bitbucket, self-hosted). The spec requires CI/CD "according to the project's Git provider".

## Why It Blocks Development

The CI workflow format, secrets storage, protected environments (production approval) and the image registry all depend on the provider.

## Options Considered (for the decision owner; agents must not pick one)

- A: GitHub + GitHub Actions + GHCR registry (TL-recommended; matches the spec's example)
- B: GitLab + GitLab CI + GitLab registry
- C: Other

## Required Decision

Choose the provider and create the repository. Say whether an image registry may be used.
Approve `git init` and the initial commit of the current workspace. Say whether `flash_business_logic_complete.zip` (a duplicate) should be committed.

## Owner

Product Owner (via PM) + Team Lead

## Status

BLOCKED (partially resolved; the provider/remote part is still open)

## Resolution

- **Partial decision, 2026-09-27, Product Owner via orchestrator:**
  - `git init` approved and done. Initial commit `8b5dc17` on branch `main`, made by the orchestrator with the PO's consent.
  - `flash_business_logic_complete.zip` (duplicate) is **not** committed. It is git-ignored.
- **Still open:** git hosting provider / remote, CI platform, image registry.
- **Effect:** TASK-011 (backend CI) stays BLOCKED. The FEAT-004 CI/CD criterion is deferred until this is resolved. Sprint-01 deploys are operator-triggered from the local machine (`make deploy` over SSH), which needs no remote.
- **Owner of the remaining decision:** Product Owner (via PM).
