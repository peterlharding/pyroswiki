#!/usr/bin/env bash
# Check what environment the running pyroswiki-api process actually sees

echo "=== Environment of running pyroswiki-api process ==="
PID=$(pgrep -f "uvicorn.*app.main" | head -1)
if [ -n "$PID" ]; then
  echo "PID: $PID"
  cat /proc/$PID/environ | tr '\0' '\n' | grep -E "BASE_URL|WEB_BASE|SITE|APP_NAME" | sort
else
  echo "Process not found via pgrep, trying systemctl..."
  systemctl show pyroswiki-api --property=MainPID | head -1
fi
