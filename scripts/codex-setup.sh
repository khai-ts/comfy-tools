#!/usr/bin/env bash
# Setup script for a Codex cloud environment (Environment settings, setup script: bash scripts/codex-setup.sh).
# Installs the Python packages and, because Codex removes secrets before the agent runs, saves the
# COMFY_CLOUD_API_KEY secret into the gitignored .env file where the scripts can still read it.
cd "$(dirname "$0")/.." || exit 1
pip install -q -r requirements.txt || echo "brand studio: pip install failed"
if [ -n "$COMFY_CLOUD_API_KEY" ]; then
  umask 077
  printf 'COMFY_CLOUD_API_KEY=%s\n' "$COMFY_CLOUD_API_KEY" > .env
  echo "brand studio: API key saved to .env"
else
  echo "brand studio: COMFY_CLOUD_API_KEY is not set; add it as a secret or environment variable"
fi
