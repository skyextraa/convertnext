#!/usr/bin/env bash
set -e
exec gunicorn --workers 1 --threads 2 --timeout 120 --bind 0.0.0.0:${PORT:-10000} app:app
