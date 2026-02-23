#!/usr/bin/env bash
# Probe CFP Foswiki - discover webs and topics

SRC="https://cfp-foswiki.performiq.com"
COOKIEJAR="/tmp/cfp_cookies.txt"

# Reuse existing cookie
echo "=== WebTopicList in Main (plain text) ==="
curl -s -c "$COOKIEJAR" -b "$COOKIEJAR" \
  "$SRC/bin/view/Main/WebTopicList?skin=text&contenttype=text/plain" | head -80

echo ""
echo "=== WebChanges to see all webs ==="
curl -s -c "$COOKIEJAR" -b "$COOKIEJAR" \
  "$SRC/bin/view/Main/WebChanges?skin=text" | head -30

echo ""
echo "=== Try fetching the Foswiki web list via configure ==="
curl -s -c "$COOKIEJAR" -b "$COOKIEJAR" \
  "$SRC/bin/view/System/SiteMap?skin=text" | head -60

echo ""
echo "=== Try raw WebTopicList ==="
curl -s -c "$COOKIEJAR" -b "$COOKIEJAR" \
  "$SRC/bin/view/Main/WebTopicList?raw=text" | head -80

echo ""
echo "=== Try CFP web directly ==="
curl -s -c "$COOKIEJAR" -b "$COOKIEJAR" \
  "$SRC/bin/view/CFP/WebHome?raw=text" | head -20

echo ""
echo "=== Try Foswiki web directly ==="
curl -s -c "$COOKIEJAR" -b "$COOKIEJAR" \
  "$SRC/bin/view/Foswiki/WebHome?raw=text" | head -10

echo ""
echo "=== Try TWiki web ==="
curl -s -c "$COOKIEJAR" -b "$COOKIEJAR" \
  "$SRC/bin/view/TWiki/WebHome?raw=text" | head -10

echo ""
echo "=== Check all links on Main/WebIndex ==="
curl -s -c "$COOKIEJAR" -b "$COOKIEJAR" \
  "$SRC/bin/view/Main/WebIndex" \
  | grep -o 'href="/bin/view/[^"]*"' | sort -u | head -40
