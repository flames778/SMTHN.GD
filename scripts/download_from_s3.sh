#!/usr/bin/env bash
set -euo pipefail
# Wrapper around scripts/s3_assets.py to download assets from S3
if [ "$#" -lt 3 ]; then
  echo "Usage: $0 <bucket> <key-or-prefix> <out-dir> [--prefix-mode]"
  echo "If --prefix-mode is provided and set to 'prefix', the script treats second arg as prefix and downloads recursively."
  exit 2
fi
BUCKET="$1"
KEY="$2"
OUT="$3"
MODE="${4:-}"
if [ "$MODE" = "prefix" ]; then
  python3 scripts/s3_assets.py download --bucket "$BUCKET" --key-prefix "$KEY" --out-dir "$OUT" --recursive
else
  python3 scripts/s3_assets.py download --bucket "$BUCKET" --key "$KEY" --out-dir "$OUT"
fi
