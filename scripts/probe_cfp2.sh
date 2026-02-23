#!/usr/bin/env bash
# Probe CFP Foswiki using session cookie auth

SRC="https://cfp-foswiki.performiq.com"
COOKIEJAR="/tmp/cfp_cookies.txt"

echo "=== Step 1: Login and get session cookie ==="
curl -s -c "$COOKIEJAR" -b "$COOKIEJAR" \
  -X POST "$SRC/bin/login" \
  -d "username=admin&password=floating&foswiki_redirect_cache=" \
  -L -o /dev/null -w "HTTP %{http_code}\n"

echo ""
echo "=== Cookies obtained ==="
cat "$COOKIEJAR"

echo ""
echo "=== Step 2: Fetch Main/WebHome raw ==="
curl -s -c "$COOKIEJAR" -b "$COOKIEJAR" \
  "$SRC/bin/view/Main/WebHome?raw=text&skin=text" | head -30

echo ""
echo "=== Step 3: List topics in Main web ==="
curl -s -c "$COOKIEJAR" -b "$COOKIEJAR" \
  "$SRC/bin/view/Main/WebIndex?skin=text" \
  | grep -o 'href="/bin/view/Main/[^"]*"' \
  | sed 's|href="/bin/view/Main/||;s|"||' \
  | sort -u | head -60

echo ""
echo "=== Step 4: Check what webs exist ==="
curl -s -c "$COOKIEJAR" -b "$COOKIEJAR" \
  "$SRC/bin/view/Main/SiteMap?skin=text" \
  | grep -o '/bin/view/[A-Za-z][A-Za-z0-9]*/WebHome' \
  | sed 's|/bin/view/||;s|/WebHome||' \
  | sort -u
