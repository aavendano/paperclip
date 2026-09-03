#!/usr/bin/env bash
# Recarga Caddy para que obtenga Let's Encrypt (igual que cms/nalpac).
set -euo pipefail
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
echo "Esperando certificado LE..."
for i in $(seq 1 12); do
  sleep 5
  code=$(curl -sk --resolve clip.aadigitalbusiness.com:443:127.0.0.1 -o /dev/null -w '%{http_code}' \
    https://clip.aadigitalbusiness.com/api/health 2>/dev/null || true)
  pub=$(curl -sk -o /dev/null -w '%{http_code}' https://clip.aadigitalbusiness.com/api/health 2>/dev/null || true)
  echo "  intento $i: origin=$code public=$pub"
  [ "$pub" = "200" ] && echo "OK" && exit 0
done
echo "Revisa: sudo journalctl -u caddy -n 50"
exit 1
