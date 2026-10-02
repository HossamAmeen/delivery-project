### Review — YYYY-MM-DD — team-lead — (plan | code | final)

**Verdict:** APPROVED / CHANGES_REQUESTED

**Checked:**
- [ ] Scope limited to the task; no unrelated changes
- [ ] Business rules match `business-logic.md` / `docs/business/` (none invented)
- [ ] Authorization: authenticated → role → ownership → state transition → business constraints
- [ ] State transitions go through a service, are locked, write history, are idempotent
- [ ] Money: Decimal, explicit currency, snapshots, ledger with idempotency key
- [ ] API contract matches `api-contracts.md` and OpenAPI; standard envelope; 429 documented
- [ ] Tests are meaningful and cover happy, negative and edge cases; validation commands pass
- [ ] Migrations present and `makemigrations --check` passes; no destructive migration
- [ ] No hardcoded secrets, domains, ports, paths
- [ ] Complies with `docs/standards/DRF_SKILL.md` (backend) / frontend ADRs (frontend) / ADR-012–014 and the infra DoD (infrastructure)
- [ ] Infra: no secrets in workflows/templates/scripts, `DEPLOYMENT_MODE` respected, both modes validated, rollback path intact

**Findings:**
1. [blocking|non-blocking] file:line — issue — required change

**Commands run:** …
