"""Audio on Comfy Cloud: sound effects with Stable Audio Open 1.0, music with ACE-Step 1.5.

Sound effects (short keyword prompts work best):
    python audio.py sfx "soft wooden button click, single, very short, dry" --seconds 1 --count 4
    python audio.py sfx "magic chime sparkle rising" --seconds 2.5 --name chime

Music (style tags; instrumental unless you give lyrics):
    python audio.py music "lofi hip hop, dusty drums, warm rhodes chords, vinyl crackle" --bpm 80 --seconds 90
    python audio.py music "drift phonk, cowbell melody, distorted 808" --bpm 140 --key "F# minor" \\
        --seconds 180 --structure drops --count 3
    python audio.py music "acoustic folk ballad" --lyrics lyrics.txt --seconds 150

Every take is reported with a brightness figure (sfx: high = whine or screech) or a loudness
contour over time (music: shows where the build-ups and drops are), so you can pick takes
without listening to all of them. Outputs land in out/audio/ (or --out).
"""

import argparse
import random
import re
import time
from pathlib import Path

from comfy import run

SFX_NEGATIVE = ("voice, speech, talking, distortion, harsh noise, clipping, long reverb tail, high pitched whine, "
                "screech, squeal, hiss")
# section tags shape a song even without lyrics
STRUCTURES = {
    "instrumental": "[Instrumental]",
    "drops": "[Intro]\n\n[Build]\n\n[Drop]\n\n[Breakdown]\n\n[Build]\n\n[Drop]\n\n[Outro]",
    "song": "[Intro]\n\n[Verse]\n\n[Chorus]\n\n[Verse]\n\n[Chorus]\n\n[Bridge]\n\n[Chorus]\n\n[Outro]",
    "loop": "[Instrumental]\n\n[Groove]",
}


def sfx_workflow(prompt, negative, seconds, takes, seed, steps, cfg):
    return {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "stable-audio-open-1.0.safetensors"}},
        "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "t5-base.safetensors", "type": "stable_audio"}},
        "3": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["2", 0]}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"text": negative, "clip": ["2", 0]}},
        "5": {"class_type": "EmptyLatentAudio", "inputs": {"seconds": seconds, "batch_size": takes}},
        "6": {"class_type": "KSampler", "inputs": {"model": ["1", 0], "seed": seed, "steps": steps, "cfg": cfg,
              "sampler_name": "dpmpp_3m_sde", "scheduler": "exponential", "positive": ["3", 0],
              "negative": ["4", 0], "latent_image": ["5", 0], "denoise": 1.0}},
        "7": {"class_type": "VAEDecodeAudio", "inputs": {"samples": ["6", 0], "vae": ["1", 2]}},
        "8": {"class_type": "SaveAudioAdvanced", "inputs": {"audio": ["7", 0], "filename_prefix": "comfy-tools/sfx",
              "format": "flac"}},
    }


def music_workflow(tags, lyrics, seconds, bpm, key, timesig, seed, fmt):
    save = {"audio": ["18", 0], "filename_prefix": "comfy-tools/music", "format": fmt}
    if fmt == "mp3":
        save["format.quality"] = "V0"
    return {
        "104": {"class_type": "UNETLoader", "inputs": {"unet_name": "acestep_v1.5_turbo.safetensors", "weight_dtype": "default"}},
        "105": {"class_type": "DualCLIPLoader", "inputs": {"clip_name1": "qwen_0.6b_ace15.safetensors",
                "clip_name2": "qwen_4b_ace15.safetensors", "type": "ace", "device": "default"}},
        "106": {"class_type": "VAELoader", "inputs": {"vae_name": "ace_1.5_vae.safetensors"}},
        "94": {"class_type": "TextEncodeAceStepAudio1.5", "inputs": {"clip": ["105", 0], "tags": tags,
               "lyrics": lyrics, "seed": seed, "bpm": bpm, "duration": seconds, "timesignature": str(timesig),
               "language": "en", "keyscale": key, "generate_audio_codes": True, "cfg_scale": 2,
               "temperature": 0.85, "top_p": 0.9, "top_k": 0, "min_p": 0}},
        "47": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["94", 0]}},
        "78": {"class_type": "ModelSamplingAuraFlow", "inputs": {"model": ["104", 0], "shift": 3}},
        "98": {"class_type": "EmptyAceStep1.5LatentAudio", "inputs": {"seconds": seconds, "batch_size": 1}},
        "3": {"class_type": "KSampler", "inputs": {"model": ["78", 0], "seed": seed, "steps": 8, "cfg": 1,
              "sampler_name": "euler", "scheduler": "simple", "positive": ["94", 0], "negative": ["47", 0],
              "latent_image": ["98", 0], "denoise": 1}},
        "18": {"class_type": "VAEDecodeAudio", "inputs": {"samples": ["3", 0], "vae": ["106", 0]}},
        "107": {"class_type": "SaveAudioAdvanced", "inputs": save},
    }


def _read(path):
    import numpy as np
    import soundfile as sf
    x, sr = sf.read(path)
    return (x if x.ndim == 1 else x.mean(axis=1)), sr, np


def brightness(path):
    """Spectral centroid and share of energy above 5 kHz: clicks and thuds should sit low, a take
    with most of its energy up high is a whine or screech."""
    try:
        x, sr, np = _read(path)
        spec = np.abs(np.fft.rfft(x))
        freqs = np.fft.rfftfreq(len(x), 1.0 / sr)
        centroid = float((spec * freqs).sum() / max(spec.sum(), 1e-9))
        high = float(spec[freqs > 5000].sum() / max(spec.sum(), 1e-9))
        return f"centroid {centroid:5.0f} Hz, {high:.0%} above 5 kHz" + ("  << HARSH" if high > 0.5 else "")
    except Exception as e:  # noqa: BLE001 - informational only
        return f"(no report: {e})"


def contour(path, window=8.0):
    """Loudness per window as a strip of characters (quiet ' .:-=+*#%@' loud): a good track for
    a game or video usually shows a quieter intro, build-ups and clearly louder drops."""
    try:
        x, sr, np = _read(path)
        n = int(window * sr)
        rms = np.array([np.sqrt((x[i:i + n] ** 2).mean()) for i in range(0, len(x) - n + 1, n)])
        db = 20 * np.log10(rms / max(rms.max(), 1e-9) + 1e-9)
        strip = "".join(" .:-=+*#%@"[min(9, int((d + 24) / 24 * 9.99))] if d > -24 else " " for d in db)
        return f"{len(x) / sr:5.1f}s  range {db.min():5.1f} dB  |{strip}|"
    except Exception as e:  # noqa: BLE001
        return f"(no report: {e})"


def slug(text):
    return re.sub(r"[^a-z0-9]+", "_", text.lower())[:28].strip("_") or "audio"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="kind", required=True)
    s = sub.add_parser("sfx", help="sound effect (Stable Audio Open)")
    s.add_argument("prompt")
    s.add_argument("--seconds", type=float, default=2.0)
    s.add_argument("--count", type=int, default=2, help="takes (generated as one batch)")
    s.add_argument("--negative", default=SFX_NEGATIVE)
    s.add_argument("--steps", type=int, default=50)
    s.add_argument("--cfg", type=float, default=5.0)
    m = sub.add_parser("music", help="music (ACE-Step 1.5)")
    m.add_argument("tags", help="style description: genre, instruments, mood, tempo feel")
    m.add_argument("--lyrics", default="", help="lyrics text, or a path to a .txt file (default: instrumental)")
    m.add_argument("--structure", default="instrumental", choices=STRUCTURES,
                   help="section layout for instrumentals (ignored with --lyrics)")
    m.add_argument("--seconds", type=float, default=120.0)
    m.add_argument("--bpm", type=int, default=100)
    m.add_argument("--key", default="C major", help='e.g. "A minor", "F# minor"')
    m.add_argument("--timesig", type=int, default=4)
    m.add_argument("--count", type=int, default=1, help="takes (separate jobs, different seeds)")
    m.add_argument("--format", default="mp3", choices=["mp3", "flac"])
    for sp in (s, m):
        sp.add_argument("--seed", type=int, default=None)
        sp.add_argument("--name", default="")
        sp.add_argument("--out", default="out/audio")
    a = p.parse_args()

    seed = a.seed if a.seed is not None else random.randint(1, 2**31)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    if a.kind == "sfx":
        name = a.name or slug(a.prompt)
        jobs = [(f"{name}_{stamp}", sfx_workflow(a.prompt, a.negative, a.seconds, a.count, seed, a.steps, a.cfg))]
        report = brightness
    else:
        lyrics = a.lyrics
        if lyrics and Path(lyrics).is_file():
            lyrics = Path(lyrics).read_text(encoding="utf-8")
        lyrics = lyrics or STRUCTURES[a.structure]
        name = a.name or slug(a.tags)
        jobs = [(f"{name}_{stamp}_s{seed + i}", music_workflow(a.tags, lyrics, a.seconds, a.bpm, a.key, a.timesig,
                                                                seed + i, a.format)) for i in range(a.count)]
        report = contour
    for path in run(jobs, a.out, "audio"):
        print(f"    {path.name}: {report(path)}")


if __name__ == "__main__":
    main()
