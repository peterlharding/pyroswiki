#!/usr/bin/env bash
# Check what %PUBURL% expands to by rendering a test topic

API="https://pyroswiki.performiq.com:8443/api/v1"
TOKEN=$(curl -s -X POST "$API/auth/token" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=windsurf&password=Automation-2026' \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')

echo "=== Create a test topic with %PUBURL% macro ==="
curl -s -X POST "$API/webs/CFP/topics" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"PubUrlTest","content":"PUBURL expands to: %PUBURL%\n\nATTACHURL expands to: %ATTACHURL%"}' \
  | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("message","ok"))'

echo ""
echo "=== Fetch rendered PubUrlTest ==="
curl -s "$API/webs/CFP/topics/PubUrlTest" \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("rendered","no rendered field"))'

echo ""
echo "=== Cleanup: delete test topic ==="
curl -s -X DELETE "$API/webs/CFP/topics/PubUrlTest" \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -c 'import sys,json; print(json.load(sys.stdin).get("message","done"))'
