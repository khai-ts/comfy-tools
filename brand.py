"""On-brand generation: wraps image.py and audio.py with a brand's style, negatives, sizes and music presets.

Brands live in brand/<slug>/brand.json (naelnewk, innoasia); output formats in brand/formats.json.

Examples:
    python brand.py list                                   # brands, scenes, music presets, formats
    python brand.py image naelnewk "woman stretching by a window" --scene routine --format tiktok --count 2
    python brand.py image innoasia "glass capsule with molecules" --scene science --format banner
    python brand.py music naelnewk --preset calm --seconds 30 --count 2 --tags "female humming"
    python brand.py sfx innoasia "notification chime" --seconds 1.5 --count 3

Any extra options (--seed, --steps, --screen, --structure, --lyrics, ...) are passed to image.py / audio.py.
Outputs go to out/brand/<slug>/images and out/brand/<slug>/audio unless you pass --out.
"""

import argparse
import json
import re
import subprocess
import sys

from comfy import HERE

BRANDS = HERE / "brand"


def load(slug):
    path = BRANDS / slug / "brand.json"
    if not path.exists():
        sys.exit(f"unknown brand {slug!r}; have: {', '.join(brands())}")
    return json.loads(path.read_text(encoding="utf-8"))


def brands():
    return sorted(p.parent.name for p in BRANDS.glob("*/brand.json"))


def formats():
    return {k: v for k, v in json.loads((BRANDS / "formats.json").read_text(encoding="utf-8")).items() if k[0] != "_"}


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "_", text.lower())[:28].strip("_")


def show():
    for slug in brands():
        b = load(slug)
        print(f"{slug}: {b['name']} - {b['tagline']}")
        print(f"  scenes: {', '.join(b['image']['scenes'])}")
        print(f"  music:  {', '.join(b['music'])}")
    print("formats:")
    for k, v in formats().items():
        print(f"  {k:15} generate {v['generate']:10} deliver {v['deliver']:10} {v['use']}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="kind", required=True)
    sub.add_parser("list", help="brands, scenes, music presets and formats")
    i = sub.add_parser("image", help="on-brand image (image.py)")
    i.add_argument("brand")
    i.add_argument("text", metavar="subject")
    i.add_argument("--scene", default="", help="a scene preset from the brand (see list)")
    i.add_argument("--format", default="square", help="an output format (see list)")
    i.add_argument("--raw", action="store_true", help="skip the brand style suffix (keeps negatives)")
    m = sub.add_parser("music", help="on-brand music (audio.py music)")
    m.add_argument("brand")
    m.add_argument("--preset", default="", help="a music preset from the brand (default: the first)")
    m.add_argument("--tags", dest="text", default="", help="extra style tags appended to the preset")
    s = sub.add_parser("sfx", help="on-brand sound effect (audio.py sfx)")
    s.add_argument("brand")
    s.add_argument("text", metavar="keywords")
    for sp in (i, m, s):
        sp.add_argument("--dry-run", action="store_true", help="print the command instead of running it")
    a, rest = p.parse_known_args()
    if a.kind == "list":
        return show()
    b = load(a.brand)
    out = ["--out", str(HERE / "out" / "brand" / a.brand / ("images" if a.kind == "image" else "audio"))]
    if "--out" in rest:
        out = []

    if a.kind == "image":
        img, fmts = b["image"], formats()
        if a.format not in fmts:
            sys.exit(f"unknown format {a.format!r}; have: {', '.join(fmts)}")
        if a.scene and a.scene not in img["scenes"]:
            sys.exit(f"unknown scene {a.scene!r}; {a.brand} has: {', '.join(img['scenes'])}")
        parts = [a.text, img["scenes"].get(a.scene, "")] + ([] if a.raw else [img["style"]])
        cmd = [sys.executable, str(HERE / "image.py"), ", ".join(x for x in parts if x),
               "--size", fmts[a.format]["generate"], "--name", f"{a.brand}_{a.format}_{slugify(a.text)}"]
        if "--negative" not in rest:
            cmd += ["--negative", img["negative"]]
    elif a.kind == "music":
        presets = b["music"]
        name = a.preset or next(iter(presets))
        if name not in presets:
            sys.exit(f"unknown preset {name!r}; {a.brand} has: {', '.join(presets)}")
        m = presets[name]
        cmd = [sys.executable, str(HERE / "audio.py"), "music", ", ".join(x for x in [m["tags"], a.text] if x),
               "--name", f"{a.brand}_{name}"]
        cmd += [x for flag in ("bpm", "key") if f"--{flag}" not in rest for x in (f"--{flag}", str(m[flag]))]
    else:
        cmd = [sys.executable, str(HERE / "audio.py"), "sfx", f"{a.text}, {b['sfx']}",
               "--name", f"{a.brand}_{slugify(a.text)}"]
    cmd += rest + out
    if a.dry_run:
        print(" ".join(f'"{c}"' if " " in c else c for c in cmd))
        return
    sys.exit(subprocess.call(cmd))


if __name__ == "__main__":
    main()
