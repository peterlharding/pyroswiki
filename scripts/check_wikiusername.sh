#!/usr/bin/env bash
API="https://pyroswiki.performiq.com:8443/api/v1"
TOKEN=$(curl -s -X POST "$API/auth/token" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=windsurf&password=Automation-2026' \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')

echo "=== Test WIKIUSERNAME and bold rendering ==="
curl -s -X POST "$API/webs/CFP/topics" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"MacroTest","content":"WIKIUSERNAME: %WIKIUSERNAME%\n\n*bold text* and _italic text_"}' \
  > /dev/null

curl -s "$API/webs/CFP/topics/MacroTest" \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("rendered",""))'

curl -s -X DELETE "$API/webs/CFP/topics/MacroTest" \
  -H "Authorization: Bearer $TOKEN" > /dev/null
