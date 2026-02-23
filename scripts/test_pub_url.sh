#!/usr/bin/env bash
echo "=== GET /pub/CFP/WebHome/n3775.pdf ==="
curl -s -o /dev/null -w "HTTP %{http_code} — %{content_type} — %{size_download} bytes\n" \
  https://pyroswiki.performiq.com/pub/CFP/WebHome/n3775.pdf

echo ""
echo "=== Rendered attachment links in CFP/WebHome (after restart) ==="
API="https://pyroswiki.performiq.com:8443/api/v1"
TOKEN=$(curl -s -X POST "$API/auth/token" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=windsurf&password=Automation-2026' \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')

curl -s "$API/webs/CFP/topics/WebHome" \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -c '
import sys, json, re
data = json.load(sys.stdin)
rendered = data.get("rendered", "")
links = re.findall(r"href=\"([^\"]*n\d{4}[^\"]*?)\"", rendered)
for l in links[:5]:
    print(" ", l)
'
