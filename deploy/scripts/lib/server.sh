# shellcheck shell=bash
# Server-side functions (_fs_*), shipped over SSH by ops_remote (lib/ops.sh) → remote_fn (lib/common.sh).
# They run ON THE SERVER as SERVER_USER. Callers use `ops_remote rw` for anything that changes state
# (dry-run is then enforced by the transport) and `ops_remote ro` for read-only probes.
# Variables available remotely (REMOTE_VARS in ops.sh): DEPLOY_PATH API_DOMAIN WEB_DOMAIN BACKEND_PORT
#   BACKEND_SYSTEMD_SERVICE CERT_NAME UV_BIN PYTHON_VERSION RELEASES_TO_KEEP DB_BACKUPS_TO_KEEP MIN_FREE_DISK_MB
# Secrets (SECRET_KEY, HEALTH_CHECK_PASSWORD) are read on the server only and never printed.

# ------------------------------------------------------------------ generic
_fs_fail() { echo "[remote] ERROR: $*" >&2; return 1; }

_fs_valid_release_id() { [[ "$1" =~ ^[0-9]{8}-[0-9]{6}$ ]]; }

# Exports KEY=VALUE lines of shared/.env into the current (sub)shell. No eval, no source.
_fs_load_shared_env() {
  local f="${1:-$DEPLOY_PATH/shared/.env}" line
  [[ -r "$f" ]] || { echo "[remote] $f is missing — run 'make setup-server'" >&2; return 2; }
  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ "$line" =~ ^[[:space:]]*(#|$) ]] && continue
    [[ "$line" =~ ^([A-Z_][A-Z0-9_]*)=(.*)$ ]] || continue
    export "${BASH_REMATCH[1]}=${BASH_REMATCH[2]}"
  done < "$f"
}

# Prints the value of one key of shared/.env (stdout; callers capture it, never echo it).
_fs_shared_env_value() {
  local key="$1" f="$DEPLOY_PATH/shared/.env" line
  [[ -r "$f" ]] || return 1
  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ "$line" == "$key="* ]] && { printf '%s' "${line#*=}"; return 0; }
  done < "$f"
  return 1
}

_fs_sha() { if [[ -r "$1" ]]; then sha256sum < "$1" | cut -d' ' -f1; else echo absent; fi; }

# ro: compare a server file with a local sha. Prints unchanged | would-update | would-create.
_fs_plan_file() { # <label> <server path> <sha>
  local cur; cur="$(_fs_sha "$2")"
  if [[ "$cur" == "$3" ]]; then echo "unchanged     $1 ($2)"
  elif [[ "$cur" == absent ]]; then echo "would-create  $1 ($2)"
  else echo "would-update  $1 ($2)"; fi
}

_fs_disk_free_mb() { df -Pm "$DEPLOY_PATH" | awk 'NR==2 {print $4}'; }

_fs_cert_state() { # prints full | http
  if sudo -n test -e "/etc/letsencrypt/live/$CERT_NAME/fullchain.pem"; then echo full; else echo http; fi
}

# ------------------------------------------------------------------ staging (/tmp/flash-stage-*)
_fs_receive_stage() { # <dir>   tar.gz on stdin
  [[ "$1" == /tmp/flash-stage-* && "$1" != *..* ]] || _fs_fail "bad stage dir $1" || return 2
  rm -rf "$1"; mkdir -m 0700 "$1"
  tar -xzf - -C "$1"
}
_fs_cleanup_stage() {
  [[ "$1" == /tmp/flash-stage-* && "$1" != *..* ]] || return 0
  rm -rf "$1"
}

# ------------------------------------------------------------------ shared/.env
_fs_template_keys() { grep -oE '^[A-Z_][A-Z0-9_]*=' "$1" | tr -d '=' | sort -u; }

_fs_shared_env_plan() { # <target> <keys...>   (ro)
  local target="$1"; shift
  if [[ ! -e "$target" ]]; then echo "would-create  $target (0600; SECRET_KEY + HEALTH_CHECK_PASSWORD generated on the server)"; return 0; fi
  local k missing=()
  for k in "$@"; do grep -q "^$k=" "$target" || missing+=("$k"); done
  echo "exists        $target (mode $(stat -c %a "$target"); never overwritten)"
  ((${#missing[@]} == 0)) || echo "MISSING KEYS  ${missing[*]} — add them by hand (values: deploy/env/shared.env.template)"
}

_fs_shared_env_install() { # <staged template> <target>   (rw)
  local tpl="$1" target="$2" line k v tmp missing=()
  if [[ -e "$target" ]]; then
    while IFS= read -r k; do grep -q "^$k=" "$target" || missing+=("$k"); done < <(_fs_template_keys "$tpl")
    [[ "$(stat -c %a "$target")" == 600 ]] || { chmod 600 "$target"; echo "fixed mode 0600 on $target"; }
    grep -q '=__GENERATE__$' "$target" && echo "WARNING: $target still contains __GENERATE__ placeholders" >&2
    echo "exists: $target (not overwritten)"
    ((${#missing[@]} == 0)) || echo "MISSING KEYS in $target: ${missing[*]} — add them by hand (see deploy/env/shared.env.template)"
    return 0
  fi
  tmp="$target.tmp.$$"
  ( umask 077
    while IFS= read -r line || [[ -n "$line" ]]; do
      if [[ "$line" =~ ^([A-Z_][A-Z0-9_]*)=__GENERATE__$ ]]; then
        k="${BASH_REMATCH[1]}"
        v="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
        printf '%s=%s\n' "$k" "$v"
      else
        printf '%s\n' "$line"
      fi
    done < "$tpl" > "$tmp" )
  mv -f "$tmp" "$target"; chmod 600 "$target"
  echo "created: $target (0600; generated on the server: $(grep -oE '^[A-Z_]+=__GENERATE__' "$tpl" | cut -d= -f1 | tr '\n' ' '))"
}

# ------------------------------------------------------------------ systemd unit
_fs_unit_install() { # <staged unit file>   (rw)
  local src="$1" dst="/etc/systemd/system/$BACKEND_SYSTEMD_SERVICE.service" changed=0
  [[ "$BACKEND_SYSTEMD_SERVICE" == flash-* ]] || _fs_fail "service name must start with flash-" || return 2
  echo "[remote] systemd-analyze verify (a missing ExecStart binary is expected before the first release):"
  systemd-analyze verify "$src" 2>&1 | sed 's/^/  /' || true
  if cmp -s "$src" "$dst"; then echo "unit unchanged: $dst"
  else sudo -n install -m 0644 -o root -g root "$src" "$dst"; changed=1; echo "installed: $dst"; sudo -n systemctl daemon-reload; fi
  if ! systemctl is-enabled -q "$BACKEND_SYSTEMD_SERVICE" 2>/dev/null; then
    sudo -n systemctl enable "$BACKEND_SYSTEMD_SERVICE"; echo "enabled: $BACKEND_SYSTEMD_SERVICE"
  fi
  if [[ -L "$DEPLOY_PATH/current" ]]; then
    if [[ $changed == 1 ]] || ! systemctl is-active -q "$BACKEND_SYSTEMD_SERVICE"; then
      sudo -n systemctl restart "$BACKEND_SYSTEMD_SERVICE"; echo "restarted: $BACKEND_SYSTEMD_SERVICE"
    fi
  else
    echo "not started: no current release yet (first 'make deploy' starts it)"
  fi
}

_fs_restart_backend() { # (rw)
  sudo -n systemctl restart "$BACKEND_SYSTEMD_SERVICE"

  for _ in $(seq 1 15); do systemctl is-active -q "$BACKEND_SYSTEMD_SERVICE" && break; sleep 1; done
  echo "$BACKEND_SYSTEMD_SERVICE: $(systemctl is-active "$BACKEND_SYSTEMD_SERVICE" || true)"
}

# ------------------------------------------------------------------ nginx safe-apply (ADR-015 reload rule)
# <stage dir containing exactly ${API_DOMAIN} and/or ${WEB_DOMAIN}> <force 0|1>
# backup → install → nginx -t → (fail: restore, nginx -t, return 1, NO reload) → reload.
# Writes under /etc/nginx only the two Flash site files and their sites-enabled symlinks.
# Backups go to /tmp/flash-nginx-backup-* (never under /etc/nginx: the dental guard hashes it all).
# Test mode (validation only): FLASH_NGINX_ROOT=/tmp/flash-* + FLASH_NGINX_CONF=<test nginx.conf> redirect
# the writes and `nginx -t -c`, and the reload is skipped. Unset in every operator script.
_fs_nginx_safe_apply() {
  local stage="$1" force="${2:-0}" root="${FLASH_NGINX_ROOT:-/etc/nginx}" avail en
  local f n changed=0 backup out rc
  local -a names=() ntest=(nginx -t)
  if [[ "$root" != /etc/nginx ]]; then
    [[ "$root" == /tmp/flash-* && -n "${FLASH_NGINX_CONF:-}" ]] || _fs_fail "test root must be /tmp/flash-* with FLASH_NGINX_CONF" || return 2
    ntest=(nginx -t -c "$FLASH_NGINX_CONF")
  fi
  avail="$root/sites-available"; en="$root/sites-enabled"
  [[ -n "$API_DOMAIN" && -n "$WEB_DOMAIN" ]] || _fs_fail "domains not set" || return 2
  for f in "$stage"/*; do
    [[ -e "$f" ]] || continue
    n="$(basename "$f")"
    [[ "$n" == "$API_DOMAIN" || "$n" == "$WEB_DOMAIN" ]] || _fs_fail "refusing nginx file '$n' (only $API_DOMAIN / $WEB_DOMAIN)" || return 2
    [[ "$n" != *dental* ]] || _fs_fail "refusing '$n'" || return 2
    names+=("$n")
  done
  ((${#names[@]} > 0)) || _fs_fail "no site files in $stage" || return 2
  for n in "${names[@]}"; do
    if ! cmp -s "$stage/$n" "$avail/$n" || [[ "$(readlink "$en/$n" 2>/dev/null)" != "$avail/$n" ]]; then changed=1; fi
  done
  if [[ $changed == 0 ]]; then
    if [[ "$force" != 1 ]]; then echo "nginx: Flash site files unchanged (${names[*]}) — no reload"; return 0; fi
    echo "nginx: files unchanged; forced reload requested"
    out="$(sudo -n "${ntest[@]}" 2>&1)" && rc=0 || rc=$?
    printf '%s\n' "$out" | sed 's/^/  [nginx -t] /'
    [[ $rc == 0 ]] || _fs_fail "nginx -t failed — not reloading" || return 1
    _fs_nginx_reload; return 0
  fi
  backup="$(mktemp -d /tmp/flash-nginx-backup-XXXXXX)"
  for n in "${names[@]}"; do
    [[ -f "$avail/$n" ]] && cp -p "$avail/$n" "$backup/$n.conf"
    [[ -L "$en/$n" ]] && readlink "$en/$n" > "$backup/$n.link"
  done
  echo "nginx: backup of the previous Flash files in $backup"
  for n in "${names[@]}"; do
    sudo -n install -m 0644 -o root -g root "$stage/$n" "$avail/$n"
    sudo -n ln -sfn "$avail/$n" "$en/$n"
    echo "nginx: wrote $avail/$n (+ sites-enabled link)"
  done
  out="$(sudo -n "${ntest[@]}" 2>&1)" && rc=0 || rc=$?
  printf '%s\n' "$out" | sed 's/^/  [nginx -t] /'
  if [[ $rc != 0 ]]; then
    echo "[remote] nginx -t FAILED — restoring the previous Flash files, NOT reloading" >&2
    for n in "${names[@]}"; do
      if [[ -f "$backup/$n.conf" ]]; then sudo -n install -m 0644 -o root -g root "$backup/$n.conf" "$avail/$n"
      else sudo -n rm -f -- "$avail/$n"; fi
      if [[ -f "$backup/$n.link" ]]; then sudo -n ln -sfn "$(cat "$backup/$n.link")" "$en/$n"
      else sudo -n rm -f -- "$en/$n"; fi
    done
    out="$(sudo -n "${ntest[@]}" 2>&1)" && rc=0 || rc=$?
    printf '%s\n' "$out" | sed 's/^/  [nginx -t after restore] /'
    return 1
  fi
  _fs_nginx_reload
}
_fs_nginx_reload() { # only ever called right after a passing nginx -t
  if [[ -n "${FLASH_NGINX_ROOT:-}" ]]; then echo "nginx: TEST MODE — reload skipped"; return 0; fi
  sudo -n systemctl reload nginx
  echo "nginx: reloaded ($(systemctl is-active nginx))"
}

# ------------------------------------------------------------------ releases
_fs_current_id() {
  local t; t="$(readlink "$DEPLOY_PATH/current" 2>/dev/null)" || return 1
  basename "$t"
}
_fs_releases() { find "$DEPLOY_PATH/releases" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | grep -E '^[0-9]{8}-[0-9]{6}$' | sort; }
_fs_previous_of() { # <id> → the release just before it (by id / UTC time)
  _fs_releases | awk -v c="$1" '$0 < c {p=$0} END {if (p != "") print p}'
}
_fs_release_info() { # ro: current, releases, disk
  echo "current:  $(_fs_current_id || echo none)"
  echo "releases: $(_fs_releases | tr '\n' ' ')"
  echo "disk:     $(_fs_disk_free_mb) MB free on $DEPLOY_PATH (min ${MIN_FREE_DISK_MB})"
}
_fs_prepare_release_dir() { # <id>  (rw)
  _fs_valid_release_id "$1" || _fs_fail "invalid release id $1" || return 2
  [[ ! -e "$DEPLOY_PATH/releases/$1" ]] || _fs_fail "release $1 already exists" || return 2
  mkdir -m 0755 "$DEPLOY_PATH/releases/$1"
}
_fs_remove_release() { # <id>  (rw) — never the current one
  _fs_valid_release_id "$1" || return 2
  [[ "$(_fs_current_id || true)" != "$1" ]] || _fs_fail "refusing to remove the current release" || return 2
  rm -rf -- "${DEPLOY_PATH:?}/releases/$1"; echo "removed release $1"
}

_fs_venv_install() { # <id>  (rw)
  local rel="$DEPLOY_PATH/releases/$1"
  [[ -f "$rel/backend/requirements/production.txt" ]] || _fs_fail "$rel/backend/requirements/production.txt missing" || return 2
  echo "[remote] uv venv ($PYTHON_VERSION) + pip install -r requirements/production.txt"
  UV_PYTHON_PREFERENCE=only-managed UV_PYTHON_DOWNLOADS=never "$UV_BIN" venv --quiet --python "$PYTHON_VERSION" "$rel/venv"
  "$UV_BIN" pip install --quiet --python "$rel/venv/bin/python" -r "$rel/backend/requirements/production.txt"
  echo "[remote] venv ready: $("$rel/venv/bin/python" --version)"
}

_fs_manage() { # <id> <manage.py args...>  — runs in a subshell with shared/.env loaded
  local rel="$DEPLOY_PATH/releases/$1"; shift
  ( _fs_load_shared_env && cd "$rel/backend" && exec "$rel/venv/bin/python" manage.py "$@" )
}

_fs_check_deploy() { # <id>  (rw: part of the deploy pipeline)
  echo "[remote] manage.py check --deploy (warnings are logged, errors fail)"
  _fs_manage "$1" check --deploy 2>&1
}
_fs_collectstatic() { # <id>  (rw)
  echo "[remote] manage.py collectstatic --noinput → $DEPLOY_PATH/shared/static"
  _fs_manage "$1" collectstatic --noinput -v 1 2>&1 | tail -3
  return "${PIPESTATUS[0]}"
}

_fs_switch_current() { # <id>  (rw) atomic: ln -sfn tmp && mv -T
  local rel="$DEPLOY_PATH/releases/$1" prev
  _fs_valid_release_id "$1" || return 2
  [[ -d "$rel/backend" && -x "$rel/venv/bin/python" ]] || _fs_fail "release $1 is incomplete" || return 2
  prev="$(_fs_current_id || echo none)"
  ln -sfn "releases/$1" "$DEPLOY_PATH/current.tmp"
  mv -Tf "$DEPLOY_PATH/current.tmp" "$DEPLOY_PATH/current"
  echo "current: $prev -> $1"
}

# ------------------------------------------------------------------ SQLite (ADR-017)
_fs_db_path() { # prints the SQLite file path from shared/.env DATABASE_URL, or nothing
  local url; url="$(_fs_shared_env_value DATABASE_URL || true)"
  [[ "$url" == sqlite:////* ]] && printf '%s' "/${url#sqlite:////}"
}
_fs_sqlite_backup() { # <src db> <dst>  online backup API (safe under WAL)
  ( umask 077
    python3 - "$1" "$2" <<'PY'
import sqlite3, sys
src = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
dst = sqlite3.connect(sys.argv[2])
with dst:
    src.backup(dst)
dst.close(); src.close()
PY
  )
  chmod 600 "$2"
}

_fs_prune_backups() { # (rw) keep DB_BACKUPS_TO_KEEP of each kind; never the current release's rollback backup (its first)
  local keep="${DB_BACKUPS_TO_KEEP:-5}" dir="$DEPLOY_PATH/shared/backups" ref="" cur kind f
  cur="$(_fs_current_id || true)"
  [[ -n "$cur" && -f "$DEPLOY_PATH/releases/$cur/MIGRATION_STATE" ]] && \
    ref="$(grep -oE 'backup=[^ ]+' "$DEPLOY_PATH/releases/$cur/MIGRATION_STATE" | cut -d= -f2 | grep -v '^none$' | head -1 || true)"
  for kind in flash pre-rollback; do
    while IFS= read -r f; do
      [[ -n "$f" ]] || continue
      [[ " $ref " == *" $f "* ]] && continue
      rm -f -- "$f"; echo "pruned backup $f"
    done < <(find "$dir" -maxdepth 1 -type f -name "$kind-*.sqlite3" -printf '%T@ %p\n' | sort -rn | tail -n +"$((keep + 1))" | cut -d' ' -f2-)
  done
}

_fs_migrate() { # <id>  (rw) plan → backup (if DB exists) → migrate → MIGRATION_STATE
  local id="$1" rel="$DEPLOY_PATH/releases/$1" db existed=0 plan applied=no backup=none ts
  db="$(_fs_db_path)"
  [[ -n "$db" && -f "$db" ]] && existed=1
  echo "[remote] migrate --plan ($id):"
  plan="$(_fs_manage "$id" migrate --plan 2>&1)" || { printf '%s\n' "$plan"; return 1; }
  printf '%s\n' "$plan" | sed 's/^/  /'
  grep -q "No planned migration operations" <<< "$plan" || applied=yes
  if [[ -z "$db" ]]; then
    echo "[remote] WARNING: DATABASE_URL is not an absolute sqlite path — no backup taken"
  elif [[ $existed == 1 ]]; then
    ts="$(date -u +%Y%m%d-%H%M%S)"; backup="$DEPLOY_PATH/shared/backups/flash-$id-$ts.sqlite3"
    _fs_sqlite_backup "$db" "$backup"
    echo "[remote] pre-migrate backup: $backup ($(du -h "$backup" | cut -f1))"
  else
    echo "[remote] no database yet (first deploy): no backup"
  fi
  _fs_manage "$id" migrate --noinput 2>&1 | sed 's/^/  /'
  [[ "${PIPESTATUS[0]}" == 0 ]] || return 1
  printf 'at=%s backup=%s applied=%s\n' "$(date -u +%FT%TZ)" "$backup" "$applied" >> "$rel/MIGRATION_STATE"
  echo "[remote] MIGRATION_STATE: backup=$backup applied=$applied"
  _fs_prune_backups
}

# ------------------------------------------------------------------ rollback (ADR-013 + ADR-017)
_fs_rollback() { # <target id or ""> <auto|always|never> [plan 0|1]   (rw; plan=1 is read-only, used by --dry-run)
  local target="$1" mode="$2" plan="${3:-0}" cur state applied=no backup="" restore=0 db ts
  cur="$(_fs_current_id)" || _fs_fail "no current release — nothing to roll back" || return 2
  [[ -n "$target" ]] || target="$(_fs_previous_of "$cur")"
  [[ -n "$target" ]] || _fs_fail "no previous release before $cur — cannot roll back" || return 2
  _fs_valid_release_id "$target" || _fs_fail "invalid release id '$target'" || return 2
  [[ "$target" != "$cur" ]] || _fs_fail "$target is already current" || return 2
  [[ -d "$DEPLOY_PATH/releases/$target/backend" && -x "$DEPLOY_PATH/releases/$target/venv/bin/python" ]] \
    || _fs_fail "release $target is missing or incomplete" || return 2
  state="$DEPLOY_PATH/releases/$cur/MIGRATION_STATE"
  if [[ -f "$state" ]]; then
    grep -q 'applied=yes' "$state" && applied=yes
    backup="$(grep -oE 'backup=[^ ]+' "$state" | cut -d= -f2 | grep -v '^none$' | head -1 || true)"
  fi
  case "$mode" in
    never) restore=0 ;;
    always) restore=1 ;;
    auto) [[ $applied == yes ]] && restore=1 ;;
    *) _fs_fail "restore mode must be auto|always|never" || return 2 ;;
  esac
  if [[ $restore == 1 && ( -z "$backup" || ! -f "$backup" ) ]]; then
    echo "[remote] WARNING: DB restore wanted (mode=$mode, migrations applied=$applied) but $cur has no pre-migrate backup (first deploy?) — database NOT restored"
    restore=0
  fi
  echo "[remote] rollback: $cur -> $target (mode=$mode, $cur applied migrations: $applied, restore DB: $([[ $restore == 1 ]] && echo "yes, from $backup" || echo no))"
  [[ "$plan" == 1 ]] && { echo "[remote] plan only: nothing changed"; return 0; }
  _fs_switch_current "$target"
  if [[ $restore == 1 ]]; then
    db="$(_fs_db_path)"
    echo "[remote] WARNING: restoring $backup — every write made after $cur was deployed is LOST (a copy of the current DB is kept)"
    sudo -n systemctl stop "$BACKEND_SYSTEMD_SERVICE"
    ts="$(date -u +%Y%m%d-%H%M%S)"
    if [[ -f "$db" ]]; then
      _fs_sqlite_backup "$db" "$DEPLOY_PATH/shared/backups/pre-rollback-$ts.sqlite3"
      echo "[remote] saved current DB as $DEPLOY_PATH/shared/backups/pre-rollback-$ts.sqlite3"
    fi
    ( umask 077; cp -f "$backup" "$db.restore.tmp" ); mv -f "$db.restore.tmp" "$db"; rm -f "$db-wal" "$db-shm"; chmod 600 "$db"
    sudo -n systemctl start "$BACKEND_SYSTEMD_SERVICE"
    echo "[remote] database restored from $backup; $BACKEND_SYSTEMD_SERVICE started"
  else
    _fs_restart_backend
  fi
  echo "ROLLBACK_RESULT from=$cur to=$target db_restored=$restore"
}

_fs_prune_releases() { # (rw) keep RELEASES_TO_KEEP newest + always current and its previous
  local keep="${RELEASES_TO_KEEP:-5}" cur prev id
  cur="$(_fs_current_id || true)"; prev=""
  [[ -n "$cur" ]] && prev="$(_fs_previous_of "$cur")"
  while IFS= read -r id; do
    [[ -n "$id" && "$id" != "$cur" && "$id" != "$prev" ]] || continue
    rm -rf -- "${DEPLOY_PATH:?}/releases/$id"; echo "pruned release $id"
  done < <(_fs_releases | sort -r | tail -n +"$((keep + 1))")
  echo "releases kept: $(_fs_releases | tr '\n' ' ')(current=$cur previous=${prev:-none})"
}

# ------------------------------------------------------------------ health (ADR-015)
# <local_only 0|1>. Token read from shared/.env here and passed to curl on stdin (-H @-): never in argv/output.
_fs_health() {
  local local_only="${1:-0}" token fails=0 body code scheme=https
  # Until tls.sh has issued the certificate, the Flash sites are the port-80 bootstrap variants.
  [[ "$(_fs_cert_state)" == full ]] || { scheme=http; echo "NOTE  certificate $CERT_NAME not issued yet: public checks use http:// (run 'make tls')"; }
  token="$(_fs_shared_env_value HEALTH_CHECK_PASSWORD || true)"
  body="$(mktemp /tmp/flash-health-XXXXXX)"
  _hc() { # <name> <url> <expect substring> [token]
    local name="$1" url="$2" want="$3" use_token="${4:-0}"
    if [[ "$use_token" == 1 ]]; then
      code="$(printf 'X-Health-Check-Token: %s\n' "$token" | curl -sS -o "$body" -w '%{http_code}' --max-time 10 -H @- "$url" 2>/dev/null)" || code="${code:-000}"
    else
      code="$(curl -sS -o "$body" -w '%{http_code}' --max-time 10 "$url" 2>/dev/null)" || code="${code:-000}"
    fi
    if [[ "$code" == 200 ]] && grep -q -- "$want" "$body"; then echo "PASS  $name ($code)"
    else echo "FAIL  $name (HTTP $code$([[ "$code" == 200 ]] && echo ", body lacks '$want'"))"; fails=$((fails + 1)); fi
  }
  if [[ -z "$token" ]]; then echo "FAIL  health token (HEALTH_CHECK_PASSWORD missing in shared/.env)"; fails=$((fails + 1)); fi
  if systemctl is-active -q "$BACKEND_SYSTEMD_SERVICE"; then echo "PASS  systemctl is-active $BACKEND_SYSTEMD_SERVICE"
  else echo "FAIL  systemctl is-active $BACKEND_SYSTEMD_SERVICE ($(systemctl is-active "$BACKEND_SYSTEMD_SERVICE" || true))"; fails=$((fails + 1)); fi
  _hc "local  /api/health/"       "http://127.0.0.1:$BACKEND_PORT/api/health/"       '"healthy"' 1
  _hc "local  /api/health/ready/" "http://127.0.0.1:$BACKEND_PORT/api/health/ready/" '"ready"'   1
  if [[ "$local_only" != 1 ]]; then
    if [[ "$scheme" == https ]]; then
      _hc "public /api/health/"       "https://$API_DOMAIN/api/health/"       '"healthy"' 1
      _hc "public /api/health/ready/" "https://$API_DOMAIN/api/health/ready/" '"ready"'   1
    else
      echo "SKIP  public token checks (never send the health token over plain http)"
    fi
    _hc "public /api/status/"       "$scheme://$API_DOMAIN/api/status/"       '"ok"'      0
    _hc "web    $scheme://$WEB_DOMAIN/" "$scheme://$WEB_DOMAIN/"            'id="app"'  0
    if sudo -n nginx -t >/dev/null 2>&1; then echo "PASS  nginx -t"; else echo "FAIL  nginx -t"; fails=$((fails + 1)); fi
  fi
  rm -f "$body"
  return $((fails > 0))
}

# ------------------------------------------------------------------ QA users (ADR-018)
_fs_seed_qa_users() { # (rw) random passwords generated here; usernames printed only
  local id rel cred tmp has_inactive=0 spec user role flags pw var
  id="$(_fs_current_id)" || _fs_fail "no current release — deploy first" || return 2
  rel="$DEPLOY_PATH/releases/$id"; cred="$DEPLOY_PATH/qa/credentials.env"
  _fs_manage "$id" create_role_user --help 2>/dev/null | grep -q -- '--inactive' && has_inactive=1
  tmp="$cred.tmp.$$"
  ( umask 077; : > "$tmp" )
  for spec in "qa_customer:CUSTOMER:CUSTOMER:" "qa_driver:DRIVER:DRIVER:" "qa_store:STORE:STORE:" \
              "qa_admin:ADMIN:ADMIN:--staff --superuser" "qa_inactive:CUSTOMER:INACTIVE:--inactive"; do
    IFS=':' read -r user role var flags <<< "$spec"
    if [[ "$flags" == *--inactive* && $has_inactive == 0 ]]; then
      echo "WARNING: create_role_user has no --inactive yet (TASK-016) — skipping $user"; continue
    fi
    pw="$(python3 -c 'import secrets; print(secrets.token_urlsafe(24))')"
    # shellcheck disable=SC2086  # $flags is a controlled word list
    if ! printf '%s\n' "$pw" | _fs_manage "$id" create_role_user --username "$user" --role "$role" $flags --password-stdin --update >/dev/null; then
      rm -f "$tmp"; _fs_fail "create_role_user failed for $user" || return 1
    fi
    printf 'QA_%s_USERNAME=%s\nQA_%s_PASSWORD=%s\n' "$var" "$user" "$var" "$pw" >> "$tmp"
    echo "seeded: $user (role $role${flags:+, $flags})"
  done
  mv -f "$tmp" "$cred"; chmod 600 "$cred"
  echo "credentials written to $cred (0600; passwords never printed)"
}

# ------------------------------------------------------------------ Playwright (setup-server --with-e2e)
_fs_e2e_install() { # (rw) apt deps via Playwright + Chromium into qa/browsers
  local venv="$DEPLOY_PATH/qa/venv" free
  [[ -x "$venv/bin/python" ]] && "$venv/bin/python" -c 'import playwright' 2>/dev/null \
    || _fs_fail "$venv has no playwright — run 'make qa-remote ARGS=\"--collect-only -q\"' first" || return 2
  free="$(_fs_disk_free_mb)"
  (( free >= MIN_FREE_DISK_MB + 700 )) || _fs_fail "only ${free} MB free; need MIN_FREE_DISK_MB+700" || return 1
  echo "[remote] packages Playwright would install (install-deps --dry-run):"
  sudo -n "$venv/bin/python" -m playwright install-deps --dry-run chromium 2>&1 | sed 's/^/  /'
  sudo -n "$venv/bin/python" -m playwright install-deps chromium
  mkdir -p "$DEPLOY_PATH/qa/browsers"
  PLAYWRIGHT_BROWSERS_PATH="$DEPLOY_PATH/qa/browsers" "$venv/bin/python" -m playwright install chromium
  echo "[remote] chromium installed in $DEPLOY_PATH/qa/browsers ($(du -sh "$DEPLOY_PATH/qa/browsers" | cut -f1))"
}

# ------------------------------------------------------------------ TLS (ADR-015)
_fs_tls_state() { # ro → covers | missing | partial
  local line
  line="$(sudo -n certbot certificates --cert-name "$CERT_NAME" 2>/dev/null | grep -m1 'Domains:' || true)"
  if [[ -z "$line" ]]; then echo missing; return 0; fi
  if [[ " $line " == *" $API_DOMAIN "* && " $line " == *" $WEB_DOMAIN "* ]]; then echo covers; else echo partial; fi
}
_fs_tls_account() { # ro → exit 0 when a registered production ACME account exists (email never printed)
  sudo -n certbot show_account >/dev/null 2>&1
}
_fs_flash_sites_enabled() { # ro
  [[ -L "/etc/nginx/sites-enabled/$API_DOMAIN" && -L "/etc/nginx/sites-enabled/$WEB_DOMAIN" ]]
}
_fs_tls_issue() { # <email or ""> (rw) — the exact ADR-015 command
  local -a mail=()
  [[ -n "$1" ]] && mail=(-m "$1")
  sudo -n certbot certonly --nginx --cert-name "$CERT_NAME" -d "$API_DOMAIN" -d "$WEB_DOMAIN" \
    --non-interactive --agree-tos "${mail[@]}" --deploy-hook "nginx -t && systemctl reload nginx"
}
_fs_tls_renew_dry_run() { # (rw: contacts the LE staging API; changes nothing on disk except certbot logs)
  sudo -n certbot renew --dry-run --cert-name "$CERT_NAME"
}

# ------------------------------------------------------------------ status / logs (read-only)
_fs_status() {
  local svc="$BACKEND_SYSTEMD_SERVICE" d
  echo "== unit $svc: active=$(systemctl is-active "$svc" 2>/dev/null || true) enabled=$(systemctl is-enabled "$svc" 2>/dev/null || true)"
  systemctl show -p MainPID -p ActiveEnterTimestamp -p NRestarts -p MemoryCurrent "$svc" 2>/dev/null | sed 's/^/   /'
  echo "== releases"; _fs_release_info | sed 's/^/   /'
  if [[ -n "$(_fs_current_id || true)" && -f "$DEPLOY_PATH/current/REVISION" ]]; then sed 's/^/   REVISION /' "$DEPLOY_PATH/current/REVISION"; fi
  echo "== backups"; find "$DEPLOY_PATH/shared/backups" -maxdepth 1 -type f -printf '   %TY-%Tm-%Td %TH:%TM  %s bytes  %f\n' 2>/dev/null | sort | tail -10
  echo "== nginx Flash sites"
  for d in "$API_DOMAIN" "$WEB_DOMAIN"; do
    echo "   $d: available=$([[ -f /etc/nginx/sites-available/$d ]] && echo yes || echo no) enabled=$([[ -L /etc/nginx/sites-enabled/$d ]] && echo yes || echo no) variant=$(grep -q 'listen 443' "/etc/nginx/sites-available/$d" 2>/dev/null && echo tls || echo http)"
  done
  echo "== certificate $CERT_NAME: $(_fs_tls_state)"
  sudo -n certbot certificates --cert-name "$CERT_NAME" 2>/dev/null | grep -E 'Domains|Expiry' | sed 's/^ */   /' || true
}
_fs_logs() { # <lines> <follow 0|1>
  local -a f=(); [[ "$2" == 1 ]] && f=(-f)
  journalctl -u "$BACKEND_SYSTEMD_SERVICE" -n "$1" --no-pager "${f[@]}"
}
