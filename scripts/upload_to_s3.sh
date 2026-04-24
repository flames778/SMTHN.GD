#!/usr/bin/env bash
set -euo pipefail
# Wrapper around scripts/s3_assets.py to upload assets to S3
if [ "$#" -lt 2 ]; then
  echo "Usage: $0 <bucket> <local-path> [key-prefix]"
  exit 2
fi
BUCKET="$1"
LOCAL="$2"
PREFIX="${3:-}" 
python3 scripts/s3_assets.py upload --bucket "$BUCKET" --key-prefix "$PREFIX" "$LOCAL"
