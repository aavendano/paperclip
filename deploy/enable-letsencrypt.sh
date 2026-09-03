#!/usr/bin/env bash
# Obtener certificado Let's Encrypt para clip.aadigitalbusiness.com (requiere sudo).
# Tras ejecutar, Cloudflare SSL/TLS puede quedar en Full (strict).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CADDYFILE="/etc/caddy/Caddyfile"

if ! grep -q 'import /home/alejandro/apps/paperclip/Caddyfile' "$CADDYFILE"; then
  echo "Añade al final de $CADDYFILE:"
  echo "  import /home/alejandro/apps/paperclip/Caddyfile"
  exit 1
fi

# Quitar tls internal del Caddyfile de Paperclip
sed -i '/^clip\.aadigitalbusiness.com {/,/^}$/ s/^[[:space:]]*tls internal[[:space:]]*$//' "$ROOT/Caddyfile"

sudo caddy validate --config "$CADDYFILE"
sudo systemctl reload caddy

echo "Esperando certificado LE..."
for i in $(seq 1 12); do
  sleep 5
  if curl -sk --resolve clip.aadigitalbusiness.com:443:127.0.0.1 -o /dev/null -w '%{http_code}' \
    https://clip.aadigitalbusiness.com/api/health | grep -q 200; then
    echo "OK: HTTPS local responde 200"
    exit 0
  fi
  echo "  intento $i..."
done

echo "No se obtuvo certificado aún. Revisa: sudo journalctl -u caddy -n 50"
exit 1
