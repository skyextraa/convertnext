#!/usr/bin/env bash
set -euo pipefail

exec gunicorn --workers 1 --threads 2 --timeout 90 --graceful-timeout 20 --access-logfile - --error-logfile - app:app
