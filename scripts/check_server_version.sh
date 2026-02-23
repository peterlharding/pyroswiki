#!/usr/bin/env bash
# Check what version/code is running on the server

API="https://pyroswiki.performiq.com:8443/api/v1"

echo "=== API health/version ==="
curl -s "$API/../health" | python3 -m json.tool 2>/dev/null || \
curl -s "https://pyroswiki.performiq.com:8443/health" | python3 -m json.tool 2>/dev/null || \
echo "(no /health endpoint)"

echo ""
echo "=== OpenAPI routes (check for /raw endpoint) ==="
curl -s "https://pyroswiki.performiq.com:8443/openapi.json" \
  | python3 -c 'import sys,json; paths=json.load(sys.stdin)["paths"]; [print(p) for p in sorted(paths) if "raw" in p or "pub" in p]'

echo ""
echo "=== Try /raw endpoint directly ==="
TOKEN=$(curl -s -X POST "$API/auth/token" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=windsurf&password=Automation-2026' \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')

curl -s -w "\nHTTP %{http_code}" \
  "$API/webs/CFP/topics/WebHome/raw" \
  -H "Authorization: Bearer $TOKEN" | tail -5
