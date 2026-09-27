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

RESOLVED

## Resolution

- **Decided by:** Product Owner, via orchestrator. **Date:** 2026-09-27. Recorded by PM.
- **Decision (quoted/summarized from the PO instruction):**
  - **Host:** one existing VPS, Ubuntu 24.04 on GCP, host `34.123.215.195`, SSH user `hossam`, key path `~/.ssh/id_ed25519` (path only, never the key). Passwordless sudo. 2 vCPU, 3.8 GB RAM, no swap, about 13 GB free disk.
  - **Shared server:** "The server is SHARED with another production app (dental-clinic)." That covers the nginx sites `api.dental.hossam-ameen.online` and `dental.hossam-ameen.online`, `dental-clinic-backend.service` (gunicorn on `127.0.0.1:8000`) and `/srv/dental-clinic`. **Flash must not touch any of it.**
  - **Domains:** `API_DOMAIN=api.delivery.hossam-ameen.online`, `WEB_DOMAIN=delivery.hossam-ameen.online`. DNS already resolves to the server.
  - **Mode:** `DEPLOYMENT_MODE=systemd`. There is no Docker on the server, and Docker must not be installed.
  - **Database:** SQLite for now (PO choice: no new services). No Redis on the server.
  - **TLS:** Let's Encrypt, using the certbot already installed and the existing nginx (1.24).
  - **Ports:** `8000` is in use (dental). Free: 8001, 8010, 8020, 5432, 6379, 3000, 5173. Proposed Flash backend port: **8010** on `127.0.0.1`.
  - **Environments:** one environment for now. This server is the production-like "staging", and there is no separate staging. Deploys are operator-triggered: no auto-deploy (`AUTO_DEPLOY` off) and no CI remote yet.
  - **Runtime:** the server has python3.12. "Python 3.13 must be provided another way, e.g. `uv` — TL to decide via ADR." Node, npm, git, rsync, envsubst, certbot and nginx are present.
  - **QA policy:** "do NOT run QA locally; QA runs on the server against the deployed instance (and backend test suites also run on the server). Local machine is for building only."
- **Documents updated:** `.ai/planning/backlog.md` (FEAT-004 scope and acceptance criteria, FEAT-001 AC1/AC9), `.ai/planning/roadmap.md`, `.ai/planning/sprints/sprint-01.md`, `.ai/business/requirements.md` (REQ-008, Change Log).
- **For the TL/Infrastructure (technical follow-ups, not PM decisions):** an ADR for the Python 3.13 provisioning (e.g. `uv`); an ADR amendment for SQLite instead of PostgreSQL (a deviation from `DRF_SKILL.md`) and for no Redis; ADR-012 default mode = systemd; confirm port 8010.
