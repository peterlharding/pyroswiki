#!/usr/bin/env bash
# Check what the running server's pub_base_url resolves to
# by fetching a rendered topic and checking the attachment URLs

API="https://pyroswiki.performiq.com:8443/api/v1"
TOKEN=$(curl -s -X POST "$API/auth/token" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=windsurf&password=Automation-2026' \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')

echo "=== Attachment links in rendered CFP/WebHome ==="
curl -s "$API/webs/CFP/topics/WebHome" \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -c '
import sys, json, re
data = json.load(sys.stdin)
rendered = data.get("rendered", "")
links = re.findall(r"href=\"([^\"]*(?:n\d{4}|\.pdf)[^\"]*?)\"", rendered)
for l in links[:3]:
    print(" ", l)
'

echo ""
echo "=== Does /pub route exist on web UI? ==="
curl -s -o /dev/null -w "GET /pub/CFP/WebHome/n3775.pdf → HTTP %{http_code}\n" \
  https://pyroswiki.performiq.com/pub/CFP/WebHome/n3775.pdf
