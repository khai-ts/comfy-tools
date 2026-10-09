# comfy-tools

Small command-line tools for generating **images, sound effects and music on [Comfy Cloud](https://cloud.comfy.org)**
from a terminal, a script, or a Claude Code session, plus the post-processing that makes the results usable:
background removal for images, trimming and seamless loops for audio.

| Tool | What it does | Model |
|---|---|---|
| `image.py` | text to image, any size or aspect, optional flat green/magenta "screen" for cutouts | Z-Image Turbo |
| `audio.py sfx` | sound effects from short prompts, several takes per batch, brightness report | Stable Audio Open 1.0 |
| `audio.py music` | songs or loops from style tags (+ optional lyrics, BPM, key, section layout), loudness contour report | ACE-Step 1.5 |
| `cutout.py` | removes the screen (or a gradient sky), trims, fits to a size, optional glow mask of lights | local |
| `sound.py` | trims one-shot sounds, makes seamless bar-cut music loops, analyses songs (tempo, loudness) | local |

Everything runs on Comfy Cloud's GPUs; your machine only sends prompts and downloads results.
Image generation costs roughly 0.5 to 1 credit per image. Every job is logged with its GPU time and an
estimated cost in `out/<kind>/usage.json`.

## Setup (your own computer)

1. Python 3.9 or newer.
2. `pip install -r requirements.txt` (only `cutout.py`, `sound.py` and the reports need packages;
   `image.py` and `audio.py` work with plain Python).
3. Your Comfy Cloud API key (Comfy Cloud → account settings → API keys), set as an environment variable:
   - macOS / Linux: `export COMFY_CLOUD_API_KEY=...` (add it to `~/.bashrc` or `~/.zshrc` to keep it)
   - Windows: `setx COMFY_CLOUD_API_KEY "..."`, then open a new terminal
   - or copy `.env.example` to `.env` and paste it there (`.env` is gitignored)

## Quick start

```bash
# images
python image.py "a cozy reading nook, warm light, watercolor" --count 4 --aspect 16:9
python image.py "cartoon fox mascot waving, flat colours" --screen green --count 2
python cutout.py out/images/cartoon_fox_..._1.png --fit 512x512 --anchor center

# sound effects (pick takes by the brightness report: clicks and thuds should sit low)
python audio.py sfx "soft wooden button click, single, very short, dry" --seconds 1 --count 4
python sound.py trim out/audio/soft_wooden_..._2.flac click.wav --max 0.3

# music
python audio.py music "lofi hip hop, dusty drums, warm rhodes, vinyl crackle" --bpm 80 --seconds 90
python audio.py music "drift phonk, cowbell melody, distorted 808" --bpm 140 --key "F# minor" \
    --seconds 180 --structure drops --count 3
python sound.py analyze out/audio/*.mp3
python sound.py loop out/audio/lofi_..._1.mp3 menu_loop.ogg --bpm 80 --bars 16
```

Every script has `--help` with all options. Outputs go to `out/images/` and `out/audio/`
(gitignored) unless you pass `--out`.

## Using it with Claude Code in the cloud (claude.ai/code)

A cloud session runs Claude in a fresh Linux sandbox with a copy of a GitHub repo. These steps give
those sessions access to Comfy Cloud so you can just ask "make 4 icons of ..." or "generate a chill
menu loop". Menu names on claude.ai may differ slightly from the ones below.

### 1. Put the tools in a repo Claude can open

Either:
- **Fork this repo** (or use it directly if you own it), or
- **Copy it into your project**, e.g. as a `tools/comfy/` folder or a git submodule, so Claude can use
  it while working on that project. If you do this, mention the folder in your project's `CLAUDE.md`
  ("Image and audio generation: see tools/comfy/README.md") so Claude knows it's there.

### 2. Connect GitHub

In [claude.ai/code](https://claude.ai/code), connect your GitHub account and give the Claude GitHub
app access to that repository.

### 3. Create a cloud environment

In the environment settings (from the environment selector when starting a session):

- **Environment variables**: add
  ```
  COMFY_CLOUD_API_KEY=your-key
  ```
- **Network access**: Comfy Cloud is not on the default allowlist. Choose a custom allowlist and
  include these hosts (keep the defaults too, so `pip` can reach PyPI):
  ```
  cloud.comfy.org
  storage.googleapis.com
  ```
  (`storage.googleapis.com` is where Comfy Cloud's result downloads redirect to.)

### 4. Start a session

Pick the repo and the environment and start. The repo's `.claude/settings.json` runs
`scripts/session-start.sh` when the session begins: in the cloud it installs the Python packages,
and it warns you if the API key is missing. Then ask in plain words, for example:

- "Generate 4 takes of a pixel-art treasure chest on a green screen, cut out the best one at 256x256."
- "Make UI sounds for a button tap, a back button and a success chime, trim them, and put them in assets/sfx/."
- "Make a 90 second calm lofi loop at 80 BPM for a menu and turn it into a seamless .ogg."

### 5. Get the results out

`out/` is gitignored, so files Claude generates disappear when the session ends unless they are
saved somewhere tracked. Ask Claude to copy the keepers into a tracked folder (for example
`assets/`) and commit and push them to a branch; then pull that branch or merge it.

## Keeping the API key safe

- **Never commit it.** It belongs in the environment variable (cloud: the environment's variables;
  local: your shell or the gitignored `.env`). The scripts never print it.
- **Anyone and anything in a session that has the key can use it**: the scripts, Claude, and anyone
  with access to that cloud environment. Only add it to environments you control.
- **Use a separate key for cloud sessions** if Comfy Cloud lets you create more than one, so you can
  revoke it without touching your local setup.
- **Watch spending** in Comfy Cloud's billing page and in the `usage.json` logs. A typo in `--count`
  is the usual way to burn credits.
- **If a key leaks** (committed by accident, pasted in a chat), revoke it in Comfy Cloud right away
  and create a new one. Removing it from git history is not enough.

## Tips

- **Cutouts:** ask for `--screen green`, or `--screen magenta` when the subject itself is green.
  `cutout.py --key greenish` (the default) copes with the muddy, shaded screens diffusion models
  paint and removes the floor shadow too. For skies and gradients use `--key flood`.
- **Picking takes without listening:** `audio.py` prints a brightness figure per sound effect
  (most energy above 5 kHz usually means a whine or screech) and a loudness strip per song. For a
  game or video track, look for a quiet intro and clearly louder drops: `|.:*%@@@@=*#@@@@*.|`.
- **Song structure:** `--structure drops` lays out intro, build, drop, breakdown, build, drop,
  outro; `song` gives verses and choruses; pass `--lyrics file.txt` for vocals.
- **Different workflow or model:** `image.py` loads `workflows/zimage_turbo.json` (a ComfyUI API-format
  export); the audio workflows are built in `audio.py`. Swap in your own the same way.

## Licences

The code is MIT (see `LICENSE`). **What you generate is governed by Comfy Cloud's terms and each
model's licence** (Z-Image Turbo, Stable Audio Open 1.0, ACE-Step 1.5), which differ, especially
for commercial use. Check them before shipping generated images, sounds or music in a product.
