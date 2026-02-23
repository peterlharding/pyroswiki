#!/usr/bin/env bash
# List all attachments under CFP/WebHome on the source Foswiki

SRC="https://cfp-foswiki.performiq.com"
COOKIEJAR="/tmp/cfp_cookies.txt"

echo "=== Attachments on CFP/WebHome ==="
curl -s -c "$COOKIEJAR" -b "$COOKIEJAR" \
  "$SRC/bin/view/CFP/WebHome" \
  | grep -o 'href="/pub/CFP/WebHome/[^"]*"' \
  | sed 's|href="||;s|"||' \
  | sort -u

echo ""
echo "=== Attachments on CFP/PreviousMeetings ==="
curl -s -c "$COOKIEJAR" -b "$COOKIEJAR" \
  "$SRC/bin/view/CFP/PreviousMeetings" \
  | grep -o 'href="/pub/CFP/[^"]*"' \
  | sed 's|href="||;s|"||' \
  | sort -u
