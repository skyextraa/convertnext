#!/usr/bin/env bash
set -euo pipefail

PROVIDER="/opt/bgutil-ytdlp-pot-provider/server/build/main.js"
LOG="/tmp/bgutil-pot-provider.log"

if [ ! -f "$PROVIDER" ]; then
  echo "bgutil provider was not built: $PROVIDER" >&2
  exit 1
fi

node "$PROVIDER" --port 4416 >"$LOG" 2>&1 &
PROVIDER_PID=$!

cleanup() {
  kill "$PROVIDER_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

for _ in $(seq 1 60); do
  if curl -fsS http://127.0.0.1:4416/ping >/dev/null 2>&1; then
    echo "bgutil provider ready on 127.0.0.1:4416"
    exec gunicorn --bind 0.0.0.0:${PORT:-8000} --workers 1 --threads 2 --timeout 180 app:app
  fi
  if ! kill -0 "$PROVIDER_PID" 2>/dev/null; then
    echo "bgutil provider exited before becoming ready" >&2
    cat "$LOG" >&2 || true
    exit 1
  fi
  sleep 0.5
done

echo "bgutil provider did not become ready" >&2
cat "$LOG" >&2 || true
exit 1
