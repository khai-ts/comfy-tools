# Brand kits

This repo is the brand studio for **Inno Asia Distribution** and its consumer brand **Nael & Newk**. Each brand
has equal standing and its own kit:

| Folder | Brand | Feel | Use it for |
|---|---|---|---|
| [`naelnewk/`](naelnewk/BRAND.md) | Nael & Newk | warm, calm, sunlit home routines | TikTok, Instagram, Shopify, membership and promo campaigns |
| [`innoasia/`](innoasia/BRAND.md) | Inno Asia Distribution | clean, clinical, white and ice-blue glass | B2B decks, healthcare professionals, corporate site, LinkedIn |

> **Work in progress.** Much of this branding is still being developed. Use the kits as inspiration and a
> sense of each brand's feel, not strict rules. Be creative and try new directions. The firm rules are only the
> ones under "Rules that apply to both brands" below.

Each kit contains:
- `BRAND.md`: the guidelines (identity, logo, colours, imagery, voice, contacts).
- `brand.json`: the same guidelines as data, which `brand.py` uses to style prompts.
- `logo/`, `products/`, `reference/`, `sub-brands/`: real assets from the brand's websites.

`formats.json` lists the output sizes for each channel. `CHANGELOG.md` logs every change to the kits, and
research behind them lives in [`../research/`](../research/README.md). Agents keep both up to date as they work.

## Generating on-brand content

```bash
python brand.py list
# images: subject + scene preset + brand style + brand negatives, at the channel's size
python brand.py image naelnewk "woman stretching by a sunny window" --scene routine --format tiktok --count 2
python brand.py image naelnewk "empty tabletop" --scene product-backdrop --format product-square --count 3
python brand.py image innoasia "capsule with molecules inside" --scene science --format banner --count 2
# music beds and sound effects
python brand.py music naelnewk --preset calm --seconds 30 --count 2
python brand.py music innoasia --preset corporate --seconds 60
python brand.py sfx naelnewk "soft bubble pop for a caption appearing" --seconds 1 --count 3
```

Add `--dry-run` to see the exact `image.py` / `audio.py` command. Any other option is passed through.
Takes go to `out/brand/<brand>/` (scratch, gitignored). `python brand.py save <files> --brand <b> --format <f>
--title "<name>"` copies the keepers, cropped to the channel size, into `creations/<brand>/<date>_<name>/`.
`python brand.py doctor` checks the setup in plain words.

## Rules that apply to both brands

1. **Never let a model draw the logo, packaging or text.** It will misspell them. Generate clean images,
   then add the real logo and text in an editor (Canva, CapCut, Figma) or composite them in code.
2. **Product shots use the real packshots** from `naelnewk/products/`. Either generate an empty backdrop and
   composite the box (`cutout.py` can lift the box off its background), or use an image-edit model that takes
   the packshot as a reference (below).
3. **No medical claims** in any caption, voiceover or on-image text. Use "support" wording.
4. Keep the two brands recognisably distinct (today: Nael & Newk warm and homely, Inno Asia cool and clinical).
   Within that, experiment.
5. Show Malaysian people, multi-ethnic, including women in hijab where it fits.

## Beyond this repo's scripts: other Comfy Cloud models

`brand.py` covers text-to-image (Z-Image Turbo), music (ACE-Step) and sound effects (Stable Audio). Comfy
Cloud also offers partner models, which you can reach through Claude's Comfy connector or the Comfy Cloud
web app. Apply the same brand kit to them by pasting the `style` and `negative` text from `brand.json` into the
prompt.

| Need | Approach |
|---|---|
| Real product in a lifestyle scene | **Proven: Nano Banana Pro (Gemini 3 Pro Image) on Comfy Cloud** with the packshots from `naelnewk/products/` as reference images, plus the brand style prompt. This is how the membership pictures were made. Then check the boxes: blur or fix any misspelled fine print or wrong doses. Flux Kontext and GPT Image are alternatives |
| TikTok / Reels video | Generate a still with `brand.py image ... --format tiktok`, then animate it with an image-to-video model (e.g. Kling, Veo, Seedance) |
| Voice-over | A text-to-speech partner model (e.g. ElevenLabs), with a script written in the brand voice |
| Background removal | `cutout.py` locally, or a partner background-removal model |

Models and prices change. Check credit costs before batch runs, and keep takes to 2 to 4.
