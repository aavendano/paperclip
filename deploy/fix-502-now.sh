#!/usr/bin/env bash
# Corrige 502: restaura origen y aplica certificado válido para Cloudflare Full (strict).
set -euo pipefail

CADDYFILE="/home/alejandro/apps/paperclip/Caddyfile"
HOST="clip.aadigitalbusiness.com"

check(){
  PC=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:3100/api/health)
  LOCAL=$(curl -sk --resolve "$HOST:443:127.0.0.1" -o /dev/null -w '%{http_code}' "https://$HOST/api/health" 2>/dev/null || echo fail)
  PUB=$(curl -sk -o /dev/null -w '%{http_code}' "https://$HOST/api/health" 2>/dev/null || echo fail)
  echo "$PC|$LOCAL|$PUB"
}

RESULT=$(check)
IFS='|' read -r PC LOCAL PUB <<< "$RESULT"

if [ "$LOCAL" != "200" ]; then
  echo "Origen roto ($LOCAL) — restaurando tls internal..."
  if ! grep -q 'tls internal' "$CADDYFILE"; then
    sed -i "/^clip\.aadigitalbusiness\.com {/a\\\ttls internal" "$CADDYFILE"
  fi
  caddy reload --config /etc/caddy/Caddyfile --address 127.0.0.1:2019
  sleep 2
  RESULT=$(check)
  IFS='|' read -r PC LOCAL PUB <<< "$RESULT"
fi

echo "Estado: paperclip=$PC origen=$LOCAL público=$PUB"

if [ "$PUB" = "200" ]; then
  echo "OK: https://$HOST operativo"
  exit 0
fi

if [ -n "${CF_API_TOKEN:-}" ]; then
  echo "Instalando Cloudflare Origin CA..."
  bash "$(dirname "$0")/install-origin-ca.sh"
  exit $?
fi

if sudo -n true 2>/dev/null; then
  bash "$(dirname "$0")/enable-le.sh"
  exit $?
fi

echo ""
echo "502 confirmado: origen=$LOCAL público=$PUB"
echo "Solución permanente (Full strict):"
echo "  CF_API_TOKEN='token' bash $(dirname "$0")/install-origin-ca.sh"
echo "O con sudo:"
echo "  bash $(dirname "$0")/enable-le.sh"
exit 1
