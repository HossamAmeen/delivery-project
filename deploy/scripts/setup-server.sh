#!/usr/bin/env bash
# Flash server setup (idempotent, dental-guarded; re-running changes nothing).
#   Bootstrap (TASK-012): /srv/flash layout with the ADR-015 permission modes (existing dirs are fixed,
#   then verified, incl. www-data access checks) → uv ${UV_VERSION} for SERVER_USER → uv python ${PYTHON_VERSION}.
#   Full (TASK-013): shared/.env from deploy/env/shared.env.template ONLY IF ABSENT (secrets generated on the
#   server; if present, missing keys are reported, nothing is overwritten) → systemd unit installed to
#   /etc/systemd/system/${BACKEND_SYSTEMD_SERVICE}.service, daemon-reload, enable (restarted only when a
#   current release exists) → both Flash nginx sites via the safe-apply (port-80 variant until the
#   certificate exists, TLS variant after) → optional --with-e2e (Playwright Chromium + apt deps).
# Usage: setup-server.sh [--bootstrap-only] [--with-e2e] [--dry-run]
set -euo pipefail
FLASH_SCRIPT=setup-server
# shellcheck source=lib/common.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib/common.sh"
# shellcheck source=lib/ops.sh
source "$FLASH_LIB_DIR/ops.sh"
trap ops_cleanup EXIT

usage() { sed -n '2,10p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; }
bootstrap_only=0; with_e2e=0
while (($#)); do
  parse_common_flag "$1" && { shift; continue; }
  case "$1" in
    --bootstrap-only) bootstrap_only=1; shift ;;
    --with-e2e) with_e2e=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "unknown argument: $1" 2 ;;
  esac
done
[[ $bootstrap_only == 1 && $with_e2e == 1 ]] && die "--with-e2e cannot be combined with --bootstrap-only" 2

ops_init UV_VERSION
[[ "$UV_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || die "UV_VERSION must be a pinned x.y.z version" 2

# ------------------------------------------------------------------ remote functions
# Prints one line per directory: ok | created | fixed | would-create | would-fix
_remote_layout() {
  local apply="$1" user="$2" base="$3"
  # ADR-015 § Layout "Permissions" (TL decision 2026-09-27): shared 0751 lets nginx (www-data) traverse
  # to static/ and media/ without listing shared/; db, backups, cache stay private.
  local -a specs=(
    "$base:0755" "$base/releases:0755" "$base/shared:0751"
    "$base/shared/static:0755" "$base/shared/media:0755"
    "$base/shared/db:0700" "$base/shared/backups:0700" "$base/shared/cache:0700"
    "$base/shared/logs:0750" "$base/sandbox:0750" "$base/qa:0750"
  )
  local spec dir mode cur
  for spec in "${specs[@]}"; do
    dir="${spec%:*}"; mode="${spec##*:}"
    if [[ -d "$dir" ]]; then
      cur="$(stat -c '%U:%G:%a' "$dir")"
      if [[ "$cur" == "$user:$user:${mode#0}" ]]; then echo "ok       $dir ($cur)"; continue; fi
      if [[ "$apply" == 1 ]]; then sudo -n install -d -o "$user" -g "$user" -m "$mode" "$dir"; echo "fixed    $dir ($cur -> $user:$user:${mode#0})"
      else echo "would-fix $dir ($cur -> $user:$user:${mode#0})"; fi
    else
      if [[ "$apply" == 1 ]]; then sudo -n install -d -o "$user" -g "$user" -m "$mode" "$dir"; echo "created  $dir ($user:$user:${mode#0})"
      else echo "would-create $dir"; fi
    fi
  done
}

# Read-only verification of the modes + what nginx (www-data) can and cannot reach. Non-zero on mismatch.
_remote_verify_perms() {
  local base="$1" user="$2" bad=0 spec dir mode cur
  for spec in "$base:755" "$base/releases:755" "$base/shared:751" "$base/shared/static:755" "$base/shared/media:755" \
              "$base/shared/db:700" "$base/shared/backups:700" "$base/shared/cache:700" "$base/shared/logs:750" \
              "$base/sandbox:750" "$base/qa:750"; do
    dir="${spec%:*}"; mode="${spec##*:}"; cur="$(stat -c '%U:%G:%a' "$dir" 2>/dev/null || echo missing)"
    if [[ "$cur" == "$user:$user:$mode" ]]; then echo "ok    $cur $dir"; else echo "BAD   $cur $dir (want $user:$user:$mode)"; bad=1; fi
  done
  if [[ -e "$base/shared/.env" ]]; then
    cur="$(stat -c '%U:%G:%a' "$base/shared/.env")"
    if [[ "$cur" == "$user:$user:600" ]]; then echo "ok    $cur $base/shared/.env"; else echo "BAD   $cur $base/shared/.env (want 600)"; bad=1; fi
  fi
  _www() { # <expect ok|denied> <description> <cmd...>
    local want="$1" what="$2"; shift 2
    if sudo -n -u www-data "$@" >/dev/null 2>&1; then got=ok; else got=denied; fi
    if [[ "$got" == "$want" ]]; then echo "ok    www-data $what: $got"; else echo "BAD   www-data $what: $got (want $want)"; bad=1; fi
  }
  local got
  _www ok     "test -r shared/static/." test -r "$base/shared/static/."
  _www ok     "test -r shared/media/."  test -r "$base/shared/media/."
  _www denied "ls shared"               ls "$base/shared"
  _www denied "test -r shared/db/."     test -r "$base/shared/db/."
  _www denied "test -r shared/backups/." test -r "$base/shared/backups/."
  _www denied "cat shared/.env"         cat "$base/shared/.env"
  return "$bad"
}

# Installs uv ${ver} into ~/.local/bin only when missing or a different version.
_remote_uv() {
  local apply="$1" ver="$2" uv="$HOME/.local/bin/uv" cur=""
  [[ -x "$uv" ]] && cur="$("$uv" --version 2>/dev/null | awk '{print $2}')"
  if [[ "$cur" == "$ver" ]]; then echo "ok       uv $cur at $uv"; return 0; fi
  if [[ "$apply" != 1 ]]; then echo "would-install uv $ver (current: ${cur:-none})"; return 0; fi
  echo "installing uv $ver (current: ${cur:-none})"
  curl -LsSf "https://astral.sh/uv/$ver/install.sh" \
    | env UV_INSTALL_DIR="$HOME/.local/bin" INSTALLER_NO_MODIFY_PATH=1 sh >/dev/null
  cur="$("$uv" --version | awk '{print $2}')"
  [[ "$cur" == "$ver" ]] || { echo "uv version after install is '$cur', expected '$ver'" >&2; return 1; }
  echo "installed uv $cur at $uv"
}

# uv python install is idempotent; only runs when no managed interpreter matches.
_remote_python() {
  local apply="$1" pyver="$2" uv="$HOME/.local/bin/uv" py=""
  if [[ ! -x "$uv" ]]; then echo "would-install python $pyver (uv not installed yet)"; return 0; fi
  py="$(UV_PYTHON_PREFERENCE=only-managed "$uv" python find "$pyver" 2>/dev/null || true)"
  if [[ -n "$py" ]]; then echo "ok       python $("$py" --version 2>&1 | awk '{print $2}') at $py"; return 0; fi
  if [[ "$apply" != 1 ]]; then echo "would-install python $pyver via uv"; return 0; fi
  UV_PYTHON_PREFERENCE=only-managed "$uv" python install --no-bin "$pyver"
  py="$(UV_PYTHON_PREFERENCE=only-managed "$uv" python find "$pyver")"
  echo "installed python $("$py" --version 2>&1 | awk '{print $2}') at $py"
}

_remote_versions() {
  local pyver="$1" uv="$HOME/.local/bin/uv" py
  echo "uv:      $("$uv" --version 2>/dev/null || echo 'not installed')"
  py="$(UV_PYTHON_PREFERENCE=only-managed "$uv" python find "$pyver" 2>/dev/null || true)"
  echo "python:  ${py:-not installed} $([[ -n "$py" ]] && "$py" --version 2>&1)"
  echo "disk:    $(df -h --output=avail,pcent "$(dirname "$DEPLOY_PATH")" | tail -1 | xargs) free/used on $(dirname "$DEPLOY_PATH")"
  echo "layout:  $(find "$DEPLOY_PATH" -maxdepth 2 -type d 2>/dev/null | sort | tr '\n' ' ')"
}

# ------------------------------------------------------------------ main
# Plans run read-only (apply=0) under --dry-run; the applying calls (apply=1) go through `remote_fn rw`,
# so --dry-run is enforced by the transport.
bootstrap_call() { # <function> [args...]
  if is_dry_run; then remote_fn ro "$1" 0 "${@:2}"; else remote_fn rw "$1" 1 "${@:2}"; fi
}
info "setup-server mode=$DEPLOYMENT_MODE host=$SERVER_HOST user=$SERVER_USER path=$DEPLOY_PATH bootstrap_only=$bootstrap_only with_e2e=$with_e2e dry_run=$DRY_RUN"
check_ssh
ops_lock

step "1/8 dental guard: preflight + before snapshot"
ops_guard_begin

step "2/8 directory layout + permission modes under $DEPLOY_PATH"
REMOTE_FUNCS=(); REMOTE_VARS=()
bootstrap_call _remote_layout "$SERVER_USER" "$DEPLOY_PATH"

step "3/8 uv $UV_VERSION for $SERVER_USER"
bootstrap_call _remote_uv "$UV_VERSION"

step "4/8 python $PYTHON_VERSION via uv"
bootstrap_call _remote_python "$PYTHON_VERSION"

if [[ $bootstrap_only == 0 ]]; then
  ops_render
  variant="$(ops_remote ro _fs_cert_state)"
  unit_dst="/etc/systemd/system/$BACKEND_SYSTEMD_SERVICE.service"
  mapfile -t env_keys < <(grep -oE '^[A-Z_][A-Z0-9_]*=' "$OPS_RENDER_DIR/env/shared.env" | tr -d '=')

  step "5/8 plan: shared/.env, systemd unit, nginx ($variant variant)"
  ops_remote ro _fs_shared_env_plan "$DEPLOY_PATH/shared/.env" "${env_keys[@]}"
  ops_remote ro _fs_plan_file "systemd unit" "$unit_dst" "$(sha_of "$OPS_RENDER_DIR/systemd/$BACKEND_SYSTEMD_SERVICE.service")"
  for d in "$API_DOMAIN" "$WEB_DOMAIN"; do
    ops_remote ro _fs_plan_file "nginx site ($variant)" "/etc/nginx/sites-available/$d" "$(sha_of "$OPS_RENDER_DIR/nginx/$variant/$d")"
  done

  step "6/8 apply: shared/.env → unit → nginx safe-apply"
  ops_stage_upload "$OPS_RENDER_DIR"
  ops_remote rw _fs_shared_env_install "$OPS_STAGE/env/shared.env" "$DEPLOY_PATH/shared/.env" \
    || { ops_stage_cleanup; die "shared/.env step failed" 1; }
  ops_remote rw _fs_unit_install "$OPS_STAGE/systemd/$BACKEND_SYSTEMD_SERVICE.service" \
    || { ops_stage_cleanup; die "systemd unit step failed" 1; }
  ops_remote rw _fs_nginx_safe_apply "$OPS_STAGE/nginx/$variant" 0 \
    || { ops_stage_cleanup; die "nginx safe-apply failed (previous Flash files restored, nginx NOT reloaded)" 1; }
  ops_stage_cleanup

  if [[ $with_e2e == 1 ]]; then
    step "7/8 Playwright Chromium for QA E2E (apt deps via sudo)"
    ops_remote rw _fs_e2e_install
  else
    step "7/8 Playwright: skipped (use --with-e2e)"
  fi
else
  step "5-7/8 skipped (--bootstrap-only): shared/.env, systemd unit, nginx, Playwright"
fi

step "8/8 verify permissions + versions"
REMOTE_FUNCS=(); REMOTE_VARS=()
if is_dry_run; then
  remote_fn ro _remote_verify_perms "$DEPLOY_PATH" "$SERVER_USER" || warn "permissions differ from ADR-015 (a real run fixes them)"
else
  remote_fn ro _remote_verify_perms "$DEPLOY_PATH" "$SERVER_USER" || die "permission verification FAILED" 1
fi
REMOTE_VARS=(DEPLOY_PATH); remote_fn ro _remote_versions "$PYTHON_VERSION"

step "dental guard: after snapshot + compare"
ops_guard_end
info "setup-server finished$(is_dry_run && echo ' (dry-run: nothing was changed)')"
