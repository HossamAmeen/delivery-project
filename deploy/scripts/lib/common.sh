# shellcheck shell=bash
# Flash deployment library: env loading, validation, logging, redaction, --dry-run, SSH.
# Sourced by every script in deploy/scripts/. Never `set -x` anywhere in this tree.
#
# Exit codes used across the scripts:
#   0 ok · 1 runtime failure · 2 configuration error (env, mode, arguments) · 3 dental guard violation
#   remote-test.sh exits with the test run's own exit code.

set -euo pipefail

if [[ -n "${FLASH_COMMON_LOADED:-}" ]]; then return 0; fi
FLASH_COMMON_LOADED=1

FLASH_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FLASH_SCRIPTS_DIR="$(dirname "$FLASH_LIB_DIR")"
REPO_ROOT="$(cd "$FLASH_SCRIPTS_DIR/../.." && pwd)"
export REPO_ROOT
DRY_RUN="${DRY_RUN:-0}"
case "$DRY_RUN" in 1|true|yes) DRY_RUN=1 ;; *) DRY_RUN=0 ;; esac

# ---------------------------------------------------------------- logging (UTC, stderr)
_ts() { date -u +%Y-%m-%dT%H:%M:%SZ; }
log()  { printf '%s [%s] %s\n' "$(_ts)" "${FLASH_SCRIPT:-flash}" "$(redact "$*")" >&2; }
info() { log "INFO  $*"; }
warn() { log "WARN  $*"; }
err()  { log "ERROR $*"; }
die()  { local code="${2:-1}"; err "$1"; exit "$code"; }
step() { log "----- $*"; }

# ---------------------------------------------------------------- redaction
# Values of variables whose NAME matches *PASSWORD*|*SECRET*|*TOKEN*|*KEY* are masked.
# SSH_KEY_PATH is a path, not a secret, and may be shown.
_is_secret_name() {
  case "$1" in
    SSH_KEY_PATH) return 1 ;;
    *PASSWORD*|*SECRET*|*TOKEN*|*KEY*) return 0 ;;
    *) return 1 ;;
  esac
}
redact() {
  local s="$*" name val
  while IFS= read -r name; do
    _is_secret_name "$name" || continue
    val="${!name-}"
    [[ ${#val} -ge 3 ]] || continue
    s="${s//"$val"/***}"
  done < <(compgen -v)
  printf '%s' "$s"
}

# ---------------------------------------------------------------- argument helpers
# parse_common_flag <arg> → returns 0 if it consumed a generic flag.
parse_common_flag() {
  case "$1" in
    --dry-run) DRY_RUN=1; return 0 ;;
    *) return 1 ;;
  esac
}
is_dry_run() { [[ "$DRY_RUN" == 1 ]]; }

# ---------------------------------------------------------------- env loading
# load_env: reads ENV_FILE (default: <repo>/.env). KEY=VALUE lines only; comments/blank ignored;
# surrounding single/double quotes stripped; never `source`d or eval'd. Variables already set in the
# process environment win (so `DEPLOYMENT_MODE=docker make …` can be used for checks).
load_env() {
  ENV_FILE="${ENV_FILE:-$REPO_ROOT/.env}"
  [[ -f "$ENV_FILE" ]] || die "env file not found: $ENV_FILE (copy .env.example to .env and fill it)" 2
  local line key val n=0
  while IFS= read -r line || [[ -n "$line" ]]; do
    n=$((n + 1))
    line="${line%$'\r'}"
    [[ "$line" =~ ^[[:space:]]*(#|$) ]] && continue
    line="${line#export }"
    [[ "$line" == *=* ]] || die "$ENV_FILE:$n: not a KEY=VALUE line" 2
    key="${line%%=*}"; val="${line#*=}"
    key="${key//[[:space:]]/}"
    [[ "$key" =~ ^[A-Z_][A-Z0-9_]*$ ]] || die "$ENV_FILE:$n: invalid variable name '$key'" 2
    if [[ "$val" =~ ^\"(.*)\"$ ]] || [[ "$val" =~ ^\'(.*)\'$ ]]; then val="${BASH_REMATCH[1]}"; fi
    if [[ -z "${!key+x}" ]]; then
      printf -v "$key" '%s' "$val"
      export "${key?}"
    fi
  done < "$ENV_FILE"
  # tilde expansion for the key path (path only; never printed with contents)
  if [[ -n "${SSH_KEY_PATH:-}" && "$SSH_KEY_PATH" == \~/* ]]; then SSH_KEY_PATH="$HOME/${SSH_KEY_PATH#\~/}"; fi
  export SSH_KEY_PATH
  : "${SERVER_PORT:=22}"
  export SERVER_PORT
}

# require_vars VAR... → exit 2 listing every missing/empty variable.
require_vars() {
  local v missing=()
  for v in "$@"; do [[ -n "${!v:-}" ]] || missing+=("$v"); done
  ((${#missing[@]} == 0)) || die "missing required variable(s) in ${ENV_FILE:-.env}: ${missing[*]}" 2
}

# validate_mode: systemd is the only implemented mode (ADR-015).
validate_mode() {
  case "${DEPLOYMENT_MODE:-}" in
    systemd) return 0 ;;
    docker) die "DEPLOYMENT_MODE=docker: docker mode is deferred (ADR-015)" 2 ;;
    "") die "DEPLOYMENT_MODE is not set (expected: systemd)" 2 ;;
    *) die "DEPLOYMENT_MODE='${DEPLOYMENT_MODE}' is invalid (expected: systemd; docker is deferred, ADR-015)" 2 ;;
  esac
}

# validate_common: the variables every server-touching script needs.
FLASH_CORE_VARS=(APP_NAME DEPLOYMENT_MODE SERVER_HOST SERVER_USER SERVER_PORT SSH_KEY_PATH DEPLOY_PATH PYTHON_VERSION)
validate_common() {
  validate_mode
  require_vars "${FLASH_CORE_VARS[@]}" "$@"
  [[ "$SERVER_PORT" =~ ^[0-9]+$ ]] || die "SERVER_PORT must be numeric" 2
  [[ -r "$SSH_KEY_PATH" ]] || die "SSH key not readable at SSH_KEY_PATH=$SSH_KEY_PATH" 2
  [[ "$DEPLOY_PATH" == /* && "$DEPLOY_PATH" != "/" && "$DEPLOY_PATH" != *..* ]] \
    || die "DEPLOY_PATH must be an absolute path other than / (got '$DEPLOY_PATH')" 2
  DEPLOY_PATH="${DEPLOY_PATH%/}"
  UV_BIN="${UV_BIN:-/home/${SERVER_USER}/.local/bin/uv}"
  export DEPLOY_PATH UV_BIN
}

# ---------------------------------------------------------------- command execution
_quote_cmd() { local out="" a; for a in "$@"; do out+="$(printf '%q' "$a") "; done; printf '%s' "${out% }"; }

# run CMD... → local command; printed (redacted); skipped under --dry-run.
run() {
  if is_dry_run; then log "[dry-run] $(_quote_cmd "$@")"; return 0; fi
  log "+ $(_quote_cmd "$@")"
  "$@"
}

ssh_opts() {
  SSH_OPTS=(-i "$SSH_KEY_PATH" -p "$SERVER_PORT" -o BatchMode=yes -o ConnectTimeout=15
            -o ServerAliveInterval=30 -o ServerAliveCountMax=6 -o LogLevel=ERROR
            -o ControlMaster=auto -o "ControlPath=${TMPDIR:-/tmp}/flash-ssh-%C" -o ControlPersist=60)
}
# shellcheck disable=SC2153  # SERVER_HOST/SERVER_USER come from .env (load_env)
ssh_target() { printf '%s@%s' "$SERVER_USER" "$SERVER_HOST"; }

# _remote_exec <mode ro|rw> <cmd-string>: raw SSH execution of a remote shell command string.
_remote_exec() {
  local mode="$1"; shift
  if is_dry_run && [[ "$mode" == rw ]]; then
    log "[dry-run] remote($(ssh_target)): $*"; return 0
  fi
  ssh_opts
  # shellcheck disable=SC2029  # the command string is meant to be expanded client-side
  ssh "${SSH_OPTS[@]}" "$(ssh_target)" "$@"
}

# remote CMD-STRING → state-changing remote command (skipped under --dry-run).
remote()    { log "remote: $*"; _remote_exec rw "$*"; }
# remote_ro CMD-STRING → read-only remote command (runs under --dry-run too).
remote_ro() { _remote_exec ro "$*"; }

# remote_fn <ro|rw> <function> [args...]
# Ships bash functions + selected variables to the server and calls <function> "$@" there.
# Declare what to ship in REMOTE_FUNCS (function names) and REMOTE_VARS (variable names; secret-named
# variables are refused). stdin is passed through (used for tar streams). The payload goes base64 in
# argv, so it must never contain secrets — secrets are read on the server only.
REMOTE_FUNCS=()
REMOTE_VARS=()
remote_fn() {
  local mode="$1" fn="$2"; shift 2
  local payload v f args=""
  payload='set -euo pipefail'$'\n'
  for v in "${REMOTE_VARS[@]}"; do
    _is_secret_name "$v" && die "refusing to ship secret-named variable $v to the server" 1
    payload+="$(printf '%s=%q' "$v" "${!v-}")"$'\n'
  done
  for f in "${REMOTE_FUNCS[@]}" "$fn"; do payload+="$(declare -f "$f")"$'\n'; done
  payload+="$fn \"\$@\""$'\n'
  for v in "$@"; do args+=" $(printf '%q' "$v")"; done
  if is_dry_run && [[ "$mode" == rw ]]; then
    log "[dry-run] remote($(ssh_target)): $fn$(redact "$args")"; return 0
  fi
  local b64; b64="$(printf '%s' "$payload" | base64 -w0)"
  ssh_opts
  # shellcheck disable=SC2029  # b64 payload and %q-quoted args are expanded client-side on purpose
  ssh "${SSH_OPTS[@]}" "$(ssh_target)" "bash -c \"\$(printf %s $b64 | base64 -d)\" flash-$fn$args"
}

# check_ssh: fails fast (exit 1) when the server is unreachable.
check_ssh() {
  remote_ro true || die "cannot reach $(ssh_target):$SERVER_PORT with the key at SSH_KEY_PATH" 1
}

# new_run_id → UTC timestamp id, e.g. 20260927-153012-4821
new_run_id() { printf '%s-%s' "$(date -u +%Y%m%d-%H%M%S)" "$$"; }
