#!/usr/bin/env bash
# Verify migrated topics are accessible on pyroswiki

API="https://pyroswiki.performiq.com:8443/api/v1"

TOKEN=$(curl -s -X POST "$API/auth/token" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=windsurf&password=Automation-2026' \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')

echo "=== CFP web info ==="
curl -s "$API/webs/CFP" -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo ""
echo "=== Topics in CFP web ==="
curl -s "$API/webs/CFP/topics" -H "Authorization: Bearer $TOKEN" \
  | python3 -c 'import sys,json; topics=json.load(sys.stdin); print(f"Count: {len(topics)}"); [print(f"  - {t[\"name\"]}") for t in topics]'

echo ""
echo "=== Sample: CFP/PreviousMeetings (first 300 chars) ==="
curl -s "$API/webs/CFP/topics/PreviousMeetings" -H "Authorization: Bearer $TOKEN" \
  | python3 -c 'import sys,json; t=json.load(sys.stdin); print(t["content"][:300])'
