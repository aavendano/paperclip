#!/usr/bin/env bash
# Corrige 502 en clip.aadigitalbusiness.com
set -euo pipefail

# Paso A: reload Caddy (ACME nativo, igual que cms/nalpac)
if sudo systemctl reload caddy 2>/dev/null; then
  sleep 25
  LOCAL=$(curl -sk --resolve clip.aadigitalbusiness.com:443:127.0.0.1 -o /dev/null -w '%{http_code}' https://clip.aadigitalbusiness.com/api/health 2>/dev/null || echo fail)
  PUB=$(curl -sk -o /dev/null -w '%{http_code}' https://clip.aadigitalbusiness.com/api/health 2>/dev/null || echo fail)
  ISSUER=$(curl -vsk --resolve clip.aadigitalbusiness.com:443:127.0.0.1 https://clip.aadigitalbusiness.com/api/health 2>&1 | grep issuer | tail -1 | tr '"' "'")
  if [ "$PUB" = "200" ]; then echo "OK: LE activo, público 200"; exit 0; fi
  if echo "$ISSUER" | grep -q "Let's Encrypt"; then
    echo "Cert LE obtenido pero público=$PUB — revisa Cloudflare SSL (debe ser Full strict)."
    exit 0
  fi
fi

# Paso B: reload vía admin API (tls internal en Caddyfile)
caddy reload --config /etc/caddy/Caddyfile --address 127.0.0.1:2019 >/dev/null 2>&1 || true
sleep 3
LOCAL=$(curl -sk --resolve clip.aadigitalbusiness.com:443:127.0.0.1 -o /dev/null -w '%{http_code}' https://clip.aadigitalbusiness.com/api/health 2>/dev/null || echo fail)
PUB=$(curl -sk -o /dev/null -w '%{http_code}' https://clip.aadigitalbusiness.com/api/health 2>/dev/null || echo fail)

echo "Origen (local): $LOCAL | Público (Cloudflare): $PUB"

if [ "$LOCAL" != "200" ]; then
  echo "ERROR: origen roto — revisa paperclip.service"
  exit 1
fi

if [ "$PUB" = "200" ]; then
  echo "OK: sitio público responde 200"
  exit 0
fi

echo ""
echo "Origen OK pero Cloudflare devuelve $PUB."
echo "Cloudflare → SSL/TLS → Overview → cambia a **Full** (no Full strict)."
echo "Luego recarga https://clip.aadigitalbusiness.com"
echo ""
echo "Para certificado Let's Encrypt permanente (Full strict):"
echo "  1. Cloudflare → SSL/TLS → desactiva 'Always Use HTTPS'"
echo "  2. sudo systemctl reload caddy"
echo "  3. Reactiva 'Always Use HTTPS'"
exit 1
