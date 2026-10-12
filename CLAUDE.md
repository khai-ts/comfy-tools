# Brand studio (Inno Asia / Nael & Newk)

The instructions for every agent are in AGENTS.md, which Codex also reads. Follow it: it covers who you are talking to
(a non-technical person, so hide the commands and use plain words), the first reply with suggestions, brand rules,
the API key, and the tools.

@AGENTS.md

Claude Code specifics:
- In a Claude cloud session `out/` and untracked files are lost when the session ends. Commit the `creations/` the
  person wants to keep to the session's branch and push.
- If you have a Comfy Cloud connector (mcp__Comfy__*), you may use it for partner models (image editing with the real
  packshots, image-to-video, voice-over). Apply the style and negative text from `brand/<slug>/brand.json`, and
  estimate credits first.
