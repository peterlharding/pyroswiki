#!/bin/sh
#
# -----------------------------------------------------------------------------

set -x

curl -s "http://localhost:8621/api/v1/search?q=Welcome" | python3 -m json.tool


