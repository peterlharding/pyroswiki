#!/usr/bin/env bash
# Check if rendered cache has been cleared for CFP topics

API="https://pyroswiki.performiq.com:8443/api/v1"
TOKEN=$(curl -s -X POST "$API/auth/token" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=windsurf&password=Automation-2026' \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')

echo "=== Force re-render by fetching with render=true (no cache) ==="
curl -s "$API/webs/CFP/topics/WebHome?render=true" \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -c '
import sys, json, re
data = json.load(sys.stdin)
rendered = data.get("rendered", "")
links = re.findall(r"href=\"([^\"]*n\d{4}[^\"]*?)\"", rendered)
print("First 3 attachment links:")
for l in links[:3]:
    print(" ", l)
'
