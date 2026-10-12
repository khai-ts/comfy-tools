# Nael & Newk brand kit

Consumer supplement brand from Inno Asia Distribution Sdn Bhd. "Simple Wellness. Thoughtfully Considered."
Machine-readable version (used by `brand.py`): [`brand.json`](brand.json).

> **Still developing:** this kit records the brand as it is today. It's a guide to the feel, not a strict
> rulebook. New ideas, moods and styles are welcome. Only the product facts, no medical claims and no
> generated logos or packaging text are firm.

Sources: [naelnewk.com](https://www.naelnewk.com/), [membership](https://www.naelnewk.com/pages/membership),
[TikTok @naelnewkmy](https://www.tiktok.com/@naelnewkmy) (collected October 2026).

## Identity

| | |
|---|---|
| Name | Nael & Newk (wordmark is lowercase: **nael & newk**; product titles also use NAEL&NEWK) |
| Tagline | Gentle on the stomach, Easy on your routine |
| Slogans | Simple Wellness. Thoughtfully Considered. / Wellness doesn't need to be complicated. |
| Logo tagline | **Now Everyone Can Live Well** (red pill under the logo, used on marketplace and membership) |
| Mission (TikTok bio) | Helping Malaysians make smarter wellness choices |
| Audience | Malaysian adults with busy routines: stress, sleep, fatigue, workout recovery, perimenopause, body aches |
| Trust points | Halal (JAKIM), KKM registered, clear labelling, traceability, authorised distribution |
| Language | English |

## Logo

- `logo/naelnewk-logo.png`: transparent background, use on light backgrounds.
- `logo/naelnewk-logo-original.jpg`: the original from the website, on white.
- `logo/naelnewk-logo-tagline.png`: transparent PNG with the red **"Now Everyone Can Live Well"** pill
  (`#D82024`). Used for membership, marketplace and promos. `logo/naelnewk-logo-tagline-original.jpg` is the
  same logo on white.
- Black rounded lowercase wordmark with two green leaves sprouting from the "l". Keep the leaves green
  (`#62AE30`) and the wordmark near-black. On dark or photo backgrounds, use an all-white version (to be supplied).
- Don't let image models draw the logo. Generate without text, then put the real logo on top in an editor.

## Colours

| Name | Hex | Use |
|---|---|---|
| Cocoa | `#5A4848` | Primary text and buttons on the website |
| Cocoa hover | `#685353` | Hover and selected states |
| Leaf green | `#62AE30` | Logo leaves and small accents only |
| Ink | `#1A1A1A` | Logo wordmark |
| Linen | `#F5EEDE` | Warm cream backgrounds |
| Sand | `#E8DFC8` | Cards, secondary backgrounds |
| Oat | `#C8B197` | Photographic mid-tone (wood, linen, sunlight) |
| Paper | `#FDFCFA` | Off-white page background |
| Navy | `#141F30` | Packaging (D3+K2, Mg+Zn) |
| Gold | `#A78848` | Packaging accent |
| Tagline red | `#D82024` | The "Now Everyone Can Live Well" pill. Promos only, used sparingly |

The membership dashboard has its own palette (navy `#232B3D`, leaf `#8AB925`, gold `#D4AE4A`). See
[MEMBERSHIP.md](MEMBERSHIP.md).

Typography on the website: **Inter** (400 for body, 700 for accents).

## Photography and imagery

Look at `reference/` before briefing new images. The common style:
- Soft morning sunlight through sheer curtains, gentle shadows, warm neutrals (cream, linen, oat, light wood).
- Minimal, airy interiors with a sprig of greenery, a glass of water, ceramics, pale stone.
- People: relaxed Malaysian and Asian adults, candid and calm, in natural linen or activewear. They aren't
  posing for an advert.
- Packshots: boxes on a white table with a warm wood surface and greenery behind.
- Avoid neon, heavy saturation, dark moody lighting, clutter, and anything clinical or cold. Cold clinical
  imagery belongs to Inno Asia.

## Products (`products/`)

| Product | Spec | Price | Pack colour | Positioning |
|---|---|---|---|---|
| Magnesium Bisglycinate 750mg | 150mg elemental Mg, 6 blisters x 10 tablets | RM90 | White / gold | Muscle relaxation & better sleep |
| Magnesium & Zinc Bisglycinate | Dual chelated, 6 blisters x 10 caplets | RM90 | Navy / gold | Stress, relaxation & sleep |
| Vitamin D3 + K2 | 1000 IU + 120 mcg, powered by K2VITAL, 3 blisters x 10 capsules | RM85 | Navy / silver | Bone, heart & exercise recovery support |

The images in `products/` are the real packshots. **Never ask a model to generate the packaging.** It will
invent text. Instead, generate an empty scene (`--scene product-backdrop`) and composite the real box in.
You can also use an image-edit model that takes the packshot as a reference input (see `../README.md`).

## Two registers: brand vs marketplace

- **Brand** (website, Instagram, membership): calm, minimal, warm. This is the default.
- **Marketplace** (Shopee, TikTok Shop, sale days): louder and full of social proof. See
  `reference/marketplace/`: "Malaysia's #1 fast-selling magnesium", "10,000+ sold on TikTok", star ratings,
  customer selfies, red and orange urgency. Use this register only when asked for marketplace or sale content.
  Use **only claims the team confirms are current and true**, and still make no medical claims. Shopee shop:
  @nael&newk.os.

## Membership

The Rewards program is built but **not launched yet**: [MEMBERSHIP.md](MEMBERSHIP.md) covers how it works,
the visuals and the messaging.

## Voice

- Calm, plain and honest. Short sentences. No hype and no stacked exclamation marks.
- Talk about routines and how a product fits the day, not miracles.
- Be transparent: dose, form (bisglycinate, chelated), certifications.
- **No medical claims** (cure, treat, prevent). Use "support" wording, as the site does.

Example caption: *Evenings are for slowing down. One Magnesium Bisglycinate caplet with water, gentle on the
stomach, easy on your routine.*

## Channels

- Shop: https://www.naelnewk.com/ · Shopee: @nael&newk.os
- TikTok: [@naelnewkmy](https://www.tiktok.com/@naelnewkmy) (Nael&Newk.HQ)
- Instagram / Threads: @naelnewk.my
- Facebook: Nael & Newk
