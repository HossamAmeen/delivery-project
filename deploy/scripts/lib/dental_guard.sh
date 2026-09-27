# shellcheck shell=bash
# Dental-clinic non-interference guard (ADR-015). Read-only against everything dental owns.
# Requires lib/common.sh to be sourced first. All values come from .env.
#
#   dental_preflight                 static assertions + remote port check (exit 3 on violation)
#   dental_snapshot <file>           writes a read-only snapshot of the dental footprint
#   dental_compare <before> <after>  exit 3 (loudly) if anything differs
#   dental_guard_begin / dental_guard_end   convenience pair used by setup/deploy/rollback/restart/tls
#
# Snapshot content (a superset of the ADR-015 list; see server-audit-2026-09-27.md, deviation 1):
#   - sha256 of every file under /etc/nginx/ (and the target of every symlink) except the two Flash
#     site files ${API_DOMAIN} / ${WEB_DOMAIN} in sites-available/ and sites-enabled/
#   - sha256 of /etc/letsencrypt/{options-ssl-nginx.conf,ssl-dhparams.pem} and renewal/*.conf except ${CERT_NAME}.conf
#   - the dental unit: is-active, MainPID, ActiveEnterTimestamp, NRestarts, unit file + drop-in sha256
#   - listener count on DENTAL_GUARD_PORT
#   - HTTPS status code of each DENTAL_GUARD_DOMAINS entry
# Flash never reads or lists DENTAL_GUARD_PATH.

DENTAL_GUARD_VARS=(DENTAL_GUARD_DOMAINS DENTAL_GUARD_SERVICE DENTAL_GUARD_PORT DENTAL_GUARD_PATH
                   API_DOMAIN WEB_DOMAIN BACKEND_PORT BACKEND_SYSTEMD_SERVICE CERT_NAME)

_dg_fail() { err "DENTAL GUARD: $1"; exit 3; }

# ---------------------------------------------------------------- remote (read-only) functions
_dg_remote_snapshot() {
  local f d code svc_file
  printf '# flash dental snapshot host=%s taken=%s\n' "$(hostname)" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  while IFS= read -r -d '' f; do
    case "$f" in
      "/etc/nginx/sites-available/$API_DOMAIN"|"/etc/nginx/sites-available/$WEB_DOMAIN"|\
      "/etc/nginx/sites-enabled/$API_DOMAIN"|"/etc/nginx/sites-enabled/$WEB_DOMAIN") continue ;;
    esac
    if [[ -L "$f" ]]; then printf 'nginx-link %s -> %s\n' "$f" "$(readlink "$f")"; fi
    if [[ -f "$f" && -r "$f" ]]; then
      printf 'nginx-file %s %s\n' "$(sha256sum < "$f" | cut -d' ' -f1)" "$f"
    else
      printf 'nginx-file UNREADABLE-OR-DANGLING %s\n' "$f"
    fi
  done < <(find /etc/nginx \( -type f -o -type l \) -print0 | sort -z)
  for f in /etc/letsencrypt/options-ssl-nginx.conf /etc/letsencrypt/ssl-dhparams.pem; do
    [[ -r "$f" ]] && printf 'le-file %s %s\n' "$(sha256sum < "$f" | cut -d' ' -f1)" "$f"
  done
  for f in /etc/letsencrypt/renewal/*.conf; do
    [[ -e "$f" ]] || continue
    [[ "$f" == "/etc/letsencrypt/renewal/$CERT_NAME.conf" ]] && continue
    if [[ -r "$f" ]]; then printf 'le-renewal %s %s\n' "$(sha256sum < "$f" | cut -d' ' -f1)" "$f"
    else printf 'le-renewal UNREADABLE %s\n' "$f"; fi
  done
  printf 'service-active %s %s\n' "$DENTAL_GUARD_SERVICE" "$(systemctl is-active "$DENTAL_GUARD_SERVICE" 2>/dev/null || true)"
  printf 'service-state %s %s\n' "$DENTAL_GUARD_SERVICE" \
    "$(systemctl show -p MainPID -p ActiveEnterTimestamp -p NRestarts "$DENTAL_GUARD_SERVICE" 2>/dev/null | sort | tr '\n' ' ')"
  svc_file="$(systemctl show -p FragmentPath --value "$DENTAL_GUARD_SERVICE" 2>/dev/null || true)"
  for f in $svc_file $(systemctl show -p DropInPaths --value "$DENTAL_GUARD_SERVICE" 2>/dev/null || true); do
    if [[ -r "$f" ]]; then printf 'service-file %s %s\n' "$(sha256sum < "$f" | cut -d' ' -f1)" "$f"; fi
  done
  printf 'port-listeners %s %s\n' "$DENTAL_GUARD_PORT" "$(ss -ltnH "sport = :$DENTAL_GUARD_PORT" | wc -l)"
  IFS=',' read -r -a _doms <<< "$DENTAL_GUARD_DOMAINS"
  for d in "${_doms[@]}"; do
    d="${d//[[:space:]]/}"; [[ -n "$d" ]] || continue
    code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 "https://$d/" || true)"
    if [[ "$code" == 000 ]]; then sleep 2; code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 "https://$d/" || true)"; fi
    printf 'https-status %s %s\n' "$d" "$code"
  done
}

# prints: free | held-by-<service> | busy pid=<pid>
_dg_remote_port_check() {
  local port="$1" svc="$2" pid
  if [[ -z "$(ss -ltnH "sport = :$port")" ]]; then echo free; return 0; fi
  pid="$(sudo -n ss -ltnpH "sport = :$port" | grep -o 'pid=[0-9]*' | head -1 | cut -d= -f2 || true)"
  if [[ -n "$pid" ]] && grep -q "/$svc.service" "/proc/$pid/cgroup" 2>/dev/null; then echo "held-by-$svc"
  else echo "busy pid=${pid:-unknown}"; fi
}

# ---------------------------------------------------------------- local API
dental_preflight() {
  require_vars "${DENTAL_GUARD_VARS[@]}"
  local d
  [[ "$BACKEND_PORT" =~ ^[0-9]+$ ]] || _dg_fail "BACKEND_PORT must be numeric"
  [[ "$BACKEND_PORT" != "$DENTAL_GUARD_PORT" ]] || _dg_fail "BACKEND_PORT=$BACKEND_PORT is dental's port"
  case "${DEPLOY_PATH%/}/" in
    "${DENTAL_GUARD_PATH%/}/"*) _dg_fail "DEPLOY_PATH=$DEPLOY_PATH is under DENTAL_GUARD_PATH" ;;
  esac
  case "${DENTAL_GUARD_PATH%/}/" in
    "${DEPLOY_PATH%/}/"*) _dg_fail "DENTAL_GUARD_PATH is under DEPLOY_PATH=$DEPLOY_PATH" ;;
  esac
  [[ "$BACKEND_SYSTEMD_SERVICE" == flash-* ]] || _dg_fail "BACKEND_SYSTEMD_SERVICE must start with 'flash-'"
  [[ "$BACKEND_SYSTEMD_SERVICE" != "$DENTAL_GUARD_SERVICE" ]] || _dg_fail "service name collides with dental's"
  for d in "$API_DOMAIN" "$WEB_DOMAIN" "$CERT_NAME"; do
    [[ "${d,,}" != *dental* ]] || _dg_fail "'$d' contains 'dental'"
    [[ ",${DENTAL_GUARD_DOMAINS// /}," != *",$d,"* ]] || _dg_fail "'$d' is a dental domain"
  done
  local state
  state="$(REMOTE_FUNCS=() REMOTE_VARS=(); remote_fn ro _dg_remote_port_check "$BACKEND_PORT" "$BACKEND_SYSTEMD_SERVICE")" \
    || _dg_fail "could not check port $BACKEND_PORT on the server"
  case "$state" in
    free|"held-by-$BACKEND_SYSTEMD_SERVICE") info "dental preflight OK (port $BACKEND_PORT: $state)" ;;
    *) _dg_fail "port $BACKEND_PORT is in use by another process ($state)" ;;
  esac
}

dental_snapshot() {
  local out="$1"
  require_vars "${DENTAL_GUARD_VARS[@]}"
  # shellcheck disable=SC2034  # read by remote_fn through dynamic scope
  local REMOTE_FUNCS=() REMOTE_VARS=(DENTAL_GUARD_DOMAINS DENTAL_GUARD_SERVICE DENTAL_GUARD_PORT API_DOMAIN WEB_DOMAIN CERT_NAME)
  remote_fn ro _dg_remote_snapshot > "$out" || _dg_fail "snapshot failed (see $out)"
  grep -q '^service-active ' "$out" || _dg_fail "snapshot incomplete: $out"
  info "dental snapshot: $out ($(grep -vc '^#' "$out") entries; $(grep -E '^(service-active|https-status)' "$out" | tr '\n' ';'))"
}

dental_compare() {
  local before="$1" after="$2" diffout
  if diffout="$(diff <(grep -v '^#' "$before") <(grep -v '^#' "$after"))"; then
    info "dental guard: before/after IDENTICAL ($(grep -vc '^#' "$after") entries)"
    return 0
  fi
  err "DENTAL GUARD: the dental-clinic footprint CHANGED during this operation:"
  printf '%s\n' "$diffout" >&2
  err "before=$before after=$after — stop and investigate before any further Flash operation."
  exit 3
}

# dental_guard_begin: preflight + before-snapshot. Sets DG_BEFORE / DG_AFTER.
dental_guard_begin() {
  local dir="${DENTAL_GUARD_DIR:-${TMPDIR:-/tmp}/flash-dental-guard}"
  mkdir -p "$dir"
  local id; id="$(new_run_id)"
  DG_BEFORE="$dir/$id-before.txt"; DG_AFTER="$dir/$id-after.txt"
  dental_preflight
  dental_snapshot "$DG_BEFORE"
}
dental_guard_end() {
  dental_snapshot "$DG_AFTER"
  dental_compare "$DG_BEFORE" "$DG_AFTER"
}
