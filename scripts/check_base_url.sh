#!/usr/bin/env bash
# Check what BASE_URL the running server is using
echo "=== Server settings via API ==="
curl -s https://pyroswiki.performiq.com:8443/api/v1/admin/settings \
  -H "Authorization: Bearer $(curl -s -X POST https://pyroswiki.performiq.com:8443/api/v1/auth/token \
    -H 'Content-Type: application/x-www-form-urlencoded' \
    -d 'username=windsurf&password=Automation-2026' \
    | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')" \
  | python3 -c 'import sys,json; d=json.load(sys.stdin); [print(f"  {k}: {v}") for k,v in d.items() if "url" in k.lower()]'
