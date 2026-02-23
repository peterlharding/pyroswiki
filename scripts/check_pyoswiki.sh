#!/usr/bin/env bash
# Check if 'pyoswiki' appears in any migrated topic content

API="https://pyroswiki.performiq.com:8443/api/v1"

TOKEN=$(curl -s -X POST "$API/auth/token" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=windsurf&password=Automation-2026' \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')

echo "=== Checking raw content of CFP/WebHome for 'pyoswiki' ==="
curl -s "$API/webs/CFP/topics/WebHome/raw" \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -c 'import sys,json; c=json.load(sys.stdin)["content"]; print("FOUND" if "pyoswiki" in c else "NOT FOUND"); [print(f"  line {i+1}: {l}") for i,l in enumerate(c.splitlines()) if "pyoswiki" in l.lower()]'

echo ""
echo "=== Checking raw content of CFP/PreviousMeetings for 'pyoswiki' ==="
curl -s "$API/webs/CFP/topics/PreviousMeetings/raw" \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -c 'import sys,json; c=json.load(sys.stdin)["content"]; print("FOUND" if "pyoswiki" in c else "NOT FOUND"); [print(f"  line {i+1}: {l}") for i,l in enumerate(c.splitlines()) if "pyoswiki" in l.lower()]'

echo ""
echo "=== Check rendered CFP/WebHome for 'pyoswiki' ==="
curl -s "$API/webs/CFP/topics/WebHome" \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -c 'import sys,json; c=json.load(sys.stdin).get("rendered",""); print("FOUND in rendered" if "pyoswiki" in c else "NOT FOUND in rendered")'

echo ""
echo "=== First 5 attachment links in rendered CFP/WebHome ==="
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
