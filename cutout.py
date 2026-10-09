"""Turn a render on a flat "screen" (generate with image.py --screen green|magenta) into a
transparent PNG: key out the background, trim to the subject, optionally fit it to a fixed size,
and optionally build a glow mask of its lights (for games: add it on top in HDR so lights bloom).

Examples:
    python cutout.py out/images/fox_..._1.png                       # -> fox_..._1_cut.png, trimmed
    python cutout.py render.png --key magentaish --fit 1024x768      # padded to 1024x768, bottom-centred
    python cutout.py render.png --fit 512x512 --anchor center --glow  # + render_cut_glow.png
    python cutout.py sky_tower.png --key flood                       # gradient/sky background

Keys:
    greenish (default) / magentaish: any pixel where green (or red+blue) clearly dominates, which
        handles the muddy, shaded screens diffusion models tend to paint; edges are despilled
    green / magenta: distance to the exact colour (for clean, flat screens)
    flood: smooth regions touching the border, plus enclosed gaps of the same colour (needs scipy)
"""

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter


def key_dominant(rgba, channel, hard, soft):
    """channel "green": green beats red and blue; "magenta": red and blue both beat green."""
    r, g, b = (rgba[..., i].astype(np.int32) for i in range(3))
    lead = g - np.maximum(r, b) if channel == "green" else np.minimum(r, b) - g
    out = rgba.copy()
    a = out[..., 3].astype(np.float32)
    edge = (lead > soft) & (lead < hard)
    t = np.clip((hard - lead) / (hard - soft), 0, 1)
    a = np.where(lead >= hard, 0, np.where(edge, a * t, a))
    if channel == "green":   # despill: no edge pixel greener than its red/blue
        out[..., 1] = np.where(edge, np.maximum(r, b).clip(0, 255), g)
    else:
        out[..., 0] = np.where(edge, np.minimum(r, g + soft), r)
        out[..., 2] = np.where(edge, np.minimum(b, g + soft), b)
    out[..., 3] = a.astype(np.uint8)
    return out


def key_exact(rgba, colour, tol=110, soft=60):
    rgb = rgba[..., :3].astype(np.float32)
    d = np.linalg.norm(rgb - np.array(colour, np.float32), axis=2)
    out = rgba.copy()
    a = out[..., 3].astype(np.float32)
    out[..., 3] = np.where(d < tol, 0, np.where(d < tol + soft, a * (d - tol) / soft, a)).astype(np.uint8)
    return out


def key_flood(rgba, edge=0.06, hole_tol=0.14):
    from scipy import ndimage
    rgb = rgba[..., :3].astype(np.float32) / 255.0
    grad = np.zeros(rgb.shape[:2], np.float32)
    for c in range(3):
        grad = np.maximum(grad, np.hypot(ndimage.sobel(rgb[..., c], 0), ndimage.sobel(rgb[..., c], 1)) / 8.0)
    smooth = ndimage.binary_opening(grad < edge, iterations=1)
    lab, n = ndimage.label(smooth)
    ring = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
    ref = np.median(ring, axis=0)
    idx = np.arange(n + 1)
    cols = np.stack([ndimage.mean(rgb[..., c], lab, index=idx) for c in range(3)], 1)
    dist = np.linalg.norm(cols - ref, axis=1)
    border = np.zeros(n + 1, bool)
    border[np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))] = True
    bg = (dist < hole_tol) | (border & (dist < hole_tol * 2.0))
    bg[0] = False
    fg = ndimage.binary_dilation(~bg[lab], iterations=1)
    alpha = ndimage.gaussian_filter(fg.astype(np.float32), 0.7)
    out = rgba.copy()
    out[..., 3] = (np.clip(alpha, 0, 1) * 255).astype(np.uint8)
    return out


def trim(img):
    bbox = img.getchannel("A").point(lambda v: 255 if v > 16 else 0).getbbox()
    return img.crop(bbox) if bbox else img


def fit(img, size, anchor):
    tw, th = size
    s = min(tw / img.width, th / img.height)
    img = img.resize((max(1, round(img.width * s)), max(1, round(img.height * s))), Image.LANCZOS)
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    y = th - img.height if anchor == "bottom" else (th - img.height) // 2
    out.paste(img, ((tw - img.width) // 2, y), img)
    return out


def glow_mask(img):
    """Guess the lights: bright and either saturated warm (red/amber), neon (cyan/pink/purple) or
    near-white. Black elsewhere, with a soft halo. Hand-paint it if the guess is off."""
    px = np.asarray(img).astype(np.float32) / 255.0
    rgb, a = px[..., :3], px[..., 3]
    v = rgb.max(axis=2)
    mn = rgb.min(axis=2)
    s = np.where(v > 0, (v - mn) / np.maximum(v, 1e-6), 0)
    hsv_h = np.asarray(img.convert("RGB").convert("HSV"))[..., 0].astype(np.float32) / 255.0
    warm = (v > 0.4) & (s > 0.55) & ((hsv_h < 0.11) | (hsv_h > 0.93))
    neon = (v > 0.85) & (s > 0.6) & (hsv_h > 0.45) & (hsv_h < 0.9)
    white = (v > 0.95) & (s < 0.15)
    lit = (warm | neon | white) & (a >= 0.5)
    boosted = np.clip(rgb / np.maximum(v, 0.01)[..., None], 0, 1)
    out = np.zeros_like(px)
    out[..., :3] = np.where(lit[..., None], boosted, 0)
    out[..., 3] = 1.0
    m = Image.fromarray((out * 255).astype(np.uint8), "RGBA")
    halo = m.filter(ImageFilter.GaussianBlur(max(2, img.width // 250)))
    return Image.blend(halo, m, 0.6)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("image", type=Path)
    p.add_argument("--key", default="greenish", choices=["greenish", "magentaish", "green", "magenta", "flood", "none"])
    p.add_argument("--fit", default="", help="WxH: scale into this size, transparent padding")
    p.add_argument("--anchor", default="bottom", choices=["bottom", "center"], help="where --fit places the subject")
    p.add_argument("--no-trim", action="store_true")
    p.add_argument("--glow", action="store_true", help="also write <out>_glow.png (lights mask)")
    p.add_argument("--out", type=Path, default=None, help="output path (default: <image>_cut.png)")
    a = p.parse_args()

    rgba = np.asarray(Image.open(a.image).convert("RGBA")).copy()
    if a.key == "greenish":
        rgba = key_dominant(rgba, "green", hard=22, soft=10)
    elif a.key == "magentaish":
        rgba = key_dominant(rgba, "magenta", hard=40, soft=20)
    elif a.key in ("green", "magenta"):
        rgba = key_exact(rgba, (0, 255, 0) if a.key == "green" else (255, 0, 255))
    elif a.key == "flood":
        rgba = key_flood(rgba)
    img = Image.fromarray(rgba, "RGBA")
    if not a.no_trim:
        img = trim(img)
    if a.fit:
        img = fit(img, tuple(int(v) for v in a.fit.lower().split("x")), a.anchor)
    out = a.out or a.image.with_name(a.image.stem + "_cut.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    print(f"wrote {out} ({img.width}x{img.height})")
    if a.glow:
        g = out.with_name(out.stem + "_glow.png")
        glow_mask(img).save(g)
        print(f"wrote {g}")


if __name__ == "__main__":
    main()
