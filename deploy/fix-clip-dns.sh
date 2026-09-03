#!/usr/bin/env bash
# Corrige DNS de clip en Cloudflare → IP pública del origen (2.28.46.34).
# Requiere token con Zone > DNS > Edit
set -euo pipefail

ZONE_NAME="aadigitalbusiness.com"
HOST="clip.aadigitalbusiness.com"
ORIGIN_IP="2.28.46.34"

if [ -f /home/alejandro/.paperclip/cf-api-token.env ]; then
  # shellcheck source=/dev/null
  source /home/alejandro/.paperclip/cf-api-token.env
fi

if [ -z "${CF_API_TOKEN:-}" ]; then
  echo "ERROR: CF_API_TOKEN requerido (permiso Zone > DNS > Edit)"
  exit 1
fi

ZONE_ID=$(curl -sf -H "Authorization: Bearer $CF_API_TOKEN" \
  "https://api.cloudflare.com/client/v4/zones?name=$ZONE_NAME" \
  | python3 -c "import sys,json; r=json.load(sys.stdin); print(r['result'][0]['id'])")

RECORDS=$(curl -s -H "Authorization: Bearer $CF_API_TOKEN" \
  "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records?name=$HOST")
echo "$RECORDS" | python3 -m json.tool | head -40

python3 - <<PY
import json, os, urllib.request
token = os.environ["CF_API_TOKEN"]
zone_id = "$ZONE_ID"
host = "$HOST"
origin_ip = "$ORIGIN_IP"
records = json.loads('''$(echo "$RECORDS" | python3 -c "import sys,json; print(json.dumps(json.load(sys.stdin)))")''')
if not records.get("success"):
    raise SystemExit("DNS API error: " + json.dumps(records.get("errors")))
items = records.get("result") or []
if not items:
    body = json.dumps({"type":"A","name":host,"content":origin_ip,"proxied":True,"ttl":1}).encode()
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
    method = "POST"
else:
    rid = items[0]["id"]
    body = json.dumps({"type":"A","name":host,"content":origin_ip,"proxied":True,"ttl":1}).encode()
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{rid}"
    method = "PUT"
req = urllib.request.Request(url, data=body, headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}, method=method)
with urllib.request.urlopen(req) as resp:
    out = json.load(resp)
print(json.dumps(out, indent=2))
if not out.get("success"):
    raise SystemExit(1)
print(f"OK: {host} -> {origin_ip} (proxied)")
PY

sleep 5
PUB=$(curl -sk -o /dev/null -w '%{http_code}' "https://$HOST/api/health" 2>/dev/null || echo fail)
echo "public=$PUB"
[ "$PUB" = "200" ] && exit 0
exit 1
