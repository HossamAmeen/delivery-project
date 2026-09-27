# Task

## ID
TASK-017

## Title
Rollback default target from deploy history (`PREVIOUS` recorded at switch time)

## Feature
FEAT-004 — Deployment & Environments (criteria 3 and 8: `make rollback` returns to the previous release)

## Description
Found in TASK-014: `rollback.sh` without `--to` picks the release whose **id** sorts just before `current` (`_fs_previous_of` in `deploy/scripts/lib/server.sh`), not the release that was live before the current one. After a rollback and a roll-forward the two differ. Today, `current` = `20260927-205803`, the release live before it = `20260927-205208`, and a bare `make rollback` would pick `20260927-205632` (the release that was rolled back from). ADR-013 means "the previous release" = the one that was active before the switch. `deploy.sh`'s auto-rollback already passes the correct id; only the manual default and prune's "keep previous" rule are wrong.

## Business Requirement
REQ-008; ADR-013 (rollback to the previous release), ADR-015, ADR-017; FEAT-004 criteria 3, 8

## Agent
Infrastructure

## Scope (allowed paths)
- `deploy/scripts/lib/server.sh`, `deploy/scripts/rollback.sh`, `deploy/scripts/deploy.sh`, `deploy/scripts/prune.sh`, `deploy/scripts/status.sh`, `deploy/README.md` (Rollback section), `.ai/reports/infrastructure/**`
- Server: one backfill file write under `/srv/flash/releases/` (see AC) and removal of the two `/tmp/flash-nginx-backup-*` directories left by TASK-014. Nothing else live: **no deploy, no rollback, no restart** while QA runs TASK-009/010.

## Dependencies
- TASK-014 READY_FOR_QA (done)
- **Blocks the rollback step of QA TASK-015** (that step starts only after this task is READY_FOR_QA). The rest of TASK-015 and TASK-009/010 are not blocked.

## Acceptance Criteria
- [ ] Every switch of `current` by `deploy.sh` writes `releases/<new>/PREVIOUS` containing the id that was `current` just before the switch (nothing written on the very first deploy). Written atomically, owned by `hossam`, 0644.
- [ ] `rollback.sh` without `--to` uses the current release's `PREVIOUS`. If the file is missing, or names a release that no longer exists, it **refuses** (exit 2) and tells the operator to use `make rollback TO=<id>`, listing the available releases with their `REVISION` sha and time. It never guesses by id order. `--to <id>` is unchanged. A rollback does not rewrite the target's `PREVIOUS`, so a second bare rollback walks further back in the history.
- [ ] `deploy.sh` auto-rollback keeps passing the explicit id (no behaviour change); verified by reading the code path and a dry-run.
- [ ] `prune.sh` always keeps `current` **and** the release named in its `PREVIOUS` (plus `RELEASES_TO_KEEP`).
- [ ] `make status` shows `previous: <id> (from PREVIOUS)` or `previous: unknown (no PREVIOUS)`.
- [ ] **Backfill (one-time, reviewed):** write `/srv/flash/releases/20260927-205803/PREVIOUS` = `20260927-205208` (the release that was live before 205803, per the TASK-014 deployment report/logs), with the evidence line from `FEAT-004-deploy-logs/` quoted in the Completion Report. This is a plain file write; no service, nginx or DB is touched. Run `make status` before and after.
- [ ] Remove `/tmp/flash-nginx-backup-1E2Y0T` and `/tmp/flash-nginx-backup-wBxjru` on the server (TASK-014 leftovers; nothing else under `/tmp`), and make safe-apply delete its backup directory after a successful apply (keep it only on failure, and print the path).
- [ ] Validation: `bash -n` + shellcheck clean; `--dry-run` of `rollback` (with and without `PREVIOUS`, with `TO=`), `deploy` and `prune`; a local/`/tmp/flash-*` harness (the TASK-013 style, the real library functions against a fake releases tree) proving: deploy A → deploy B → rollback (to A) → deploy C → a bare rollback picks **A** (the release live before C, not B), a second bare rollback walks further back, and a missing `PREVIOUS` refuses. Dental guard untouched (no live nginx/unit changes).
- [ ] `deploy/README.md` Rollback section updated (default target = deploy history; refusal message; `TO=`).

## Technical Notes
- ADR-013 wording is clarified by the TL in the same review: "previous release" = the one active before the last switch, recorded in `PREVIOUS`.
- Keep the TASK-013 constraints: no sudo beyond the ADR-015 list; nothing under `/etc/nginx`; never touch dental.
- Until this task is READY_FOR_QA, operators (and QA) use `make rollback TO=<id>` explicitly.

## Testing Requirements
- The harness and dry-runs above; no live rollback in this task (QA observes one in TASK-015).

## Plan Review Required
No — small, fully specified change to existing tooling within ADR-013/015

## Status

QA_IN_PROGRESS

## Activity Log
- 2026-09-28 | team-lead | — → TODO | created from the TASK-014 review (finding 1); must reach READY_FOR_QA before QA TASK-015's rollback step
- 2026-09-28 | infrastructure | TODO → IN_PROGRESS | started (no live deploy/rollback/restart/reload while QA runs)
- 2026-09-28 | infrastructure | IN_PROGRESS → READY_FOR_REVIEW | PREVIOUS recorded at deploy switch; bare rollback uses it or refuses (exit 2); prune keeps current+PREVIOUS; backfill 205803→205208 done; /tmp leftovers removed; safe-apply deletes its backup on success; evidence .ai/reports/infrastructure/TASK-017-validation-2026-09-28.md
- 2026-09-28 | team-lead | READY_FOR_REVIEW → REVIEW | code review started
- 2026-09-28 | team-lead | REVIEW → READY_FOR_QA | APPROVED; `make rollback DRY_RUN=1` targets 20260927-205208 from PREVIOUS; unblocks TASK-015's rollback step
- 2026-09-28 | qa | READY_FOR_QA → QA_IN_PROGRESS | FEAT-004 verification on the server started (TASK-015)

## Implementation Plan
(not required)

## Completion Report
- **Files changed:**
  - `deploy/scripts/lib/server.sh`:
    - new `_fs_recorded_previous` (reads and validates `releases/<id>/PREVIOUS`) and `_fs_releases_table` (every release with its REVISION sha/time, current and previous marked)
    - `_fs_switch_current <id> [record_previous]` writes `PREVIOUS` atomically (umask 022 → 0644, tmp + `mv`) only when asked, and never on a first deploy
    - `_fs_rollback`: the default target comes from `PREVIOUS`; otherwise it refuses with exit 2 and the listing; `--to` is unchanged; a rollback does not rewrite the target's `PREVIOUS`
    - `_fs_prune_releases` keeps current + its recorded `PREVIOUS`
    - `_fs_release_info` prints `previous: <id> (from PREVIOUS)` or `previous: unknown (no PREVIOUS)`, and `_fs_status` adds the release table
    - safe-apply deletes its backup dir after a successful apply and keeps it (path printed) on failure
    - `_fs_previous_of` (id-order guessing) was **removed**
  - `deploy/scripts/deploy.sh`: `_fs_switch_current "$release" 1`. The auto-rollback still passes `--to "$PREV"` (explicit id, unchanged).
  - `deploy/scripts/rollback.sh`: header text; a refusal propagates **exit 2** in both dry-run and real mode (nothing changed).
  - `deploy/README.md`: Rollback section (default = deploy history, refusal message, `TO=`, prune rule), and the safe-apply backup behaviour.
  - `prune.sh` and `status.sh` needed no change; their behaviour changed through the library.
  - Report: `.ai/reports/infrastructure/TASK-017-validation-2026-09-28.md`.
- **Live (allowed) changes:**
  - Backfill `/srv/flash/releases/20260927-205803/PREVIOUS` = `20260927-205208` (hossam, 0644, atomic). Evidence line from `FEAT-004-deploy-logs/10-deploy3.txt`: `107:current: 20260927-205208 -> 20260927-205803` (and `DEPLOY OK: release=20260927-205803 … previous=20260927-205208`). `make status`: before `previous: unknown (no PREVIOUS)`, after `previous: 20260927-205208 (from PREVIOUS)`.
  - Removed `/tmp/flash-nginx-backup-1E2Y0T` (empty) and `/tmp/flash-nginx-backup-wBxjru` (the pre-TLS Flash http files). Nothing else under `/tmp` was touched.
  - No deploy, rollback, restart or reload: flash-backend MainPID 41268 is unchanged since TASK-014; dental MainPID 18284, NRestarts 0.
- **Validation:**
  - `bash -n` on 22 files and `shellcheck -x` → clean.
  - Harness (real functions, `/tmp/flash-t017`, restart stubbed): deploy A (no PREVIOUS) → B (PREVIOUS=A) → C (PREVIOUS=B) → bare rollback → B → deploy D (PREVIOUS=**B**) → bare rollback from D → **B, not C** → second bare rollback → **A** (B's PREVIOUS untouched by the rollback) → third → **refused, exit 2** (A has no PREVIOUS, releases listed) → `--to D` works. PREVIOUS naming a deleted release → refused, exit 2. Prune with `RELEASES_TO_KEEP=2`, current D, PREVIOUS B → kept B, C, D, pruned A. All PREVIOUS files are 0644 hossam.
  - safe-apply test mode: success → "backup … removed", 0 dirs left; failure → "previous Flash files kept for inspection in …", 1 dir (then cleaned).
  - Dry-runs:
    - live bare `make rollback DRY_RUN=1` → target **20260927-205208** from PREVIOUS (before this task it would have been 205632)
    - `make rollback TO=20260927-205632 DRY_RUN=1` → that target
    - `rollback.sh --dry-run` on a `/tmp` root without PREVIOUS → refusal + listing, **exit 2**; with `--to` → exit 0
    - `make deploy DRY_RUN=1 ALLOW_DIRTY=1` → `_fs_switch_current <id> 1`
    - `make prune DRY_RUN=1` → ok
    - dental guard IDENTICAL on every guarded dry-run
  - A bug found and fixed during validation: the release listing aborted (under `pipefail`) when a release had no `REVISION`.
- **Contract/OpenAPI changes:** none.
- **Known limitations:** releases deployed before this change carry no `PREVIOUS` except the backfilled 205803. Today a bare rollback from 205208 or 205632 would therefore refuse and ask for `TO=`, which is the intended safe behaviour.

## Review Log
(team-lead)

### Review — 2026-09-28 — team-lead — code

**Verdict:** APPROVED

**Checked:**
- [x] Scope: `lib/server.sh`, `deploy.sh`, `rollback.sh`, `deploy/README.md`, the validation report. Live changes limited to the `PREVIOUS` backfill and the `/tmp/flash-nginx-backup-*` cleanup; `flash-backend` MainPID 41268 unchanged, `current` unchanged
- [x] `_fs_switch_current <id> 1` (deploy only) writes `releases/<id>/PREVIOUS` atomically (tmp + `mv -f`, umask 022 → 0644), not on the first deploy or a same-id switch; rollbacks pass 0, so the target's `PREVIOUS` is kept and a second bare rollback walks back
- [x] `_fs_recorded_previous` validates presence, id format and existence; a bare rollback without a valid `PREVIOUS` refuses with exit 2 before any change and lists the releases with sha and build time; id-order guessing (`_fs_previous_of`) is removed everywhere (rollback, prune, status)
- [x] `rollback.sh` maps a refusal to exit 2 ("nothing changed") and closes the dental guard; other failures stay exit 1; `--to` unchanged; deploy's auto-rollback still passes the explicit id
- [x] Prune keeps current + recorded `PREVIOUS` + the newest `RELEASES_TO_KEEP`
- [x] Safe-apply deletes its backup after a successful apply and keeps it (path printed) on failure
- [x] Harness evidence (`TASK-017-validation-2026-09-28.md`, real `lib/server.sh` against `/tmp/flash-t017`): A→B→rollback→C→bare rollback picks A-side history correctly, the 2nd bare rollback walks back, a missing/dangling `PREVIOUS` refuses, prune keeps the recorded previous
- [x] ADR-013 clarification (2026-09-28) implemented; README Rollback/Resource sections match
- [x] No secrets; no nginx/unit/DB change; dental untouched

**Findings:** none.

**Commands run (read-only; no rollback, deploy, restart or reload — QA TASK-009/010 running):**
```
bash -n on all deploy/scripts/*.sh and lib/*.sh      → OK
shellcheck -x (0.11.0) on all scripts                → clean, EXIT 0
make status   → current 20260927-205803; previous 20260927-205208 (from PREVIOUS); table marks both; MainPID 41268, active
make rollback DRY_RUN=1
              → "target from releases/20260927-205803/PREVIOUS: 20260927-205208";
                "rollback: 20260927-205803 -> 20260927-205208 (mode=auto, … applied migrations: no, restore DB: no)";
                "plan only: nothing changed"; dental guard before/after IDENTICAL (33 entries)          EXIT 0
ssh (read-only): current → releases/20260927-205803; MainPID 41268; releases/20260927-205803/PREVIOUS 0644 hossam = 20260927-205208;
                 /tmp/flash-nginx-backup-* count 0
```

## QA Log
- 2026-09-28 | qa | IN PROGRESS | PREVIOUS file, make status line, rollback dry-run target 20260927-205208 + DB decision, /tmp cleanup: PASS; live bare rollback + roll-forward pending (permission)

## Sign-off
- TL final review: ☐
- QA verdict: ☐
- PM acceptance: ☐
