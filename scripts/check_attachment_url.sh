#!/usr/bin/env bash
# Check how attachments are served on pyroswiki

API="https://pyroswiki.performiq.com:8443/api/v1"
WEB="https://pyroswiki.performiq.com"

TOKEN=$(curl -s -X POST "$API/auth/token" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=windsurf&password=Automation-2026' \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')

echo "=== List attachments on CFP/WebHome ==="
curl -s "$API/webs/CFP/topics/WebHome/attachments" \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -c 'import sys,json; atts=json.load(sys.stdin); print(f"Count: {len(atts)}"); [print(f"  {a[\"filename\"]} -> {a.get(\"url\",\"no url\")}") for a in atts[:5]]'

echo ""
echo "=== Try fetching n3775.pdf directly ==="
curl -s -o /dev/null -w "%{http_code} %{url_effective}\n" \
  "$API/webs/CFP/topics/WebHome/attachments/n3775.pdf" \
  -H "Authorization: Bearer $TOKEN"

echo ""
echo "=== Try pub path ==="
curl -s -o /dev/null -w "%{http_code}\n" \
  "$WEB/pub/CFP/WebHome/n3775.pdf"
