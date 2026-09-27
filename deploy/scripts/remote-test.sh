#!/usr/bin/env bash
# Flash on-server test runners (ADR-018). Tests never run on the local machine (REQ-009).
#
# Usage:
#   remote-test.sh [--dry-run] backend [--ref <git-ref> | --worktree] [--steps <list>] [-- <pytest args>]
#   remote-test.sh [--dry-run] qa [<pytest args>]
#   remote-test.sh [--dry-run] throttle-reset
#
# backend  Ships backend/ (git archive of --ref, default HEAD; or the working tree with --worktree)
#          to ${DEPLOY_PATH}/sandbox/backend and runs, with an explicit test env (shared/.env is never
#          read): ruff check, ruff format --check, manage.py check, makemigrations --check --dry-run,
#          pytest --cov --cov-fail-under=80. --steps: comma list of ruff-check,ruff-format,check,
#          makemigrations,pytest (or lint = both ruff steps; default all).
#          Results → backend/.remote-results/<run-id>/ (+ latest). Exit code: pytest's if it failed,
#          else the first failing step's, else 0.
# qa       Ships qa/ to ${DEPLOY_PATH}/qa/suite and runs pytest <args> on the server against
#          https://${API_DOMAIN} / https://${WEB_DOMAIN}. QA_HEALTH_TOKEN (from shared/.env) and the QA
#          user credentials (qa/credentials.env) are exported only into the pytest process and
#          redacted from output. Results → qa/.results/<run-id>/ (+ latest). Exit code = pytest's.
# throttle-reset  Empties ${DEPLOY_PATH}/shared/cache/ (throttle counters) and prints the count.
#
# Overrides (env): BACKEND_SRC_DIR, BACKEND_RESULTS_DIR, QA_SRC_DIR, QA_RESULTS_LOCAL_DIR,
#   REMOTE_TEST_TIMEOUT (s per step, default 2700), REMOTE_TEST_LOCK_WAIT (s, default 1800).
# One pytest process at a time per suite (server lock); `-n`/xdist is refused.
set -euo pipefail
FLASH_SCRIPT=remote-test
# shellcheck source=lib/common.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib/common.sh"

usage() { sed -n '2,24p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; }

REMOTE_TEST_TIMEOUT="${REMOTE_TEST_TIMEOUT:-2700}"
REMOTE_TEST_LOCK_WAIT="${REMOTE_TEST_LOCK_WAIT:-1800}"
RESULTS_TO_KEEP="${RESULTS_TO_KEEP:-10}"
TAR_EXCLUDES=(--exclude=.env --exclude='*.sqlite3' --exclude='*.sqlite3-*' --exclude=.venv --exclude=venv
              --exclude=__pycache__ --exclude=.pytest_cache --exclude=.ruff_cache --exclude=.mypy_cache
              --exclude=.remote-results --exclude=.results --exclude=test-results --exclude=htmlcov
              --exclude=.coverage --exclude='.coverage.*' --exclude=node_modules --exclude=credentials.env)

# =============================================================== remote functions (run on the server)
_rt_lock() { # <lockfile>
  exec 9>"$1"
  if ! flock -n 9; then
    echo "[remote] another run holds $1 — waiting up to ${REMOTE_TEST_LOCK_WAIT}s"
    flock -w "$REMOTE_TEST_LOCK_WAIT" 9 || { echo "[remote] lock timeout" >&2; exit 75; }
  fi
}

_rt_receive() { # <dest dir>  (tar.gz on stdin → atomic replace)
  rm -rf "$1.incoming"; mkdir -p "$1.incoming"
  tar -xzf - -C "$1.incoming"
  rm -rf "$1"; mv "$1.incoming" "$1"
}

_rt_prune_results() { # <results parent>
  local keep="$RESULTS_TO_KEEP"
  find "$1" -mindepth 1 -maxdepth 1 -type d -printf '%T@ %p\n' 2>/dev/null | sort -rn \
    | tail -n +"$((keep + 1))" | cut -d' ' -f2- | xargs -r rm -rf
}

_rt_venv() { # <venv> <requirements file (relative to cwd)> → (re)builds only when the hash changes
  local venv="$1" req="$2" hash
  hash="$( { printf '%s|%s|' "$PYTHON_VERSION" "$("$UV_BIN" --version)"; \
             find "$(dirname "$req")" -maxdepth 1 -type f -name '*.txt' -print0 | sort -z | xargs -0 cat; } \
           | sha256sum | cut -d' ' -f1)"
  if [[ -x "$venv/bin/python" && "$(cat "$venv/.flash-reqhash" 2>/dev/null)" == "$hash" ]]; then
    echo "[remote] venv $venv up to date (requirements hash ${hash:0:12})"; return 0
  fi
  echo "[remote] venv $venv: (re)building on Python $PYTHON_VERSION (requirements hash ${hash:0:12})"
  rm -rf "$venv"
  UV_PYTHON_PREFERENCE=only-managed UV_PYTHON_DOWNLOADS=never "$UV_BIN" venv --quiet --python "$PYTHON_VERSION" "$venv"
  "$UV_BIN" pip install --quiet --python "$venv/bin/python" -r "$req"
  printf '%s\n' "$hash" > "$venv/.flash-reqhash"
}

_rt_clean_env() { # keep only a minimal, explicit environment (subshell use only)
  local v
  while IFS= read -r v; do
    case "$v" in HOME|USER|LOGNAME|SHELL|TERM) ;; *) unset "$v" ;; esac
  done < <(compgen -e)
  export PATH="$1/bin:/usr/local/bin:/usr/bin:/bin" LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONUNBUFFERED=1
}

_rt_kill_leftovers() { # <venv>
  local n
  n="$(pgrep -u "$(id -u)" -f -- "$1/bin/" | wc -l || true)"
  if [[ "$n" -gt 0 ]]; then
    echo "[remote] killing $n leftover process(es) from $1"
    pkill -TERM -u "$(id -u)" -f -- "$1/bin/" || true; sleep 2
    pkill -KILL -u "$(id -u)" -f -- "$1/bin/" || true
  fi
}

_rt_redact_prog() { # perl program: masks every FLASH_REDACT value and truncated prefixes ("abcdef...")
  cat <<'PERL'
BEGIN {
  $| = 1;
  my @s = sort { length($b) <=> length($a) } grep { length($_) >= 4 } split /\n/, ($ENV{FLASH_REDACT} // "");
  my @alt = map { quotemeta($_) } @s;
  for my $v (@s) { for my $l (reverse 6 .. length($v) - 1) { push @alt, quotemeta(substr($v, 0, $l)) . '(?=\.\.\.|\xE2\x80\xA6)'; } }
  our $re = @alt ? join('|', @alt) : undef;
}
our $re; s/(?:$re)/***/g if defined $re;
PERL
}

_rt_redact_filter() { # stdin→stdout; secrets come from FLASH_REDACT (newline separated) in perl's env
  perl -pe "$(_rt_redact_prog)"
}

_rt_backend() { # <run_id> <label> <steps> [pytest args...]
  local run_id="$1" label="$2" steps="$3"; shift 3
  local base="$DEPLOY_PATH/sandbox" src venv res
  src="$base/backend"; venv="$base/venv"; res="$base/results/$run_id"
  [[ -d "$base" ]] || { echo "[remote] $base missing — run 'make setup-server' first" >&2; cat >/dev/null; exit 2; }
  _rt_lock "$base/.lock"
  _rt_receive "$src"
  mkdir -p "$res"; _rt_prune_results "$base/results"
  cd "$src"
  [[ -f requirements/development.txt ]] || { echo "[remote] backend/requirements/development.txt missing" >&2; exit 2; }
  _rt_venv "$venv" requirements/development.txt
  local xdist=()
  "$venv/bin/python" -c 'import xdist' 2>/dev/null && xdist=(-n 0)
  rm -f "$base"/test.sqlite3*
  set +e
  (
    _rt_clean_env "$venv"
    export DJANGO_SETTINGS_MODULE=config.settings.development
    export DATABASE_URL="sqlite:///$base/test.sqlite3"
    export RATELIMIT_CACHE_URL=locmem://
    export CELERY_ENABLED=False CELERY_BEAT_ENABLED=False
    SECRET_KEY="$("$venv/bin/python" -c 'import secrets; print("test-" + secrets.token_urlsafe(48))')"
    HEALTH_CHECK_PASSWORD="$("$venv/bin/python" -c 'import secrets; print(secrets.token_urlsafe(24))')"
    export SECRET_KEY HEALTH_CHECK_PASSWORD
    export COVERAGE_FILE="$res/.coverage"
    echo "== Flash backend test run $run_id | $label | $("$venv/bin/python" --version) | $(date -u +%FT%TZ)"
    echo "== env: DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE DATABASE_URL=$DATABASE_URL RATELIMIT_CACHE_URL=$RATELIMIT_CACHE_URL (shared/.env not read)"
    local first_rc=0 pytest_rc=0 rc name
    declare -A want=()
    local s
    IFS=',' read -r -a _st <<< "$steps"
    for s in "${_st[@]}"; do
      case "$s" in
        all) for n in ruff-check ruff-format check makemigrations pytest; do want[$n]=1; done ;;
        lint) want[ruff-check]=1; want[ruff-format]=1 ;;
        ruff-check|ruff-format|check|makemigrations|pytest) want[$s]=1 ;;
        *) echo "unknown step '$s'" >&2; exit 2 ;;
      esac
    done
    : > "$res/summary.txt"
    for name in ruff-check ruff-format check makemigrations pytest; do
      [[ -n "${want[$name]:-}" ]] || continue
      echo; echo "== step: $name"
      case "$name" in
        ruff-check)     timeout -k 30 "$REMOTE_TEST_TIMEOUT" "$venv/bin/python" -m ruff check . ;;
        ruff-format)    timeout -k 30 "$REMOTE_TEST_TIMEOUT" "$venv/bin/python" -m ruff format --check . ;;
        check)          timeout -k 30 "$REMOTE_TEST_TIMEOUT" "$venv/bin/python" manage.py check ;;
        makemigrations) timeout -k 30 "$REMOTE_TEST_TIMEOUT" "$venv/bin/python" manage.py makemigrations --check --dry-run ;;
        pytest)         timeout -k 30 "$REMOTE_TEST_TIMEOUT" "$venv/bin/python" -m pytest -p no:cacheprovider "${xdist[@]}" \
                          --cov --cov-report=term-missing --cov-report="xml:$res/coverage.xml" --cov-fail-under=80 \
                          --junitxml="$res/junit.xml" "$@" ;;
      esac
      rc=$?
      printf '%-15s %s\n' "$name" "$([[ $rc == 0 ]] && echo PASS || echo "FAIL (exit $rc)")" | tee -a "$res/summary.txt"
      [[ $name == pytest ]] && pytest_rc=$rc
      [[ $rc != 0 && $first_rc == 0 ]] && first_rc=$rc
    done
    rc=$first_rc; [[ $pytest_rc != 0 ]] && rc=$pytest_rc
    echo; echo "== summary ($run_id)"; cat "$res/summary.txt"; echo "== exit code: $rc"
    printf 'exit %s\n' "$rc" >> "$res/summary.txt"
    exit "$rc"
  ) 2>&1 | tee "$res/output.log"
  local rc="${PIPESTATUS[0]}"
  set -e
  rm -f "$base"/test.sqlite3*
  _rt_kill_leftovers "$venv"
  exit "$rc"
}

_rt_qa() { # <run_id> [pytest args...]
  local run_id="$1"; shift
  local base="$DEPLOY_PATH/qa" suite venv res envf credf
  suite="$base/suite"; venv="$base/venv"; res="$base/results/$run_id"
  envf="$DEPLOY_PATH/shared/.env"; credf="$base/credentials.env"
  [[ -d "$base" ]] || { echo "[remote] $base missing — run 'make setup-server' first" >&2; cat >/dev/null; exit 2; }
  _rt_lock "$base/.lock"
  _rt_receive "$suite"
  mkdir -p "$res"; _rt_prune_results "$base/results"
  cd "$suite"
  [[ -f requirements.txt ]] || { echo "[remote] qa/requirements.txt missing" >&2; exit 2; }
  _rt_venv "$venv" requirements.txt

  # Secrets: read on the server, never printed, never in argv.
  local token="" line k v redact=""
  local -a cred_names=() cred_values=()
  if [[ -r "$envf" ]]; then
    while IFS= read -r line || [[ -n "$line" ]]; do
      [[ "$line" == HEALTH_CHECK_PASSWORD=* ]] || continue
      token="${line#*=}"; token="${token%\"}"; token="${token#\"}"; token="${token%\'}"; token="${token#\'}"
    done < "$envf"
  fi
  if [[ -r "$credf" ]]; then
    while IFS= read -r line || [[ -n "$line" ]]; do
      [[ "$line" =~ ^(QA_[A-Z0-9_]+)=(.*)$ ]] || continue
      k="${BASH_REMATCH[1]}"; v="${BASH_REMATCH[2]}"; v="${v%\"}"; v="${v#\"}"; v="${v%\'}"; v="${v#\'}"
      cred_names+=("$k"); cred_values+=("$v")
      [[ "$k" == *PASSWORD* ]] && redact+="$v"$'\n'
    done < "$credf"
  fi
  [[ -n "$token" ]] && redact+="$token"$'\n'
  echo "== Flash QA run $run_id | base=https://$API_DOMAIN web=https://$WEB_DOMAIN | $("$venv/bin/python" --version) | $(date -u +%FT%TZ)"
  echo "== QA_HEALTH_TOKEN: $([[ -n "$token" ]] && echo 'set (from shared/.env)' || echo 'NOT set (shared/.env absent or no HEALTH_CHECK_PASSWORD)')"
  echo "== QA credentials: ${#cred_names[@]} variable(s) from $credf$([[ -r "$credf" ]] || echo ' (absent — run make seed-qa-users)')"
  local -a junit=()
  [[ " $* " == *" --junitxml"* ]] || junit=(--junitxml="$res/junit.xml")
  set +e
  (
    _rt_clean_env "$venv"
    export QA_BASE_URL="https://$API_DOMAIN" QA_WEB_URL="https://$WEB_DOMAIN" QA_RESULTS_DIR="$res"
    export QA_DENTAL_DOMAINS="$DENTAL_GUARD_DOMAINS" PLAYWRIGHT_BROWSERS_PATH="$base/browsers"
    [[ -n "$token" ]] && export QA_HEALTH_TOKEN="$token"
    local i
    for i in "${!cred_names[@]}"; do export "${cred_names[$i]}=${cred_values[$i]}"; done
    exec timeout -k 30 "$REMOTE_TEST_TIMEOUT" "$venv/bin/python" -m pytest -p no:cacheprovider "${junit[@]}" "$@"
  ) 2>&1 | FLASH_REDACT="$redact" _rt_redact_filter | tee "$res/output.log"
  local rc="${PIPESTATUS[0]}"
  set -e
  # collect artifacts QA may have written inside the suite, then scrub every text artifact
  [[ -d "$suite/.results" ]] && cp -a "$suite/.results/." "$res/" 2>/dev/null || true
  [[ -d "$suite/test-results" ]] && cp -a "$suite/test-results" "$res/playwright" 2>/dev/null || true
  local prog; prog="$(_rt_redact_prog)"
  find "$res" -type f \( -name '*.xml' -o -name '*.log' -o -name '*.txt' -o -name '*.json' -o -name '*.html' \) -print0 \
    | FLASH_REDACT="$redact" xargs -0 -r perl -pi -e "$prog"
  printf 'pytest exit %s\n' "$rc" > "$res/summary.txt"
  echo "== exit code: $rc"
  _rt_kill_leftovers "$venv"
  exit "$rc"
}

_rt_throttle_reset() { # <apply 0|1>
  local dir="$DEPLOY_PATH/shared/cache" n
  [[ -n "$DEPLOY_PATH" && "$DEPLOY_PATH" != / && "$dir" == */shared/cache ]] || { echo "bad cache path" >&2; exit 2; }
  [[ -d "$dir" ]] || { echo "throttle-reset: $dir does not exist (run make setup-server)" >&2; exit 1; }
  n="$(find "$dir" -mindepth 1 -type f | wc -l)"
  if [[ "$1" == 1 ]]; then
    find "$dir" -mindepth 1 -delete
    echo "throttle-reset: removed $n file(s) from $dir"
  else
    echo "throttle-reset (dry-run): would remove $n file(s) from $dir"
  fi
}

# =============================================================== local side
refuse_xdist() {
  local a
  for a in "$@"; do
    case "$a" in -n|-n[0-9]*|--numprocesses|--numprocesses=*|--dist|--dist=*)
      die "parallel pytest ($a) is not allowed on the shared server (one worker only)" 2 ;;
    esac
  done
}

fetch_results() { # <remote dir> <local parent> <run_id>
  local rdir="$1" lparent="$2" id="$3"
  mkdir -p "$lparent/$id"
  ssh_opts
  if rsync -a -e "ssh $(_quote_cmd "${SSH_OPTS[@]}")" "$(ssh_target):$rdir/" "$lparent/$id/"; then
    ln -sfn "$id" "$lparent/latest"
    find "$lparent" -mindepth 1 -maxdepth 1 -type d -printf '%T@ %p\n' | sort -rn \
      | tail -n +"$((RESULTS_TO_KEEP + 1))" | cut -d' ' -f2- | xargs -r rm -rf
    info "results copied to $lparent/$id (also $lparent/latest)"
  else
    warn "could not copy results back from $rdir"
  fi
}

REMOTE_FUNCS_ALL=(_rt_lock _rt_receive _rt_prune_results _rt_venv _rt_clean_env _rt_kill_leftovers _rt_redact_prog _rt_redact_filter)

cmd_backend() {
  local ref="" worktree=0 steps="all"
  local -a pytest_args=()
  while (($#)); do
    case "$1" in
      --ref) [[ $# -ge 2 ]] || die "--ref needs a value" 2; ref="$2"; shift 2 ;;
      --ref=*) ref="${1#--ref=}"; shift ;;
      --worktree) worktree=1; shift ;;
      --steps) [[ $# -ge 2 ]] || die "--steps needs a value" 2; steps="$2"; shift 2 ;;
      --dry-run) DRY_RUN=1; shift ;;
      --) shift; pytest_args=("$@"); break ;;
      *) pytest_args+=("$1"); shift ;;
    esac
  done
  [[ -n "$ref" && "$worktree" == 1 ]] && die "use either --ref or --worktree, not both" 2
  refuse_xdist "${pytest_args[@]}"
  local src label tmp=""
  if [[ "$worktree" == 1 ]]; then
    src="${BACKEND_SRC_DIR:-$REPO_ROOT/backend}"
    label="worktree $src (HEAD $(git -C "$REPO_ROOT" rev-parse --short HEAD 2>/dev/null || echo none), uncommitted changes included)"
  else
    ref="${ref:-HEAD}"
    local sha
    sha="$(git -C "$REPO_ROOT" rev-parse --verify --quiet "$ref^{commit}")" || die "git ref '$ref' not found" 2
    tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
    git -C "$REPO_ROOT" archive --format=tar "$sha" backend 2>/dev/null | tar -x -C "$tmp" \
      || die "commit ${sha:0:12} has no backend/ directory (use --worktree for uncommitted work)" 2
    src="$tmp/backend"; label="ref $ref (${sha:0:12})"
  fi
  [[ -d "$src" ]] || die "backend source not found: $src" 2
  [[ -f "$src/manage.py" ]] || die "$src/manage.py not found — is this the backend project?" 2
  [[ -f "$src/requirements/development.txt" ]] || die "$src/requirements/development.txt not found" 2
  local results="${BACKEND_RESULTS_DIR:-$REPO_ROOT/backend/.remote-results}" run_id
  run_id="$(new_run_id)"
  info "backend tests on $(ssh_target): $label run=$run_id steps=$steps pytest_args=[${pytest_args[*]}]"
  info "files to ship: $(tar -C "$src" "${TAR_EXCLUDES[@]}" -cf - . | tar -t | grep -vc '/$')"
  if is_dry_run; then
    log "[dry-run] tar -C $src (excludes .env, sqlite, venvs, caches) | ssh → $DEPLOY_PATH/sandbox/backend (flock $DEPLOY_PATH/sandbox/.lock)"
    log "[dry-run] remote: venv $DEPLOY_PATH/sandbox/venv (uv, Python $PYTHON_VERSION, requirements/development.txt, rebuilt only on hash change)"
    log "[dry-run] remote: env -i style clean env + DJANGO_SETTINGS_MODULE=config.settings.development DATABASE_URL=sqlite:///$DEPLOY_PATH/sandbox/test.sqlite3 RATELIMIT_CACHE_URL=locmem:// CELERY_ENABLED=False SECRET_KEY/HEALTH_CHECK_PASSWORD=<random, generated on server>"
    log "[dry-run] remote: steps=$steps → ruff check . | ruff format --check . | manage.py check | makemigrations --check --dry-run | pytest --cov --cov-fail-under=80 --junitxml ${pytest_args[*]}"
    log "[dry-run] rsync $DEPLOY_PATH/sandbox/results/$run_id/ → $results/$run_id/"
    return 0
  fi
  check_ssh
  local rc=0
  REMOTE_FUNCS=("${REMOTE_FUNCS_ALL[@]}")
  REMOTE_VARS=(DEPLOY_PATH PYTHON_VERSION UV_BIN REMOTE_TEST_TIMEOUT REMOTE_TEST_LOCK_WAIT RESULTS_TO_KEEP)
  tar -C "$src" "${TAR_EXCLUDES[@]}" -czf - . \
    | remote_fn rw _rt_backend "$run_id" "$label" "$steps" "${pytest_args[@]}" || rc=$?
  if [[ $rc == 255 ]]; then die "SSH failure while running the backend tests" 255; fi
  fetch_results "$DEPLOY_PATH/sandbox/results/$run_id" "$results" "$run_id"
  if [[ $rc == 0 ]]; then info "backend tests PASSED (run $run_id)"; else err "backend tests FAILED with exit $rc (run $run_id)"; fi
  return "$rc"
}

cmd_qa() {
  local -a pytest_args=()
  while (($#)); do
    case "$1" in
      --dry-run) DRY_RUN=1; shift ;;
      --) shift; pytest_args+=("$@"); break ;;
      *) pytest_args+=("$1"); shift ;;
    esac
  done
  refuse_xdist "${pytest_args[@]}"
  require_vars API_DOMAIN WEB_DOMAIN DENTAL_GUARD_DOMAINS
  local src="${QA_SRC_DIR:-$REPO_ROOT/qa}" results="${QA_RESULTS_LOCAL_DIR:-$REPO_ROOT/qa/.results}" run_id
  [[ -d "$src" ]] || die "QA suite not found: $src" 2
  [[ -f "$src/requirements.txt" ]] || die "$src/requirements.txt not found" 2
  run_id="$(new_run_id)"
  info "QA suite on $(ssh_target) against https://$API_DOMAIN + https://$WEB_DOMAIN run=$run_id pytest_args=[${pytest_args[*]}]"
  if is_dry_run; then
    log "[dry-run] tar -C $src (excludes .results, venvs, caches, credentials) | ssh → $DEPLOY_PATH/qa/suite (flock $DEPLOY_PATH/qa/.lock)"
    log "[dry-run] remote: venv $DEPLOY_PATH/qa/venv (uv, Python $PYTHON_VERSION, requirements.txt, rebuilt only on hash change)"
    log "[dry-run] remote: pytest ${pytest_args[*]} with QA_BASE_URL=https://$API_DOMAIN QA_WEB_URL=https://$WEB_DOMAIN QA_HEALTH_TOKEN=<from shared/.env, server-side only> QA_* credentials=<from $DEPLOY_PATH/qa/credentials.env>"
    log "[dry-run] rsync $DEPLOY_PATH/qa/results/$run_id/ → $results/$run_id/"
    return 0
  fi
  check_ssh
  local rc=0
  REMOTE_FUNCS=("${REMOTE_FUNCS_ALL[@]}")
  REMOTE_VARS=(DEPLOY_PATH PYTHON_VERSION UV_BIN REMOTE_TEST_TIMEOUT REMOTE_TEST_LOCK_WAIT RESULTS_TO_KEEP
               API_DOMAIN WEB_DOMAIN DENTAL_GUARD_DOMAINS)
  tar -C "$src" "${TAR_EXCLUDES[@]}" -czf - . | remote_fn rw _rt_qa "$run_id" "${pytest_args[@]}" || rc=$?
  if [[ $rc == 255 ]]; then die "SSH failure while running the QA suite" 255; fi
  fetch_results "$DEPLOY_PATH/qa/results/$run_id" "$results" "$run_id"
  if [[ $rc == 0 ]]; then info "QA run PASSED (run $run_id)"; else err "QA run FAILED with exit $rc (run $run_id)"; fi
  return "$rc"
}

cmd_throttle_reset() {
  while (($#)); do parse_common_flag "$1" || die "unknown argument: $1" 2; shift; done
  local apply=1; is_dry_run && apply=0
  REMOTE_FUNCS=(); REMOTE_VARS=(DEPLOY_PATH)
  remote_fn ro _rt_throttle_reset "$apply"
}

# --------------------------------------------------------------- main
while (($#)); do
  parse_common_flag "$1" && { shift; continue; }
  break
done
sub="${1:-}"; [[ $# -gt 0 ]] && shift
case "$sub" in
  -h|--help|help|"") usage; [[ -n "$sub" ]]; exit $? ;;
  backend|qa|throttle-reset) ;;
  *) usage >&2; die "unknown command: $sub" 2 ;;
esac

load_env
# shellcheck disable=SC2119  # no extra required variables for this script
validate_common
case "$sub" in
  backend) cmd_backend "$@" ;;
  qa) cmd_qa "$@" ;;
  throttle-reset) cmd_throttle_reset "$@" ;;
esac
