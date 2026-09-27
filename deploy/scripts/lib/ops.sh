# shellcheck shell=bash
# Local helpers shared by the operator scripts (TASK-013). Requires lib/common.sh.
# Sources lib/dental_guard.sh, lib/templates.sh and lib/server.sh.

# shellcheck source=lib/dental_guard.sh
source "$FLASH_LIB_DIR/dental_guard.sh"
# shellcheck source=lib/templates.sh
source "$FLASH_LIB_DIR/templates.sh"
# shellcheck source=lib/server.sh
source "$FLASH_LIB_DIR/server.sh"

FLASH_OPS_VARS=(API_DOMAIN WEB_DOMAIN BACKEND_PORT BACKEND_SYSTEMD_SERVICE CERT_NAME RELEASES_TO_KEEP
                DB_BACKUPS_TO_KEEP HEALTH_CHECK_TIMEOUT MIN_FREE_DISK_MB)

# ops_init [extra required vars...]: env + mode (docker/missing → exit 2) + required variables.
ops_init() {
  load_env
  validate_common "${FLASH_OPS_VARS[@]}" "$@"
  local v
  for v in RELEASES_TO_KEEP DB_BACKUPS_TO_KEEP HEALTH_CHECK_TIMEOUT MIN_FREE_DISK_MB BACKEND_PORT; do
    [[ "${!v}" =~ ^[0-9]+$ ]] || die "$v must be an integer (got '${!v}')" 2
  done
  ((RELEASES_TO_KEEP >= 2)) || die "RELEASES_TO_KEEP must be >= 2 (current + previous)" 2
}

# ops_remote <ro|rw> <_fs_function> [args...]: ships every _fs_* function + the ops variables.
ops_remote() {
  local mode="$1"; shift
  local -a funcs
  mapfile -t funcs < <(compgen -A function _fs_)
  # shellcheck disable=SC2034  # read by remote_fn through dynamic scope
  local REMOTE_FUNCS=("${funcs[@]}")
  # shellcheck disable=SC2034
  local REMOTE_VARS=(DEPLOY_PATH API_DOMAIN WEB_DOMAIN BACKEND_PORT BACKEND_SYSTEMD_SERVICE CERT_NAME
                     UV_BIN PYTHON_VERSION RELEASES_TO_KEEP DB_BACKUPS_TO_KEEP MIN_FREE_DISK_MB)
  remote_fn "$mode" "$@"
}

# One Flash operation at a time from this machine (children inherit the lock).
ops_lock() {
  [[ "${FLASH_OPS_LOCKED:-0}" == 1 ]] && return 0
  local lf="${TMPDIR:-/tmp}/flash-ops.lock"
  exec 8>"$lf"
  flock -n 8 || die "another Flash operation holds $lf — wait for it to finish" 1
  export FLASH_OPS_LOCKED=1
}

# Dental guard with nesting: the outermost script snapshots; children called by it skip.
OPS_GUARD_OWNER=0
ops_guard_begin() {
  if [[ "${FLASH_GUARD_ACTIVE:-0}" == 1 ]]; then info "dental guard: handled by the calling script"; return 0; fi
  dental_guard_begin
  OPS_GUARD_OWNER=1
  export FLASH_GUARD_ACTIVE=1
}
ops_guard_end() { [[ "$OPS_GUARD_OWNER" == 1 ]] && dental_guard_end; return 0; }

# ops_render → sets OPS_RENDER_DIR (local, removed on exit by ops_cleanup)
OPS_TMP_DIRS=()
ops_cleanup() { local d; for d in "${OPS_TMP_DIRS[@]}"; do [[ -n "$d" ]] && rm -rf -- "$d"; done; }
ops_mktemp() { local d; d="$(mktemp -d "${TMPDIR:-/tmp}/flash-$1-XXXXXX")"; OPS_TMP_DIRS+=("$d"); printf '%s' "$d"; }
ops_render() {
  OPS_RENDER_DIR="$(ops_mktemp render)"
  render_all "$OPS_RENDER_DIR"
}

# ops_stage_upload <local dir> → sets OPS_STAGE (server path). rw: nothing is sent under --dry-run.
ops_stage_upload() {
  OPS_STAGE="/tmp/flash-stage-$(new_run_id)-$(od -An -N4 -tx4 /dev/urandom | tr -d " ")"
  if is_dry_run; then log "[dry-run] upload $1 → $(ssh_target):$OPS_STAGE"; return 0; fi
  tar -C "$1" -czf - . | ops_remote rw _fs_receive_stage "$OPS_STAGE"
}
ops_stage_cleanup() { [[ -n "${OPS_STAGE:-}" ]] && ops_remote rw _fs_cleanup_stage "$OPS_STAGE"; return 0; }

sha_of() { sha256sum < "$1" | cut -d' ' -f1; }

# Prints the command to roll back (used by every failure path).
print_rollback_hint() { err "to roll back manually: make rollback   (or deploy/scripts/rollback.sh [--to <release-id>])"; }

# Runs a sibling script, propagating --dry-run (DRY_RUN is exported) and the lock/guard state.
run_script() { local s="$1"; shift; DRY_RUN="$DRY_RUN" "$FLASH_SCRIPTS_DIR/$s" "$@"; }
