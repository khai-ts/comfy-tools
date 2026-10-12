# Inno Creative Director

> **AI agents (Codex, Claude, others): read [`AGENTS.md`](AGENTS.md) and follow it.**

An AI helper that makes on-brand **images, music, sound effects, captions and content ideas** for
**Nael & Newk** and **Inno Asia Distribution**. You talk to it in plain words, and it already knows the logos,
colours, products, photo style and tone of voice.

## How to start

**With the Codex app (recommended, on your computer)**
1. Install the Codex app and sign in with your ChatGPT account.
2. Start a new chat and paste this:
   *"Set up and open this creative director for me: https://github.com/khai-ts/inno-creative-director"*
3. Codex will set things up and suggest ideas. Pick one or describe what you want.

**With Codex on the web (chatgpt.com/codex)**: someone needs to set up the environment once (see
"For IT: setting this up" below). Then pick this repo and say "hi".

**With Claude Code**: open this repo in Claude Code and say "hi".

## Things you can ask

- "Give me 5 TikTok ideas for our magnesium this month."
- "Make 3 calm morning backgrounds for a Reels video, with space for text at the top."
- "Put our Vitamin D3 + K2 box on a sunny kitchen table for Shopify."
- "A 30-second relaxing music bed for a sleep-routine video."
- "Write captions and hashtags for this picture."
- "A LinkedIn banner for Inno Asia about quality and research."
- "Make the same image square for Instagram."

## Where your files go

Finished files are saved in the **`creations`** folder, sorted by brand and date. Ask "open my creations folder"
and the helper will open it for you.

## Good to know

- If the helper says "Tell IT to setup the API key for you", forward that to IT. Until then it can still help
  with ideas and captions.
- Each image or song uses a few **Comfy Cloud credits**. The helper makes 2 to 4 options at a time and asks before
  big batches.
- AI images never include the real logo or text. Add those in Canva or CapCut, or ask the helper to place the real
  logo or product photo.
- The helper won't write medical claims ("cures", "treats"). That's deliberate.

## For IT: setting this up

If the helper says **"Tell IT to setup the API key for you"**, the Comfy Cloud key below is missing or wrong.

- **Comfy Cloud API key:** create one at cloud.comfy.org (account settings, then API keys). A separate key per
  person can be revoked on its own.
  - *On a computer:* create a file named `.env` in the repo folder containing `COMFY_CLOUD_API_KEY=<key>`
    (see `.env.example`), or set it as a user environment variable. The `.env` file never goes to GitHub.
  - *Codex on the web:* in the environment settings, add `COMFY_CLOUD_API_KEY` as an environment variable.
    Or add it as a secret and set the setup script to `bash scripts/codex-setup.sh`.
  - *Claude Code on the web:* add it as an environment variable.
- **Internet access (cloud only):** allow `cloud.comfy.org` and `storage.googleapis.com`. Also keep package
  installs (PyPI) allowed.
- **Repo access:** if this repo is private, the person using it needs access on GitHub.
- **Brand gaps to fill:** see the TODOs in `brand/naelnewk/BRAND.md` (membership details) and
  `brand/innoasia/BRAND.md` (official font).
- Technical details: [`docs/technical.md`](docs/technical.md) · brand kits: [`brand/README.md`](brand/README.md)
