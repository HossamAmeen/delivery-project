#!/usr/bin/env bash
# Flash deploy (systemd mode, ADR-013/015/017). Single entry point; hides the mode.
#   preflight (env, mode, clean tree, SSH, disk ≥ MIN_FREE_DISK_MB, dental snapshot + port guard)
#   → deploy-frontend.sh (local PWA build) → stage git archive backend/ + frontend/dist + REVISION
#   → rsync to releases/<UTC ts> (--link-dest previous) → deploy-backend.sh (venv, check --deploy, collectstatic)
#   → migrate.sh (SQLite backup + migrate) → atomic switch of current → restart backend
#   → nginx safe-apply (only if the rendered files changed) → health-check.sh (HEALTH_CHECK_TIMEOUT)
#   → dental compare → prune.sh → summary.
# Failure before the switch: the half-built release is removed, the live site is untouched, exit 1.
# Failure after the switch: AUTO_ROLLBACK=true → rollback.sh to the previous release; exit 1 either way.
# Usage: deploy.sh [--allow-dirty] [--dry-run]
#   --allow-dirty  accept uncommitted changes in backend/ frontend/ deploy/ Makefile (the working tree of
#                  backend/ and frontend/ is shipped; recorded as dirty=true + dirty_paths in REVISION)
FLASH_SCRIPT=deploy
set -euo pipefail
# shellcheck source=lib/common.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib/common.sh"
# shellcheck source=lib/ops.sh
source "$FLASH_LIB_DIR/ops.sh"
trap ops_cleanup EXIT

allow_dirty=0
while (($#)); do
  parse_common_flag "$1" && { shift; continue; }
  case "$1" in
    --allow-dirty) allow_dirty=1; shift ;;
    -h|--help) sed -n '2,13p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) die "unknown argument: $1" 2 ;;
  esac
done
ops_init VITE_API_BASE_URL AUTO_ROLLBACK
case "$AUTO_ROLLBACK" in true|false) ;; *) die "AUTO_ROLLBACK must be true or false" 2 ;; esac
t0="$(date +%s)"
release="$(date -u +%Y%m%d-%H%M%S)"
SWITCHED=0; CREATED=0; PREV=""

deploy_fail() { # <what failed>
  err "DEPLOY FAILED at: $1 (release $release)"
  if [[ "$SWITCHED" == 0 ]]; then
    if [[ "$CREATED" == 1 ]]; then ops_remote rw _fs_remove_release "$release" >&2 || warn "could not remove releases/$release"; fi
    err "the live site was NOT changed (current is still ${PREV:-none})"
  elif [[ "$AUTO_ROLLBACK" == true && -n "$PREV" ]]; then
    warn "AUTO_ROLLBACK=true → rolling back to $PREV"
    if run_script rollback.sh --to "$PREV"; then err "ROLLBACK OUTCOME: rolled back to $PREV, health OK"
    else err "ROLLBACK OUTCOME: rollback to $PREV FAILED — manual action needed"; fi
  elif [[ -z "$PREV" ]]; then
    err "first deploy: there is no previous release to roll back to"
  else
    print_rollback_hint
  fi
  ops_guard_end || true
  exit 1
}

# ------------------------------------------------------------------ preflight
step "preflight"
cd "$REPO_ROOT"
sha="$(git rev-parse HEAD)" || die "not a git repository" 2
git cat-file -e "HEAD:backend/requirements/production.txt" 2>/dev/null || [[ $allow_dirty == 1 ]] \
  || die "HEAD has no backend/requirements/production.txt — commit the backend first (or --allow-dirty)" 2
# Release content (backend/, frontend/) AND the tooling that deploys it (deploy/, root Makefile) must be committed,
# so the release of record is reproducible from one sha. The result is recorded in REVISION.
dirty_paths=(backend frontend deploy Makefile)
dirty_files="$(git status --porcelain -- "${dirty_paths[@]}" | wc -l)"
dirty_list="$(git status --porcelain -- "${dirty_paths[@]}" | awk '{print $2}' | cut -d/ -f1 | sort -u | paste -sd, -)"
dirty=false
if [[ "$dirty_files" -gt 0 ]]; then
  [[ $allow_dirty == 1 ]] || die "uncommitted change(s) in ${dirty_list} ($dirty_files path(s)) — commit them or use --allow-dirty" 2
  dirty=true; warn "--allow-dirty: $dirty_files uncommitted path(s) in ${dirty_list} (backend/ and frontend/ shipped from the working tree)"
fi
info "release $release from ${sha:0:12} (dirty=$dirty) → $(ssh_target):$DEPLOY_PATH"
check_ssh
free="$(ops_remote ro _fs_disk_free_mb)"
((free >= MIN_FREE_DISK_MB)) || die "only ${free} MB free on the server (< MIN_FREE_DISK_MB=$MIN_FREE_DISK_MB)" 1
ops_remote ro _fs_release_info >&2
PREV="$(ops_remote ro _fs_current_id || true)"
ops_lock
ops_guard_begin

# ------------------------------------------------------------------ build + stage (local)
step "build frontend (local) and stage release"
stage="$(ops_mktemp release)"
run_script deploy-frontend.sh --out "$stage" || deploy_fail "frontend build"
if [[ "$dirty" == true ]]; then
  tar -C "$REPO_ROOT" --exclude=.env --exclude='*.sqlite3' --exclude=__pycache__ --exclude=.venv --exclude=venv \
      --exclude=.pytest_cache --exclude=.ruff_cache --exclude=.remote-results --exclude=htmlcov --exclude=.coverage \
      -cf - backend | tar -x -C "$stage"
else
  git archive --format=tar "$sha" backend | tar -x -C "$stage"
fi
printf 'release=%s\nsha=%s\ndirty=%s\ndirty_paths=%s\ndirty_checked=%s\nbuilt_at=%s\nbuilt_by=%s@%s\nvite_api_base_url=%s\n' \
  "$release" "$sha" "$dirty" "${dirty_list:-none}" "${dirty_paths[*]}" "$(date -u +%FT%TZ)" "$(id -un)" "$(hostname -s)" \
  "$VITE_API_BASE_URL" > "$stage/REVISION"
sed 's/^/  REVISION /' "$stage/REVISION" >&2
info "staged: backend $(find "$stage/backend" -type f | wc -l) files, frontend/dist $(find "$stage/frontend/dist" -type f 2>/dev/null | wc -l) files"

# ------------------------------------------------------------------ upload
step "upload to releases/$release"
ops_remote rw _fs_prepare_release_dir "$release" || deploy_fail "create release dir"
CREATED=1
ssh_opts
link_dest=(); [[ -n "$PREV" ]] && link_dest=(--link-dest="$DEPLOY_PATH/releases/$PREV/")
run rsync -a --delete --chmod=Du=rwx,Dgo=rx,Fu=rw,Fgo=r "${link_dest[@]}" \
  -e "ssh $(_quote_cmd "${SSH_OPTS[@]}")" "$stage/" "$(ssh_target):$DEPLOY_PATH/releases/$release/" \
  || deploy_fail "rsync"

# ------------------------------------------------------------------ server build + migrate (old release still serving)
step "server: venv, check --deploy, collectstatic"
run_script deploy-backend.sh --release "$release" || deploy_fail "deploy-backend"
step "server: migrations (backup first)"
run_script migrate.sh --release "$release" || deploy_fail "migrate"

# ------------------------------------------------------------------ switch + restart
step "switch current → $release"
ops_remote rw _fs_switch_current "$release" 1 || deploy_fail "switch current"   # 1 = record PREVIOUS
SWITCHED=1
run_script restart-backend.sh || deploy_fail "restart backend"

step "nginx (safe-apply only if the rendered files changed)"
variant="$(ops_remote ro _fs_cert_state)"
ops_render
ops_stage_upload "$OPS_RENDER_DIR/nginx/$variant" || deploy_fail "upload nginx files"
ops_remote rw _fs_nginx_safe_apply "$OPS_STAGE" 0 || { ops_stage_cleanup; deploy_fail "nginx safe-apply"; }
ops_stage_cleanup

step "health"
run_script health-check.sh --timeout "$HEALTH_CHECK_TIMEOUT" || deploy_fail "health check"

ops_guard_end
step "prune"
run_script prune.sh || warn "prune failed (deploy itself succeeded)"

if is_dry_run; then info "DRY-RUN complete: nothing was changed (release id $release would be created from ${sha:0:12}, dirty=$dirty)"; exit 0; fi
info "DEPLOY OK: release=$release sha=${sha:0:12} dirty=$dirty previous=${PREV:-none} duration=$(( $(date +%s) - t0 ))s health=PASS"
