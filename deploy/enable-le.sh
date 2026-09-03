#!/usr/bin/env bash
# Ejecutar en el servidor con sudo (una sola vez).
# Obtiene certificado Let's Encrypt y deja clip.aadigitalbusiness.com operativo con Cloudflare Full (strict).
set -euo pipefail

CADDYFILE="/home/alejandro/apps/paperclip/Caddyfile"

# Solo quitar tls internal si sudo está disponible (evita dejar origen sin cert)
if ! sudo -n true 2>/dev/null; then
  echo "ERROR: se requiere sudo para reload de Caddy."
  echo "Ejecuta: sudo bash $0"
  echo "O usa: CF_API_TOKEN='...' bash $(dirname "$0")/install-origin-ca.sh"
  exit 1
fi

sed -i '/tls internal/d' "$CADDYFILE"

sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy

echo "Esperando certificado LE..."
for i in $(seq 1 18); do
  sleep 5
  LOCAL=$(curl -sk --resolve clip.aadigitalbusiness.com:443:127.0.0.1 -o /dev/null -w '%{http_code}' \
    https://clip.aadigitalbusiness.com/api/health 2>/dev/null || echo fail)
  PUB=$(curl -sk -o /dev/null -w '%{http_code}' https://clip.aadigitalbusiness.com/api/health 2>/dev/null || echo fail)
  ISSUER=$(curl -vsk --resolve clip.aadigitalbusiness.com:443:127.0.0.1 \
    https://clip.aadigitalbusiness.com/api/health 2>&1 | grep issuer | tail -1 || true)
  echo "  $i: local=$LOCAL public=$PUB | $ISSUER"
  [ "$PUB" = "200" ] && echo "OK: https://clip.aadigitalbusiness.com operativo" && exit 0
done

echo "Falló. Revisa: sudo journalctl -u caddy -n 50"
exit 1
