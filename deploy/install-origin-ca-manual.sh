#!/usr/bin/env bash
# Instala certificado Origin CA creado manualmente en el panel Cloudflare.
# 1. Dashboard → SSL/TLS → Origin Server → Create Certificate
#    Hostname: clip.aadigitalbusiness.com
# 2. Guarda certificado y clave en:
#      /home/alejandro/apps/paperclip/certs/origin.pem
#      /home/alejandro/apps/paperclip/certs/origin-key.pem
# 3. bash deploy/install-origin-ca-manual.sh
set -euo pipefail

HOST="clip.aadigitalbusiness.com"
CADDYFILE="/home/alejandro/apps/paperclip/Caddyfile"
CERT_DIR="/home/alejandro/apps/paperclip/certs"

CERT="$CERT_DIR/origin.pem"
KEY="$CERT_DIR/origin-key.pem"

if [ ! -s "$CERT" ] || [ ! -s "$KEY" ]; then
  echo "Faltan certificados. Crea Origin CA en:"
  echo "  https://dash.cloudflare.com/?to=/:account/:zone/ssl-tls/origin"
  echo ""
  echo "Hostname: $HOST"
  echo "Guarda como:"
  echo "  $CERT"
  echo "  $KEY"
  exit 1
fi

chmod o+x /home/alejandro
chmod 755 "$CERT_DIR"
chmod 600 "$KEY"
chmod 644 "$CERT"

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
print("Caddyfile actualizado con Origin CA")
PY

caddy validate --config /etc/caddy/Caddyfile
caddy reload --config /etc/caddy/Caddyfile --address 127.0.0.1:2019

sleep 2
LOCAL=$(curl -sk --resolve "$HOST:443:127.0.0.1" -o /dev/null -w '%{http_code}' "https://$HOST/api/health" 2>/dev/null || echo fail)
PUB=$(curl -sk -o /dev/null -w '%{http_code}' "https://$HOST/api/health" 2>/dev/null || echo fail)

echo "origen=$LOCAL público=$PUB"
[ "$PUB" = "200" ] && echo "OK: https://$HOST operativo" && exit 0
echo "Si público sigue 502, verifica DNS (A → IP pública del servidor)."
exit 1
