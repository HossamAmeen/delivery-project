# Flash — Delivery Platform

Flash is a delivery platform with four roles: **Customer, Store, Driver and Admin**.
It is built by a controlled team of Claude Code agents (PM, Team Lead, Backend, Frontend, Fullstack, QA, Infrastructure) that hand work to each other only through files in this repository.

- PWA: https://delivery.hossam-ameen.online
- API: https://api.delivery.hossam-ameen.online (status: `/api/status/`)

## Repository layout

| Folder | What it holds | Owner |
|---|---|---|
| `docs/business/` | Canonical business rules: core domain, per-app rules, cross-app flows, QA contract | PM, after Product Owner approval |
| `docs/design/` | Brand assets (initial logo). The PWA icons are generated from it | PM / Product Owner |
| `docs/standards/` | Engineering standards: `DRF_SKILL.md`, the mandatory backend standard | Team Lead |
| `backend/` | Django REST Framework API | Backend |
| `frontend/` | Vue 3 PWA (customer, driver, store and admin areas) | Frontend |
| `qa/` | Black-box QA suite (pytest + httpx, Playwright) that runs on the server | QA |
| `deploy/`, `Makefile`, `.env.example` | Deployment tooling (systemd mode on the VPS) | Infrastructure |
| `.ai/` | Team operating system: plans, architecture/ADRs/contracts, tasks, reports, templates | PM / TL |
| `.claude/agents/` | The seven subagents | TL |
| `.claude/skills/` | Project skills: procedures each agent preloads | TL |

## How work flows

```
PM (feature, sprint) → TL (design, contracts, tasks) → developers / infrastructure
→ TL code review → QA on the server → TL final sign-off → PM acceptance → DONE
```

- Start with [`CLAUDE.md`](CLAUDE.md) (orchestration rules and current state), then [`.ai/README.md`](.ai/README.md) (statuses, IDs, ownership, Definition of Done).
- Business gaps become blockers in `.ai/planning/blockers/`. They are never guessed.

## Skills

**Project skills** in `.claude/skills/` are attached to each agent through the `skills:` field in `.claude/agents/*.md`:

| Agent | Skills |
|---|---|
| All | `flash-workflow` |
| Project Manager | `pm-feature`, `pm-sprint`, `pm-acceptance` |
| Team Lead | `tl-design-breakdown`, `tl-review`, `tl-bug-routing-signoff`, `drf-standard` |
| Backend | `backend-task`, `backend-state-money`, `drf-standard` |
| Frontend | `frontend-screen` |
| Fullstack | `fullstack-slice` + the Backend and Frontend skills |
| QA | `qa-test-plan`, `qa-verify` |
| Infrastructure | `infra-change`, `infra-deploy-verify` |

**Built-in Claude Code skills** fit in as follows:
- `/code-review` and `/security-review` are extra checks before release. They do not replace the TL review or QA.
- `/simplify` is a pre-review cleanup.
- `/run` is a local PWA preview only.
- `/update-config` is for permissions and hooks.

See [`CLAUDE.md` § Skills](CLAUDE.md#skills) for the rules.

## Common commands (repository root)

The **local machine only builds**. Tests and QA run on the server (ADR-018).

```bash
make help                                   # list the ops targets
make test-backend-remote WORKTREE=1         # backend lint, check, migrations check, pytest on the server
make qa-remote ARGS="-m 'smoke or deploy'"  # QA suite on the server against the live URLs
make status && make health                  # read-only state and health of the deployment
cd frontend && npm run lint && npm run type-check && npm run test:unit && npm run build-only
```

`make deploy`, `make rollback`, `make restart` and `make migrate` are live production actions, and the operator runs them. See [`deploy/README.md`](deploy/README.md).
