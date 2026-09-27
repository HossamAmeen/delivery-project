#!/usr/bin/env bash
# TLS for exactly the two Flash names (ADR-015). Idempotent.
#   1. skip issuance if cert ${CERT_NAME} exists and covers ${API_DOMAIN} + ${WEB_DOMAIN}; otherwise:
#      sudo certbot certonly --nginx --cert-name ${CERT_NAME} -d ${API_DOMAIN} -d ${WEB_DOMAIN}
#        --non-interactive --agree-tos [-m ${LETSENCRYPT_EMAIL}] --deploy-hook "nginx -t && systemctl reload nginx"
#      LETSENCRYPT_EMAIL is optional: empty → no -m, the registered production ACME account is reused
#      (fails early if `certbot show_account` finds none). Never --register-unsafely-without-email.
#   2. switch both Flash sites to the full TLS templates via the nginx safe-apply.
#   3. sudo certbot renew --dry-run --cert-name ${CERT_NAME}
# Usage: tls.sh [--dry-run]
FLASH_SCRIPT=tls
set -euo pipefail
# shellcheck source=lib/common.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib/common.sh"
# shellcheck source=lib/ops.sh
source "$FLASH_LIB_DIR/ops.sh"
trap ops_cleanup EXIT
while (($#)); do
  parse_common_flag "$1" && { shift; continue; }
  case "$1" in -h|--help) sed -n '2,13p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;; *) die "unknown argument: $1" 2 ;; esac
done
ops_init
LETSENCRYPT_EMAIL="${LETSENCRYPT_EMAIL:-}"
[[ -z "$LETSENCRYPT_EMAIL" || "$LETSENCRYPT_EMAIL" =~ ^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$ ]] \
  || die "LETSENCRYPT_EMAIL is not an e-mail address" 2
ops_lock
ops_guard_begin

step "1/3 certificate $CERT_NAME for $API_DOMAIN $WEB_DOMAIN"
state="$(ops_remote ro _fs_tls_state)"
info "certificate state: $state"
if [[ "$state" == covers ]]; then
  info "certificate exists and covers both names — issuance skipped"
else
  ops_remote ro _fs_flash_sites_enabled \
    || die "the Flash nginx sites are not enabled (run 'make setup-server' first: the port-80 variants answer the ACME challenge)" 1
  if [[ -z "$LETSENCRYPT_EMAIL" ]]; then
    ops_remote ro _fs_tls_account \
      || die "LETSENCRYPT_EMAIL is empty and 'certbot show_account' finds no registered production account — set LETSENCRYPT_EMAIL in .env" 2
    info "LETSENCRYPT_EMAIL empty: reusing the registered Let's Encrypt production account (no -m)"
  fi
  ops_remote rw _fs_tls_issue "$LETSENCRYPT_EMAIL" || die "certbot certonly failed" 1
fi

step "2/3 switch both Flash sites to the TLS templates (nginx safe-apply)"
ops_render
full="$(ops_mktemp nginx)"; cp "$OPS_RENDER_DIR/nginx/full/$API_DOMAIN" "$OPS_RENDER_DIR/nginx/full/$WEB_DOMAIN" "$full/"
ops_stage_upload "$full"
ops_remote rw _fs_nginx_safe_apply "$OPS_STAGE" 0 || { ops_stage_cleanup; die "nginx safe-apply failed (previous files restored, not reloaded)" 1; }
ops_stage_cleanup

step "3/3 renewal dry-run (scoped to $CERT_NAME)"
ops_remote rw _fs_tls_renew_dry_run || die "certbot renew --dry-run failed" 1

ops_guard_end
info "tls done"
