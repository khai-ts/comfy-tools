"""Text to image on Comfy Cloud with Z-Image Turbo (fast, about 1 credit per image).

Examples:
    python image.py "a red vintage scooter, studio photo" --count 4
    python image.py "pixel art castle at dusk" --size 1536x864
    python image.py "cartoon fox mascot, flat colours" --aspect 1:1 --screen green   # then: cutout.py
    python image.py "..." --negative "text, watermark" --seed 123 --name fox --out out/mascots

Outputs land in out/images/ (or --out) as <name>_<stamp>_<n>.png. Sizes are rounded to
multiples of 16; about 1-2 megapixels works best.
"""

import argparse
import json
import random
import re
import time
from pathlib import Path

from comfy import HERE, run

WORKFLOW = HERE / "workflows" / "zimage_turbo.json"
ASPECTS = {"1:1": (1, 1), "4:3": (4, 3), "3:4": (3, 4), "3:2": (3, 2), "2:3": (2, 3), "16:9": (16, 9),
           "9:16": (9, 16), "21:9": (21, 9), "2:1": (2, 1), "1:2": (1, 2)}
# flat "screens" that cutout.py removes cleanly; use magenta when the subject itself is green
SCREEN = ", isolated on a flat pure {} background, centered, the whole subject in frame, no shadow, no text"


def size_for(a):
    if a.size:
        w, h = (int(v) for v in a.size.lower().split("x"))
    else:
        rw, rh = ASPECTS[a.aspect]
        w, h = (a.long, a.long * rh / rw) if rw >= rh else (a.long * rw / rh, a.long)
    return max(256, round(w / 16) * 16), max(256, round(h / 16) * 16)


def build(prompt, negative, size, seed, steps):
    wf = json.loads(WORKFLOW.read_text(encoding="utf-8"))
    sampler = next(n for n in wf.values() if n["class_type"] == "KSampler")
    wf[sampler["inputs"]["positive"][0]]["inputs"]["text"] = prompt
    if negative:
        wf[sampler["inputs"]["negative"][0]]["inputs"]["text"] = negative
    sampler["inputs"]["seed"] = seed
    sampler["inputs"]["steps"] = steps
    for n in wf.values():
        if n["class_type"] == "EmptySD3LatentImage":
            n["inputs"].update(width=size[0], height=size[1])
        if n["class_type"] == "SaveImage":
            n["inputs"]["filename_prefix"] = "comfy-tools/image"
    return wf


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("prompt")
    p.add_argument("--negative", default="", help="things to avoid (replaces the workflow's default)")
    p.add_argument("--size", default="", help="WxH, e.g. 1024x1024 (overrides --aspect)")
    p.add_argument("--aspect", default="1:1", choices=ASPECTS)
    p.add_argument("--long", type=int, default=1280, help="long side in px when using --aspect")
    p.add_argument("--count", type=int, default=1)
    p.add_argument("--seed", type=int, default=None, help="first seed (each take adds 1); random if unset")
    p.add_argument("--steps", type=int, default=8)
    p.add_argument("--screen", choices=["green", "magenta"], help="render on a flat colour for cutout.py")
    p.add_argument("--name", default="", help="file name prefix (default: from the prompt)")
    p.add_argument("--out", default="out/images")
    a = p.parse_args()

    prompt = a.prompt + (SCREEN.format(a.screen) if a.screen else "")
    size = size_for(a)
    seed = a.seed if a.seed is not None else random.randint(1, 2**40)
    name = a.name or re.sub(r"[^a-z0-9]+", "_", a.prompt.lower())[:32].strip("_") or "image"
    stamp = time.strftime("%Y%m%d-%H%M%S")
    print(f"{a.count} x {size[0]}x{size[1]}, seeds {seed}..{seed + a.count - 1}")
    jobs = [(f"{name}_{stamp}_s{seed + i}", build(prompt, a.negative, size, seed + i, a.steps)) for i in range(a.count)]
    run(jobs, a.out, "images", timeout=600)


if __name__ == "__main__":
    main()
