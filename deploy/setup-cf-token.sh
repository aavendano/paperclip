#!/usr/bin/env bash
# Guía y validación del token Cloudflare para Origin CA (clip.aadigitalbusiness.com).
set -euo pipefail

TOKEN_FILE="/home/alejandro/.paperclip/cf-api-token.env"
ZONE_NAME="aadigitalbusiness.com"
HOST="clip.aadigitalbusiness.com"

echo "=============================================="
echo " Token Cloudflare para Origin CA (clip 502)"
echo "=============================================="
echo ""
echo "No se puede generar automáticamente — créalo en:"
echo "  https://dash.cloudflare.com/profile/api-tokens"
echo ""
echo "Pasos:"
echo "  1. Create Token → Create Custom Token"
echo "  2. Token name: paperclip-origin-ca"
echo "  3. Permissions:"
echo "       Zone → SSL and Certificates → Edit"
echo "  4. Zone Resources:"
echo "       Include → Specific zone → $ZONE_NAME"
echo "  5. Create Token → copia el valor (solo se muestra una vez)"
echo ""

if [ -n "${CF_API_TOKEN:-}" ]; then
  TOKEN="$CF_API_TOKEN"
elif [ -f "$TOKEN_FILE" ]; then
  # shellcheck source=/dev/null
  source "$TOKEN_FILE"
  TOKEN="${CF_API_TOKEN:-}"
else
  read -rsp "Pega el token aquí (no se mostrará): " TOKEN
  echo ""
fi

if [ -z "${TOKEN:-}" ]; then
  echo "ERROR: token vacío."
  exit 1
fi

echo "Validando token..."
RESP=$(curl -sf -H "Authorization: Bearer $TOKEN" \
  "https://api.cloudflare.com/client/v4/zones?name=$ZONE_NAME")

OK=$(echo "$RESP" | python3 -c "import sys,json; r=json.load(sys.stdin); print('yes' if r.get('success') and r['result'] else 'no')")
if [ "$OK" != "yes" ]; then
  echo "ERROR: token inválido o sin acceso a $ZONE_NAME"
  echo "$RESP" | python3 -m json.tool 2>/dev/null || echo "$RESP"
  exit 1
fi

ZONE_ID=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['result'][0]['id'])")
echo "OK: token válido para $ZONE_NAME (zone_id=$ZONE_ID)"

mkdir -p "$(dirname "$TOKEN_FILE")"
chmod 700 "$(dirname "$TOKEN_FILE")"
printf 'CF_API_TOKEN=%s\n' "$TOKEN" > "$TOKEN_FILE"
chmod 600 "$TOKEN_FILE"
echo "Token guardado en $TOKEN_FILE (chmod 600)"

echo ""
echo "Paso 1: cambiar SSL a Full (fix inmediato 502)..."
export CF_API_TOKEN="$TOKEN"
if bash "$(dirname "$0")/set-cf-ssl-full.sh"; then
  exit 0
fi

echo ""
echo "Paso 2: instalar Origin CA (Full strict permanente)..."
bash "$(dirname "$0")/install-origin-ca.sh"
