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

BLOCKED

## Resolution

(pending)
