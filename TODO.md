# Flash — what's needed to finish the deployment

Status on 2026-09-27: **nothing is deployed yet.** The code, the deploy scripts and the server setup are ready. These items are waiting on the owner.

## 1. Decisions the owner needs to make (blocking)

- [ ] **Allow the server test and deploy commands.** The permission policy denied these for the Team Lead and QA agents:
  - `make test-backend-remote …` (backend tests on the server; needed for the TL's approval of TASK-001 to 005)
  - `make qa-remote …` (QA on the server; TASK-008, 009, 010, 015)
  - `make seed-qa-users`, `make throttle-reset`
  - `make setup-server`, `make deploy`, `make tls`, `make rollback`, `make health`, `make migrate`, `make restart` (TASK-014)

  To allow them, add this to `.claude/settings.local.json` (or approve each prompt as it appears):
  ```json
  {
    "permissions": {
      "allow": [
        "Bash(make test-backend-remote:*)",
        "Bash(make qa-remote:*)",
        "Bash(make seed-qa-users:*)",
        "Bash(make throttle-reset:*)",
        "Bash(make setup-server:*)",
        "Bash(make deploy:*)",
        "Bash(make tls:*)",
        "Bash(make rollback:*)",
        "Bash(make health:*)",
        "Bash(make migrate:*)",
        "Bash(make restart:*)",
        "Bash(make status:*)"
      ]
    }
  }
  ```

- [ ] **Approve a local git commit** of `backend/`, `frontend/`, `qa/`, `deploy/`, `Makefile`, `.env.example`, `.ai/` and `TODO.md` on `main`. `make deploy` refuses uncommitted code. Nothing gets pushed, because there is no remote.

## 2. What happens after that (the agents do it)

1. [ ] TL runs the backend tests on the server and gives the verdicts for TASK-001 to 005
2. [ ] QA's collection check on the server for TASK-008, then TL verdict
3. [ ] Backend TASK-016: the `create_role_user --inactive` flag used by the `qa_inactive` QA user
4. [ ] Local commit
5. [ ] Infrastructure TASK-014:
   - add the HTTP/2 guard and the dirty-tree check
   - `setup-server`, then the first deploy (systemd `flash-backend` on 127.0.0.1:8010, and nginx for both domains)
   - Let's Encrypt HTTPS for `api.delivery.hossam-ameen.online` and `delivery.hossam-ameen.online` (reusing the server's existing ACME account)
   - seed the QA users
   - run a live rollback and roll-forward
   - confirm dental-clinic is unaffected
6. [ ] QA on the server: TASK-015 (deploy, TLS, rollback, dental), TASK-009 (backend API), TASK-010 (PWA E2E), and the rate-limit suite last
7. [ ] TL final sign-off, then PM acceptance, then DONE

## 3. Open later (not blocking this deployment)

- [ ] **BLK-012:** pick a git provider and remote (GitHub/GitLab) to unblock CI (TASK-011)
- [ ] **BLK-007:** onboarding and accounts (needed for FEAT-002 registration in sprint-02)
- [ ] **BLK-009:** language and currency (the UI is English-only for now)
- [ ] **BLK-003 / 004 / 005 / 006 / 008 / 010:** pricing and fees, payment methods, cancellation and terminal states, assignment strategy, order scope, notifications (needed for later sprints)
- [ ] Confirm the sprint-01 dates (proposed: 2026-09-28 to 2026-10-09)
- [ ] Copy the BLK-001 and BLK-002 decisions into `flash_business_logic/` (canonical docs, PM task)
- [ ] Future hardening: move the refresh token to an httpOnly cookie and add a logout/blacklist endpoint before real customer data exists
- [ ] Future: PostgreSQL/Redis instead of SQLite and a file cache; HTTP/2 only with the dental owner's consent

## Reference

- Server: `hossam@34.123.215.195` (key `~/.ssh/id_ed25519`), shared with the dental-clinic app, which must never be touched
- Flash layout: `/srv/flash/{current,releases,shared,sandbox,qa}`, with the backend on `127.0.0.1:8010`
- Details: `deploy/README.md`, `.ai/planning/sprints/sprint-01.md`, and the task files in `.ai/tasks/`
