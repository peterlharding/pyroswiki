#!/usr/bin/env bash
TOKEN=$(curl -s -X POST https://pyroswiki.performiq.com:8443/api/v1/auth/token \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=windsurf&password=Automation-2026' \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')

echo "Token: ${TOKEN:0:30}..."

curl -s https://pyroswiki.performiq.com:8443/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
