#!/bin/sh
#
#

TOKEN=$(curl -s -X POST http://localhost:8621/api/v1/auth/token \
  -d "username=admin&password=Testing-2026" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

echo "TOKEN |${TOKEN}|"


