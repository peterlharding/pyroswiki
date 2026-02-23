#!/usr/bin/env bash
API="https://pyroswiki.performiq.com:8443/api/v1"
TOKEN=$(curl -s -X POST "$API/auth/token" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=windsurf&password=Automation-2026' \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')

echo "=== Raw content of CFP/WebHome (first 20 lines) ==="
curl -s "$API/webs/CFP/topics/WebHome/raw" \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -c '
import sys,json
d=json.load(sys.stdin)
for i,l in enumerate(d["content"].splitlines()[:20]):
    print(f"{i+1:3}: {l}")
'

echo ""
echo "=== Rendered CFP/WebHome (first 300 chars of HTML) ==="
curl -s "$API/webs/CFP/topics/WebHome" \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -c '
import sys,json
d=json.load(sys.stdin)
print(d.get("rendered","")[:500])
'
