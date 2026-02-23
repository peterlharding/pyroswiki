#!/usr/bin/env bash
# Probe the source Foswiki instance to understand available webs and topics

SRC="https://cfp-foswiki.performiq.com"
CREDS="admin:floating"

echo "=== Raw text of Main/WebHome ==="
curl -s -u "$CREDS" "$SRC/Main/WebHome?raw=text" | head -40

echo ""
echo "=== List of webs via WebIndex ==="
curl -s -u "$CREDS" "$SRC/System/WebIndex?raw=text" | head -20

echo ""
echo "=== Topic list in Main web ==="
curl -s -u "$CREDS" "$SRC/Main/WebIndex?raw=text" | head -60

echo ""
echo "=== Topic list in CFP web (if exists) ==="
curl -s -u "$CREDS" "$SRC/CFP/WebIndex?raw=text" | head -60

echo ""
echo "=== Check what webs exist (via bin/view WebIndex) ==="
curl -s -u "$CREDS" "$SRC/bin/view/Main/SiteMap" \
  | grep -o 'href="/[A-Za-z][A-Za-z0-9]*/WebHome"' \
  | sed 's|href="/||;s|/WebHome"||' \
  | sort -u
