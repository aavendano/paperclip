#!/usr/bin/env bash
# Instala certificado Cloudflare Origin CA para clip (compatible con Full strict).
# Uso: CF_API_TOKEN='tu-token' bash deploy/install-origin-ca.sh
set -euo pipefail

HOST="clip.aadigitalbusiness.com"
ZONE_NAME="aadigitalbusiness.com"
CADDYFILE="/home/alejandro/apps/paperclip/Caddyfile"
CERT_DIR="/home/alejandro/apps/paperclip/certs"

if [ -z "${CF_API_TOKEN:-}" ]; then
  if [ -f /home/alejandro/.paperclip/cf-api-token.env ]; then
    # shellcheck source=/dev/null
    source /home/alejandro/.paperclip/cf-api-token.env
  fi
fi

if [ -z "${CF_API_TOKEN:-}" ]; then
  echo "ERROR: exporta CF_API_TOKEN (permiso Zone > SSL and Certificates > Edit)"
  echo "Crea el token en: https://dash.cloudflare.com/profile/api-tokens"
  exit 1
fi

mkdir -p "$CERT_DIR"
chmod 755 "$CERT_DIR"

echo "Obteniendo zone_id para $ZONE_NAME..."
ZONE_ID=$(curl -sf -H "Authorization: Bearer $CF_API_TOKEN" \
  "https://api.cloudflare.com/client/v4/zones?name=$ZONE_NAME" \
  | python3 -c "import sys,json; r=json.load(sys.stdin); print(r['result'][0]['id'] if r.get('success') and r['result'] else '')")

if [ -z "$ZONE_ID" ]; then
  echo "ERROR: no se encontró zone_id. Verifica CF_API_TOKEN."
  exit 1
fi

echo "Creando Origin CA para $HOST..."
openssl req -new -newkey rsa:2048 -nodes \
  -keyout "$CERT_DIR/origin-key.pem" \
  -out "$CERT_DIR/origin.csr" \
  -subj "/CN=$HOST" 2>/dev/null
chmod 600 "$CERT_DIR/origin-key.pem"
CSR_JSON=$(python3 -c "import json, pathlib; print(json.dumps(pathlib.Path('$CERT_DIR/origin.csr').read_text()))")

HTTP_CODE=$(curl -s -w '%{http_code}' -o "$CERT_DIR/origin-ca-response.json" -X POST \
  "https://api.cloudflare.com/client/v4/certificates?zone_id=$ZONE_ID" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"csr\":$CSR_JSON,\"hostnames\":[\"$HOST\"],\"requested_validity\":5475,\"request_type\":\"origin-rsa\"}")

if [ "$HTTP_CODE" != "200" ] || [ ! -s "$CERT_DIR/origin-ca-response.json" ]; then
  echo "ERROR: API Origin CA falló (HTTP $HTTP_CODE)"
  cat "$CERT_DIR/origin-ca-response.json" 2>/dev/null | python3 -m json.tool 2>/dev/null || true
  exit 1
fi

python3 - <<PY
import json, os, stat, pathlib, urllib.request
cert_dir = pathlib.Path("$CERT_DIR")
with open(cert_dir / "origin-ca-response.json") as f:
    data = json.load(f)
if not data.get("success"):
    raise SystemExit("API error: " + json.dumps(data.get("errors", data)))
cert = data["result"]["certificate"]
(cert_dir / "origin.pem").write_text(cert)
# Cadena completa para compatibilidad TLS
try:
    root = urllib.request.urlopen("https://developers.cloudflare.com/ssl/static/origin_ca_rsa_root.pem").read().decode()
    (cert_dir / "origin.pem").write_text(cert + root)
except OSError:
    pass
(cert_dir / "origin-key.pem").chmod(stat.S_IRUSR | stat.S_IWUSR)
(cert_dir / "origin.pem").chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
print("Certificados guardados en", cert_dir)
PY
rm -f "$CERT_DIR/origin-ca-response.json" "$CERT_DIR/origin.csr"

# Caddy (usuario caddy) debe poder leer certs fuera de $HOME
chmod o+x /home/alejandro
chmod 644 "$CERT_DIR/origin.pem" "$CERT_DIR/origin-key.pem"

python3 - <<PY
from pathlib import Path
import re
cert_dir = "$CERT_DIR"
p = Path("$CADDYFILE")
text = p.read_text()
block = f'''clip.aadigitalbusiness.com {{
\ttls {cert_dir}/origin.pem {cert_dir}/origin-key.pem

\tencode zstd gzip

\treverse_proxy 127.0.0.1:3100 {{
\t\theader_up Host {{host}}
\t\theader_up X-Real-IP {{remote_host}}
\t\theader_up X-Forwarded-Proto {{scheme}}
\t\theader_up X-Forwarded-For {{remote_host}}
\t}}
}}
'''
p.write_text(re.sub(r'clip\.aadigitalbusiness\.com \{.*?\n\}', block, text, count=1, flags=re.S))
print("Caddyfile actualizado")
PY

caddy validate --config /etc/caddy/Caddyfile
caddy reload --config /etc/caddy/Caddyfile --address 127.0.0.1:2019

echo "Esperando HTTPS..."
for i in $(seq 1 12); do
  sleep 3
  LOCAL=$(curl -sk --resolve "$HOST:443:127.0.0.1" -o /dev/null -w '%{http_code}' "https://$HOST/api/health" 2>/dev/null || echo fail)
  PUB=$(curl -sk -o /dev/null -w '%{http_code}' "https://$HOST/api/health" 2>/dev/null || echo fail)
  echo "  $i: local=$LOCAL public=$PUB"
  [ "$PUB" = "200" ] && echo "OK: https://$HOST operativo con Origin CA" && exit 0
done

echo "Origin CA instalado pero público aún no responde 200. Revisa DNS (A → IP pública) y SSL mode."
exit 1
