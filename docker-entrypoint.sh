#!/usr/bin/env sh
set -eu

mkdir -p /app/db /app/exports /app/wordlists
exec python3 /app/main.py "$@"
