#!/usr/bin/env bash
# Runs when a Claude Code session starts (.claude/settings.json). In a Claude cloud session it
# installs the Python packages; on your own machine it does nothing (set those up once yourself).
if [ "$CLAUDE_CODE_REMOTE" = "true" ]; then
  pip install -q -r "$(dirname "$0")/../requirements.txt" >/dev/null 2>&1 \
    && echo "comfy-tools: Python packages installed" \
    || echo "comfy-tools: pip install failed (is PyPI allowed in the environment's network access?)"
fi
if [ -z "$COMFY_CLOUD_API_KEY" ] && [ ! -f "$(dirname "$0")/../.env" ]; then
  echo "comfy-tools: COMFY_CLOUD_API_KEY is not set; generation won't work until it is (see README)"
fi
exit 0
