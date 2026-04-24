#!/usr/bin/env bash
set -euo pipefail
# Simple asset fetcher for team workflows.
# Usage:
#   scripts/fetch_assets.sh [assets_dir]
# Environment variables:
#   DEEPSEEK_URL - tar.gz URL containing DeepSeek-V4-Pro folder (optional)
#   SESAME_PROMPTS_URL - URL to prompts archive (optional)
#   MINIFORGE_URL - URL to Miniforge installer (optional)

ASSETS_DIR="${1:-assets}"
mkdir -p "$ASSETS_DIR"

MINIFORGE_URL="${MINIFORGE_URL:-https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-x86_64.sh}"
MINIFORGE_OUT="$ASSETS_DIR/Miniforge3-MacOSX-x86_64.sh"
echo "Downloading Miniforge installer -> $MINIFORGE_OUT"
curl -L "$MINIFORGE_URL" -o "$MINIFORGE_OUT"

if [ -n "${DEEPSEEK_URL:-}" ]; then
  echo "Downloading DeepSeek archive from $DEEPSEEK_URL"
  tmp="$ASSETS_DIR/deepseek.tar.gz"
  curl -L "$DEEPSEEK_URL" -o "$tmp"
  mkdir -p DeepSeek-V4-Pro
  echo "Extracting DeepSeek into ./DeepSeek-V4-Pro"
  tar -xzf "$tmp" -C DeepSeek-V4-Pro --strip-components=1
else
  echo "No DEEPSEEK_URL set. To fetch DeepSeek assets, set DEEPSEEK_URL and re-run."
fi

if [ -n "${SESAME_PROMPTS_URL:-}" ]; then
  echo "Downloading Sesame prompts from $SESAME_PROMPTS_URL"
  tmp2="$ASSETS_DIR/sesame_prompts.tar.gz"
  curl -L "$SESAME_PROMPTS_URL" -o "$tmp2"
  mkdir -p csm/prompts
  tar -xzf "$tmp2" -C csm/prompts --strip-components=1
else
  echo "No SESAME_PROMPTS_URL set. To fetch prompts, set SESAME_PROMPTS_URL and re-run."
fi

echo "Assets fetched into $ASSETS_DIR (if provided) and any configured directories."
