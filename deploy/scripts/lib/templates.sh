# shellcheck shell=bash
# Template rendering (ADR-015): envsubst with an EXPLICIT variable list, so nginx variables such as
# $host, $uri, $remote_addr survive. Requires lib/common.sh.
#
#   render_all <out_dir>   renders every template into:
#     <out>/nginx/http/<API_DOMAIN>  <out>/nginx/http/<WEB_DOMAIN>   (port-80 bootstrap variants)
#     <out>/nginx/full/<API_DOMAIN>  <out>/nginx/full/<WEB_DOMAIN>   (TLS variants)
#     <out>/systemd/<BACKEND_SYSTEMD_SERVICE>.service
#     <out>/env/shared.env                                           (placeholders, no secrets)

FLASH_TEMPLATE_DIR="$REPO_ROOT/deploy"
# Variables substituted into templates. Nothing else is expanded.
FLASH_TEMPLATE_VARS=(APP_NAME API_DOMAIN WEB_DOMAIN DEPLOY_PATH BACKEND_PORT CERT_NAME SERVER_USER
                     GUNICORN_WORKERS GUNICORN_THREADS GUNICORN_TIMEOUT BACKEND_MEMORY_MAX
                     BACKEND_SYSTEMD_SERVICE NGINX_LISTEN_HTTP2)
# Variables that must be non-empty (NGINX_LISTEN_HTTP2 is derived and may be empty).
FLASH_TEMPLATE_REQUIRED=(APP_NAME API_DOMAIN WEB_DOMAIN DEPLOY_PATH BACKEND_PORT CERT_NAME SERVER_USER
                         GUNICORN_WORKERS GUNICORN_THREADS GUNICORN_TIMEOUT BACKEND_MEMORY_MAX
                         BACKEND_SYSTEMD_SERVICE)

validate_template_vars() {
  require_vars "${FLASH_TEMPLATE_REQUIRED[@]}"
  local v
  for v in BACKEND_PORT GUNICORN_WORKERS GUNICORN_THREADS GUNICORN_TIMEOUT; do
    [[ "${!v}" =~ ^[0-9]+$ ]] || die "$v must be a positive integer (got '${!v}')" 2
  done
  [[ "$BACKEND_MEMORY_MAX" =~ ^[0-9]+[KMGT]?$ ]] || die "BACKEND_MEMORY_MAX must look like 700M" 2
  for v in API_DOMAIN WEB_DOMAIN; do
    [[ "${!v}" =~ ^[a-z0-9]([a-z0-9.-]*[a-z0-9])?$ ]] || die "$v is not a valid host name" 2
  done
  [[ "$API_DOMAIN" != "$WEB_DOMAIN" ]] || die "API_DOMAIN and WEB_DOMAIN must differ" 2
  [[ "$CERT_NAME" =~ ^[A-Za-z0-9._-]+$ ]] || die "CERT_NAME contains invalid characters" 2
  [[ "$BACKEND_SYSTEMD_SERVICE" =~ ^[A-Za-z0-9_.-]+$ ]] || die "BACKEND_SYSTEMD_SERVICE is invalid" 2
  # BLK-013 RESOLVED (TL): http2 is mandatory OFF. nginx 1.24 applies `listen … http2` to the whole 443
  # socket shared with dental-clinic, so "on" would switch dental to HTTP/2 as well.
  case "${NGINX_HTTP2:-off}" in
    off) NGINX_LISTEN_HTTP2="" ;;
    on) die "NGINX_HTTP2=on is refused (BLK-013): http2 on the shared 443 socket would change dental-clinic; set NGINX_HTTP2=off" 2 ;;
    *) die "NGINX_HTTP2 must be off (BLK-013)" 2 ;;
  esac
  export NGINX_LISTEN_HTTP2
}

# _render_one <template> <output>
_render_one() {
  local tpl="$1" out="$2" list="" v
  [[ -f "$tpl" ]] || die "template not found: $tpl" 1
  for v in "${FLASH_TEMPLATE_VARS[@]}"; do list+="\${$v} "; done
  mkdir -p "$(dirname "$out")"
  envsubst "$list" < "$tpl" > "$out"
  # any ${UPPER_CASE} left means a template uses a variable outside the explicit list
  if grep -nE '\$\{[A-Z_][A-Z0-9_]*\}' "$out" >&2; then
    die "unresolved \${VAR} in $out (add it to FLASH_TEMPLATE_VARS or fix the template)" 2
  fi
}

render_all() {
  local out="$1"
  validate_template_vars
  export "${FLASH_TEMPLATE_VARS[@]}"
  local t="$FLASH_TEMPLATE_DIR"
  _render_one "$t/nginx/api.http.conf.template" "$out/nginx/http/$API_DOMAIN"
  _render_one "$t/nginx/web.http.conf.template" "$out/nginx/http/$WEB_DOMAIN"
  _render_one "$t/nginx/api.conf.template"      "$out/nginx/full/$API_DOMAIN"
  _render_one "$t/nginx/web.conf.template"      "$out/nginx/full/$WEB_DOMAIN"
  _render_one "$t/systemd/backend.service.template" "$out/systemd/$BACKEND_SYSTEMD_SERVICE.service"
  _render_one "$t/env/shared.env.template"      "$out/env/shared.env"
  chmod 0644 "$out"/nginx/*/* "$out"/systemd/*.service
  chmod 0600 "$out/env/shared.env"
}
