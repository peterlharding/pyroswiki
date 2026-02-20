#!/bin/sh
#
# ----------------------------------------------------------------------------

curl -s -X POST http://localhost:8621/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","email":"admin@example.com","password":"Testing-2026","display_name":"Admin"}' | python3 -m json.tool


