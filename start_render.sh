#!/usr/bin/env bash
set -euo pipefail

export BGUTIL_SERVER_HOME=/opt/bgutil-ytdlp-pot-provider/server
export CONVERTNEST_DISABLE_LOCAL_POT=1
export YTDL_POT_PROVIDER_URL=http://127.0.0.1:4416
export CONVERTNEST_USE_POT_HTTP=1

PROVIDER_LOG=/tmp/bgutil-pot-provider.log
PROVIDER=/opt/bgutil-ytdlp-pot-provider/server/build/main.js

if [ ! -f "$PROVIDER" ]; then
  echo "ERROR: bgutil provider was not built at $PROVIDER" >&2
  exit 1
fi

node "$PROVIDER" --port 4416 >"$PROVIDER_LOG" 2>&1 &
PROVIDER_PID=$!

cleanup() {
  kill "$PROVIDER_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

READY=0
for _ in $(seq 1 40); do
  if curl -fsS http://127.0.0.1:4416/ping >/dev/null 2>&1; then
    READY=1
    break
  fi
  if ! kill -0 "$PROVIDER_PID" 2>/dev/null; then
    break
  fi
  sleep 0.25
done

if [ "$READY" -ne 1 ]; then
  echo "ERROR: bgutil provider did not become ready." >&2
  cat "$PROVIDER_LOG" >&2 || true
  exit 1
fi

echo "bgutil PO-token provider is ready on 127.0.0.1:4416"
exec gunicorn --workers 1 --threads 2 --timeout 120 app:app
