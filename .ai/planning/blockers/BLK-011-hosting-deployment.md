# Blocker

## ID

BLK-011

## Title

Hosting target, domains and environments

## Raised By / Date

project-manager (initial discovery) — 2026-09-27

## Affects

FEAT-004 Deployment & environments

## Description

No information on: hosting (VPS/cloud, OS), the default `DEPLOYMENT_MODE` per environment (docker vs systemd), server access (SSH host/user/key), domain names (`DOMAIN`, `API_DOMAIN`, `WEB_DOMAIN`), TLS certificates, whether staging exists, managed vs self-hosted PostgreSQL/Redis, and the `AUTO_DEPLOY` policy for staging and production. (The CI platform moved to BLK-012.)

## Why It Blocks Development

Staging/production Docker, nginx/systemd templates can be scaffolded generically, but deployment cannot be validated end to end.

## Options Considered (for the decision owner; agents must not pick one)

- A: Single VPS, Docker Compose + Nginx, managed or containerized Postgres

## Required Decision

Provide the hosting target, the default deployment mode per environment, SSH access for the Infrastructure agent (key path only, never the key), domains, staging yes/no, the database/Redis hosting and the auto-deploy policy.

## Owner

Product Owner (via PM) + Team Lead

## Status

BLOCKED

## Resolution

(pending)
