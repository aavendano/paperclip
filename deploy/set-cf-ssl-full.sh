#!/usr/bin/env bash
# Fix rápido 502: cambia Cloudflare SSL a Full (acepta cert autofirmado del origen).
# Requiere token con Zone > SSL and Certificates > Edit
# Uso: CF_API_TOKEN='...' bash deploy/set-cf-ssl-full.sh
set -euo pipefail

ZONE_NAME="aadigitalbusiness.com"
HOST="clip.aadigitalbusiness.com"

if [ -z "${CF_API_TOKEN:-}" ]; then
  if [ -f /home/alejandro/.paperclip/cf-api-token.env ]; then
    # shellcheck source=/dev/null
    source /home/alejandro/.paperclip/cf-api-token.env
  fi
fi

if [ -z "${CF_API_TOKEN:-}" ]; then
  echo "ERROR: exporta CF_API_TOKEN"
  exit 1
fi

ZONE_ID=$(curl -sf -H "Authorization: Bearer $CF_API_TOKEN" \
  "https://api.cloudflare.com/client/v4/zones?name=$ZONE_NAME" \
  | python3 -c "import sys,json; r=json.load(sys.stdin); print(r['result'][0]['id'] if r.get('success') and r['result'] else '')")

if [ -z "$ZONE_ID" ]; then
  echo "ERROR: token inválido o sin acceso a $ZONE_NAME"
  exit 1
fi

echo "Cambiando SSL mode a Full para zone $ZONE_ID..."
RESP=$(curl -s -X PATCH "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/settings/ssl" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"value":"full"}')

OK=$(echo "$RESP" | python3 -c "import sys,json; r=json.load(sys.stdin); print('yes' if r.get('success') else 'no')")
if [ "$OK" != "yes" ]; then
  echo "ERROR al cambiar SSL mode:"
  echo "$RESP" | python3 -m json.tool
  exit 1
fi

echo "SSL mode = Full. Verificando..."
sleep 3
PUB=$(curl -sk -o /dev/null -w '%{http_code}' "https://$HOST/api/health" 2>/dev/null || echo fail)
LOCAL=$(curl -sk --resolve "$HOST:443:127.0.0.1" -o /dev/null -w '%{http_code}' "https://$HOST/api/health" 2>/dev/null || echo fail)

echo "origen=$LOCAL público=$PUB"
[ "$PUB" = "200" ] && echo "OK: https://$HOST operativo" && exit 0
echo "Aún no 200 — espera 30s y recarga. Si persiste, ejecuta install-origin-ca.sh para Full strict."
exit 1
