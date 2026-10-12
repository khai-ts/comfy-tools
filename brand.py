"""On-brand generation: wraps image.py and audio.py with a brand's style, negatives, sizes and music presets.

Brands live in brand/<slug>/brand.json (naelnewk, innoasia); output formats in brand/formats.json.

Examples:
    python brand.py doctor                                 # plain-language setup check (run this first)
    python brand.py list                                   # brands, scenes, music presets, formats
    python brand.py image naelnewk "woman stretching by a window" --scene routine --format tiktok --count 2
    python brand.py image innoasia "glass capsule with molecules" --scene science --format banner
    python brand.py music naelnewk --preset calm --seconds 30 --count 2 --tags "female humming"
    python brand.py sfx innoasia "notification chime" --seconds 1.5 --count 3
    python brand.py save out/brand/naelnewk/images/x.png --brand naelnewk --format tiktok --title "sleep routine"
    python brand.py open creations                         # show a folder in Finder / Explorer

Any extra options (--seed, --steps, --screen, --structure, --lyrics, ...) are passed to image.py / audio.py.
Takes go to out/brand/<slug>/images and out/brand/<slug>/audio (scratch, gitignored) unless you pass --out;
`save` copies the chosen ones, sized for their channel, to creations/<slug>/<date>_<title>/.
"""

import argparse
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from comfy import COMFY, HERE, api_key

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


def doctor():
    """Checks everything generation needs and explains problems in plain words. Never prints the key."""
    problems = []
    try:
        key = api_key()
    except SystemExit:
        key = ""
    has_key = bool(key) and key != "paste-your-key-here"
    print(f"{'OK ' if has_key else 'FIX'} Comfy Cloud key {'found' if has_key else 'not set'}")
    if not has_key:
        problems.append("No Comfy Cloud API key. Tell IT to setup the API key for you.")
    ok = sys.version_info >= (3, 9)
    print(f"{'OK ' if ok else 'FIX'} Python {sys.version.split()[0]}")
    if not ok:
        problems.append("Python 3.9 or newer is needed (python.org/downloads).")
    missing = [m for m in ("PIL", "numpy", "soundfile", "scipy") if importlib.util.find_spec(m) is None]
    print(f"{'FIX' if missing else 'OK '} helper packages{': missing ' + ', '.join(missing) if missing else ''}")
    if missing:
        problems.append(f"Install packages: {sys.executable} -m pip install -r requirements.txt")
    # an authenticated, free call: proves the network path and (with a key) that the key works
    headers = {"User-Agent": "comfy-tools"}
    if has_key:
        headers["X-API-Key"] = key
    try:
        urllib.request.urlopen(urllib.request.Request(COMFY + "/api/queue", headers=headers), timeout=20).close()
        reach, key_ok = True, has_key
    except urllib.error.HTTPError as e:
        reach, key_ok = e.code in (401, 403) and "cloudflare" in e.headers.get("Server", ""), False
    except Exception:
        reach, key_ok = False, False
    print(f"{'OK ' if reach else 'FIX'} can reach {COMFY}")
    if not reach:
        problems.append("Can't reach Comfy Cloud: the internet is off or blocked here. Allow cloud.comfy.org and "
                        "storage.googleapis.com in this environment's internet settings (Codex cloud: Agent internet "
                        "access; Claude cloud: Network access), or run on your own computer.")
    elif has_key and not key_ok:
        print("FIX Comfy Cloud rejected the key")
        problems.append("The API key was rejected. Tell IT to setup the API key for you.")
    for x in problems:
        print("  - " + x)
    print("READY" if not problems else "NOT READY")
    return 0 if not problems else 1


def save(files, brand, fmt, title, to):
    """Copies chosen takes to a tidy folder; images are centre-cropped and resized to the format's deliver size."""
    dest = Path(to) if to else HERE / "creations" / brand / f"{time.strftime('%Y-%m-%d')}_{slugify(title) or 'picks'}"
    dest.mkdir(parents=True, exist_ok=True)
    size = None
    if fmt:
        fmts = formats()
        if fmt not in fmts:
            sys.exit(f"unknown format {fmt!r}; have: {', '.join(fmts)}")
        size = tuple(int(v) for v in fmts[fmt]["deliver"].split("x"))
    for i, f in enumerate(map(Path, files), 1):
        if not f.exists():
            sys.exit(f"not found: {f}")
        stem = f"{brand}_{fmt + '_' if fmt else ''}{slugify(title) or f.stem}_{i}"
        if size and f.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
            from PIL import Image, ImageOps
            out = dest / f"{stem}.png"
            ImageOps.fit(Image.open(f), size, Image.LANCZOS).save(out)
        else:
            out = dest / f"{stem}{f.suffix}"
            shutil.copy2(f, out)
        print(f"saved {out.relative_to(HERE) if out.is_relative_to(HERE) else out}")
    return dest


def open_folder(path):
    path = Path(path).resolve()
    path.mkdir(parents=True, exist_ok=True)
    opener = {"darwin": ["open"], "win32": ["explorer"]}.get(sys.platform, ["xdg-open"])
    try:
        subprocess.Popen(opener + [str(path)])
    except OSError:
        pass
    print(path)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="kind", required=True)
    sub.add_parser("list", help="brands, scenes, music presets and formats")
    sub.add_parser("doctor", help="check setup (Python, packages, API key, network) in plain words")
    sv = sub.add_parser("save", help="copy chosen takes to creations/<brand>/<date>_<title>/, sized for a channel")
    sv.add_argument("files", nargs="+")
    sv.add_argument("--brand", required=True)
    sv.add_argument("--format", default="", help="resize and crop images to this format's deliver size")
    sv.add_argument("--title", default="", help="short name for the folder, e.g. 'sleep routine tiktok'")
    sv.add_argument("--to", default="", help="folder to save into instead")
    op = sub.add_parser("open", help="open a folder in Finder / Explorer")
    op.add_argument("path", nargs="?", default="creations")
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
    if rest and a.kind in ("list", "doctor", "save", "open"):
        p.error(f"unrecognized arguments: {' '.join(rest)}")
    if a.kind == "list":
        return show()
    if a.kind == "doctor":
        sys.exit(doctor())
    if a.kind == "save":
        load(a.brand)
        return save(a.files, a.brand, a.format, a.title, a.to)
    if a.kind == "open":
        return open_folder(a.path)
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
