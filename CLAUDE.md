# comfy-tools (Inno Asia / Nael & Newk brand studio)

Brand fork of comfy-tools for **Inno Asia Distribution** and **Nael & Newk** (equal weight). Brand kits, logos,
product packshots and reference images are in `brand/`. Read `brand/README.md` and the relevant
`brand/<slug>/BRAND.md` before generating anything for a brand.

CLI tools that generate images (Z-Image Turbo), sound effects (Stable Audio Open) and music (ACE-Step 1.5) on
Comfy Cloud, plus local post-processing. See README.md for full usage.

- `python brand.py image|music|sfx <naelnewk|innoasia> ...` (on-brand wrapper; `python brand.py list`)
- `python image.py "<prompt>" [--count N] [--aspect 16:9 | --size WxH] [--screen green|magenta] [--name x] [--out dir]`
- `python cutout.py <png> [--key greenish|magentaish|green|magenta|flood|none] [--fit WxH] [--anchor bottom|center] [--glow]`
- `python audio.py sfx "<keywords>" --seconds S --count N` (prints brightness per take)
- `python audio.py music "<style tags>" --bpm N --key "A minor" --seconds S [--structure drops|song|loop] [--lyrics f.txt] [--count N]`
- `python sound.py trim <in> <out.wav> [--max S] | loop <in> <out.ogg> --bpm N [--bars N] | analyze <files>`

Working rules:
- The API key is the `COMFY_CLOUD_API_KEY` environment variable. Never print it, write it to a file, or commit it.
  If it's missing, tell the user to add it to their environment (README: "Keeping the API key safe").
- Generation spends the user's credits: keep `--count` modest (2 to 4) unless asked, and say how many jobs you ran.
  Costs are logged in `out/<kind>/usage.json`.
- You can't hear audio or judge taste reliably: use the brightness/contour reports and look at images, pick the
  best candidates, and tell the user which you picked and why so they can check.
- `out/` is gitignored. Copy the files the user wants to keep into a tracked folder and commit them, or they're
  lost when a cloud session ends.
- Write text files with LF line endings.

Brand rules:
- Never have a model draw logos, packaging or text. Composite the real files from `brand/` instead.
- No medical claims (cure/treat/prevent) in any caption or copy. Use "support" wording. English copy.
- Nael & Newk = warm, sunlit, homely; Inno Asia = white/ice-blue, clinical glass. Don't mix the looks.
- Save keepers to `assets/<slug>/` and commit. When a brand detail is missing (see TODOs in BRAND.md), ask the user.
