# TASK-017 — validation evidence (2026-09-28)

No deploy, rollback, restart or nginx reload was performed on the live site (QA TASK-009/010 running). Live changes: the backfill file and the removal of 2 `/tmp` leftovers. flash-backend MainPID 41268 is unchanged since TASK-014; dental MainPID 18284, NRestarts 0.

## Harness (real lib/server.sh against /tmp/flash-t017; `_fs_restart_backend` stubbed)
```
test root with releases A..D (=…0001..0004)
2026-09-27T22:52:19Z [t017] ----- deploy A (first: no PREVIOUS)
current: none -> 20260101-000001
2026-09-27T22:52:19Z [t017] ----- deploy B
recorded: releases/20260101-000002/PREVIOUS = 20260101-000001
current: 20260101-000001 -> 20260101-000002
2026-09-27T22:52:20Z [t017] ----- deploy C
recorded: releases/20260101-000003/PREVIOUS = 20260101-000002
current: 20260101-000002 -> 20260101-000003
  20260101-000001 PREVIOUS=<none> 
  20260101-000002 PREVIOUS=20260101-000001 644 hossam
  20260101-000003 PREVIOUS=20260101-000002 644 hossam
  20260101-000004 PREVIOUS=<none> 
  current -> 20260101-000003
2026-09-27T22:52:21Z [t017] ----- bare rollback from C → expect B (C/PREVIOUS)
[remote] target from releases/20260101-000003/PREVIOUS: 20260101-000002
[remote] rollback: 20260101-000003 -> 20260101-000002 (mode=auto, 20260101-000003 applied migrations: no, restore DB: no)
[stub] restart skipped (harness)
ROLLBACK_RESULT from=20260101-000003 to=20260101-000002 db_restored=0
2026-09-27T22:52:21Z [t017] ----- deploy D (current before = B)
recorded: releases/20260101-000004/PREVIOUS = 20260101-000002
current: 20260101-000002 -> 20260101-000004
  20260101-000001 PREVIOUS=<none> 
  20260101-000002 PREVIOUS=20260101-000001 644 hossam
  20260101-000003 PREVIOUS=20260101-000002 644 hossam
  20260101-000004 PREVIOUS=20260101-000002 644 hossam
  current -> 20260101-000004
current:  20260101-000004
previous: 20260101-000002 (from PREVIOUS)
2026-09-27T22:52:22Z [t017] ----- bare rollback from D → expect B (live before D), NOT C (id order)
[remote] target from releases/20260101-000004/PREVIOUS: 20260101-000002
[remote] rollback: 20260101-000004 -> 20260101-000002 (mode=auto, 20260101-000004 applied migrations: no, restore DB: no)
[stub] restart skipped (harness)
ROLLBACK_RESULT from=20260101-000004 to=20260101-000002 db_restored=0
2026-09-27T22:52:23Z [t017] ----- 2nd bare rollback from B → expect A (walks further back; B/PREVIOUS unchanged by the rollback)
[remote] target from releases/20260101-000002/PREVIOUS: 20260101-000001
[remote] rollback: 20260101-000002 -> 20260101-000001 (mode=auto, 20260101-000002 applied migrations: no, restore DB: no)
[stub] restart skipped (harness)
ROLLBACK_RESULT from=20260101-000002 to=20260101-000001 db_restored=0
2026-09-27T22:52:23Z [t017] ----- 3rd bare rollback from A → expect REFUSAL exit 2 (A has no PREVIOUS)
[remote] ERROR: no recorded previous release for 20260101-000001 (release 20260101-000001 has no PREVIOUS file).
[remote] Refusing to guess by release-id order. Choose the target explicitly: make rollback TO=<id>
[remote] Available releases:
  20260101-000001  sha=000000000000  built=2026-01-01T00:00:01Z <- current
  20260101-000002  sha=000000000000  built=2026-01-01T00:00:02Z
  20260101-000003  sha=000000000000  built=2026-01-01T00:00:03Z
  20260101-000004  sha=000000000000  built=2026-01-01T00:00:04Z
  exit=2
2026-09-27T22:52:24Z [t017] ----- explicit TO=D from A (unchanged --to behaviour)
[remote] rollback: 20260101-000001 -> 20260101-000004 (mode=auto, 20260101-000001 applied migrations: no, restore DB: no)
[stub] restart skipped (harness)
ROLLBACK_RESULT from=20260101-000001 to=20260101-000004 db_restored=0
  20260101-000001 PREVIOUS=<none> 
  20260101-000002 PREVIOUS=20260101-000001 644 hossam
  20260101-000003 PREVIOUS=20260101-000002 644 hossam
  20260101-000004 PREVIOUS=20260101-000002 644 hossam
  current -> 20260101-000004
2026-09-27T22:52:25Z [t017] ----- PREVIOUS naming a release that no longer exists → refusal
D/PREVIOUS -> 20250101-000000 (nonexistent)
[remote] ERROR: no recorded previous release for 20260101-000004 (releases/20260101-000004/PREVIOUS names 20250101-000000, which no longer exists).
[remote] Refusing to guess by release-id order. Choose the target explicitly: make rollback TO=<id>
[remote] Available releases:
  20260101-000001  sha=000000000000  built=2026-01-01T00:00:01Z
  20260101-000002  sha=000000000000  built=2026-01-01T00:00:02Z
  20260101-000003  sha=000000000000  built=2026-01-01T00:00:03Z
  20260101-000004  sha=000000000000  built=2026-01-01T00:00:04Z <- current
  exit=2
D/PREVIOUS restored
2026-09-27T22:52:27Z [t017] ----- prune RELEASES_TO_KEEP=2 with current=D, PREVIOUS=B → keep C,D (newest) + B (PREVIOUS), prune A
pruned release 20260101-000001
releases kept: 20260101-000002 20260101-000003 20260101-000004 (current=20260101-000004 previous=20260101-000002)
  20260101-000002 PREVIOUS=20260101-000001 644 hossam
  20260101-000003 PREVIOUS=20260101-000002 644 hossam
  20260101-000004 PREVIOUS=20260101-000002 644 hossam
  current -> 20260101-000004
removed /tmp/flash-t017
```

## safe-apply backup cleanup (test mode, /tmp/flash-t017-nginx)
```
/tmp/flash-nginx-backup-1E2Y0T: 
/tmp/flash-nginx-backup-wBxjru: api.delivery.hossam-ameen.online.conf api.delivery.hossam-ameen.online.link delivery.hossam-ameen.online.conf delivery.hossam-ameen.online.link 
remaining /tmp/flash-*: 
pre-existing backup dirs (TASK-014 leftovers): 0
backup dirs in /tmp: 0
### success
nginx: backup of the previous Flash files in /tmp/flash-nginx-backup-QQ60An
nginx: TEST MODE — reload skipped
nginx: backup /tmp/flash-nginx-backup-QQ60An removed (apply succeeded)
backup dirs in /tmp: 0
### failure
nginx: backup of the previous Flash files in /tmp/flash-nginx-backup-b4cBhM
[remote] nginx -t FAILED — restoring the previous Flash files, NOT reloading
[remote] previous Flash files kept for inspection in /tmp/flash-nginx-backup-b4cBhM
backup dirs in /tmp: 1
cleaned
```

## Backfill
Evidence (`.ai/reports/infrastructure/FEAT-004-deploy-logs/10-deploy3.txt`):
```
107:current: 20260927-205208 -> 20260927-205803
130:2026-09-27T20:58:46Z [deploy] INFO  DEPLOY OK: release=20260927-205803 sha=f85848b9bbdb dirty=false previous=20260927-205208 duration=43s health=PASS
```
`make status` before:
```
== releases
   current:  20260927-205803
   previous: unknown (no PREVIOUS)
   releases: 20260927-205208 20260927-205632 20260927-205803 
   disk:     11172 MB free on /srv/flash (min 1500)
   20260927-205208  sha=f85848b9bbdb  built=2026-09-27T20:52:31Z
   20260927-205632  sha=f85848b9bbdb  built=2026-09-27T20:56:54Z
   20260927-205803  sha=f85848b9bbdb  built=2026-09-27T20:58:29Z <- current
```
Write (atomic):
```
hossam:hossam 644 /srv/flash/releases/20260927-205803/PREVIOUS
20260927-205208
```
`make status` after:
```
== releases
   current:  20260927-205803
   previous: 20260927-205208 (from PREVIOUS)
   releases: 20260927-205208 20260927-205632 20260927-205803 
   disk:     11183 MB free on /srv/flash (min 1500)
   20260927-205208  sha=f85848b9bbdb  built=2026-09-27T20:52:31Z <- previous (PREVIOUS)
   20260927-205632  sha=f85848b9bbdb  built=2026-09-27T20:56:54Z
   20260927-205803  sha=f85848b9bbdb  built=2026-09-27T20:58:29Z <- current
```

## Dry-runs
```
### make rollback TO=20260927-205632 DRY_RUN=1
[remote] rollback: 20260927-205803 -> 20260927-205632 (mode=auto, 20260927-205803 applied migrations: no, restore DB: no)
[remote] plan only: nothing changed
exit=0
test root /tmp/flash-t017b: current=20260101-000002 without PREVIOUS
### rollback.sh --dry-run, no PREVIOUS (DEPLOY_PATH=/tmp/flash-t017b)
current:  20260101-000002
previous: unknown (no PREVIOUS)
[remote] ERROR: no recorded previous release for 20260101-000002 (release 20260101-000002 has no PREVIOUS file).
[remote] Refusing to guess by release-id order. Choose the target explicitly: make rollback TO=<id>
[remote] Available releases:
2026-09-27T22:50:57Z [rollback] ERROR rollback is not possible (see above)
exit=2
### same with --to 20260101-000001
[remote] rollback: 20260101-000002 -> 20260101-000001 (mode=auto, 20260101-000002 applied migrations: no, restore DB: no)
[remote] plan only: nothing changed
exit=0
removed /tmp/flash-t017b; /tmp/flash-*: 0
### make deploy DRY_RUN=1 ALLOW_DIRTY=1 (switch records PREVIOUS)
previous: 20260927-205208 (from PREVIOUS)
2026-09-27T22:51:06Z [deploy] [dry-run] remote(hossam@34.123.215.195): _fs_switch_current 20260927-225102 1
2026-09-27T22:51:08Z [deploy] INFO  dental guard: before/after IDENTICAL (33 entries)
2026-09-27T22:51:08Z [deploy] INFO  DRY-RUN complete: nothing was changed (release id 20260927-225102 would be created from f85848b9bbdb, dirty=true)
exit=0
### make prune DRY_RUN=1
2026-09-27T22:51:08Z [prune] [dry-run] remote(hossam@34.123.215.195): _fs_prune_releases
2026-09-27T22:51:08Z [prune] [dry-run] remote(hossam@34.123.215.195): _fs_prune_backups
exit=0
### deploy auto-rollback code path
44:    if run_script rollback.sh --to "$PREV"; then err "ROLLBACK OUTCOME: rolled back to $PREV, health OK"
76:PREV="$(ops_remote ro _fs_current_id || true)"
current:  20260101-000002
[remote] ERROR: no recorded previous release for 20260101-000002 (release 20260101-000002 has no PREVIOUS file).
[remote] Refusing to guess by release-id order. Choose the target explicitly: make rollback TO=<id>
[remote] Available releases:
  20260101-000001  sha=abcdef012345  built=2026-01-01T00:00:01Z
  20260101-000002  sha=?  built=? <- current
2026-09-27T22:51:30Z [rollback] ERROR rollback is not possible (see above)
exit=2
```

## Live state after
```
flash-backend active MainPID=41268 NRestarts=1 ActiveEnterTimestamp=Sun 2026-09-27 20:59:08 UTC 
dental active MainPID=18284 NRestarts=0 
releases/20260927-205803
0
```
