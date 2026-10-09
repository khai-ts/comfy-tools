"""Post-process generated audio.

One-shot sounds (UI clicks, hits): cut the leading silence so they feel instant, trim the tail with
a short fade, cap the length, peak-normalise:
    python sound.py trim out/audio/click_..._1.flac click.wav --max 0.3 --peak -6

Seamless music loop: skip a short intro, cut to whole bars, crossfade the end into the start:
    python sound.py loop out/audio/lofi_..._1.mp3 menu_loop.ogg --bpm 80 --bars 16

Quick report on songs (length, tempo, loudness contour) to pick takes without listening:
    python sound.py analyze out/audio/*.mp3
"""

import argparse
from pathlib import Path

import numpy as np
import soundfile as sf


def mono(x):
    return x if x.ndim == 1 else x.mean(axis=1)


def normalise(x, peak_db):
    p = np.abs(x).max()
    return x if p == 0 else x * (10 ** (peak_db / 20.0) / p)


def write(path, x, sr):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".ogg":
        # write in blocks: libsndfile's Vorbis encoder can crash on one big write
        ch = 1 if x.ndim == 1 else x.shape[1]
        with sf.SoundFile(path, "w", samplerate=sr, channels=ch, format="OGG", subtype="VORBIS") as f:
            for i in range(0, len(x), sr):
                f.write(x[i:i + sr].astype(np.float32))
    else:
        sf.write(path, x.astype(np.float32), sr, subtype="PCM_16" if path.suffix.lower() == ".wav" else None)


def trim(src, dst, max_len, peak_db, floor_db, fade):
    x, sr = sf.read(src)
    x = mono(x)
    fr = max(1, int(0.005 * sr))           # 5 ms RMS envelope: faint hiss doesn't count as sound
    n = len(x) // fr
    env = np.sqrt((x[: n * fr].reshape(n, fr) ** 2).mean(axis=1))
    loud = np.where(env > env.max() * 10 ** (floor_db / 20.0))[0]
    if loud.size:
        a = max(0, loud[0] * fr - int(0.002 * sr))
        b = min(len(x), (loud[-1] + 1) * fr + int(fade * sr))
        x = x[a:b].copy()
    if max_len and len(x) > max_len * sr:
        x = x[: int(max_len * sr)].copy()
    f = min(int(fade * sr), len(x))
    x[-f:] *= np.linspace(1.0, 0.0, f)
    fi = min(int(0.001 * sr), len(x))
    x[:fi] *= np.linspace(0.0, 1.0, fi)
    write(dst, normalise(x, peak_db), sr)
    print(f"wrote {dst}  {len(x) / sr:.2f}s")


def loop(src, dst, bpm, bars, skip_bars, xfade, peak_db, beats_per_bar):
    x, sr = sf.read(src)
    x = x if x.ndim == 2 else np.stack([x, x], axis=1)
    bar = beats_per_bar * 60.0 / bpm
    start = int(bar * skip_bars * sr) if len(x) > bar * (skip_bars + 8) * sr else 0
    n_bars = bars or int(((len(x) - start) / sr - xfade) // bar)
    length = int(n_bars * bar * sr)
    body = x[start:start + length].copy()
    tail = x[start + length:start + length + int(xfade * sr)]
    f = min(len(tail), int(xfade * sr))
    if f > 0:   # equal-power crossfade of what follows the loop point into the loop's start
        t = np.linspace(0.0, 1.0, f)[:, None]
        body[:f] = body[:f] * np.sin(t * np.pi / 2) + tail[:f] * np.cos(t * np.pi / 2)
    write(dst, normalise(body, peak_db), sr)
    print(f"wrote {dst}  {n_bars} bars, {len(body) / sr:.1f}s")


def analyze(paths, window):
    try:
        import librosa
    except ImportError:
        librosa = None
    for p in paths:
        x, sr = sf.read(p)
        x = mono(x)
        n = int(window * sr)
        rms = np.array([np.sqrt((x[i:i + n] ** 2).mean()) for i in range(0, len(x) - n + 1, n)])
        db = 20 * np.log10(rms / max(rms.max(), 1e-9) + 1e-9)
        strip = "".join(" .:-=+*#%@"[min(9, int((d + 24) / 24 * 9.99))] if d > -24 else " " for d in db)
        tempo = ""
        if librosa is not None:
            y = librosa.resample(x.astype(np.float32), orig_sr=sr, target_sr=22050)
            bpm, beats = librosa.beat.beat_track(y=y, sr=22050)
            bt = librosa.frames_to_time(beats, sr=22050)
            ibi = np.diff(bt)
            steady = np.std(ibi) / np.mean(ibi) if len(ibi) > 4 else float("nan")
            tempo = f"tempo {float(np.atleast_1d(bpm)[0]):5.1f} (wobble {steady:.3f})  "
        clip = (np.abs(x) > 0.99).mean()
        print(f"{Path(p).name}: {len(x) / sr:5.1f}s  {tempo}range {db.min():5.1f} dB  clipped {clip:.2%}  |{strip}|")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("trim", help="one-shot sound: trim silence, cap length, normalise")
    t.add_argument("src")
    t.add_argument("dst")
    t.add_argument("--max", type=float, default=0.0, help="longest length in seconds (0 = no cap)")
    t.add_argument("--peak", type=float, default=-6.0, help="peak level in dBFS")
    t.add_argument("--floor", type=float, default=-36.0, help="what counts as silence, dB below the peak")
    t.add_argument("--fade", type=float, default=0.03, help="tail fade in seconds")
    lo = sub.add_parser("loop", help="seamless music loop cut to whole bars")
    lo.add_argument("src")
    lo.add_argument("dst", help=".ogg, .wav or .flac")
    lo.add_argument("--bpm", type=float, required=True)
    lo.add_argument("--bars", type=int, default=0, help="loop length in bars (default: as many as fit)")
    lo.add_argument("--skip-bars", type=int, default=2, help="intro bars to skip")
    lo.add_argument("--xfade", type=float, default=2.0)
    lo.add_argument("--peak", type=float, default=-3.0)
    lo.add_argument("--beats-per-bar", type=int, default=4)
    an = sub.add_parser("analyze", help="length, tempo (if librosa is installed) and loudness contour")
    an.add_argument("paths", nargs="+")
    an.add_argument("--window", type=float, default=8.0, help="seconds per contour character")
    a = p.parse_args()
    if a.cmd == "trim":
        trim(a.src, a.dst, a.max, a.peak, a.floor, a.fade)
    elif a.cmd == "loop":
        loop(a.src, a.dst, a.bpm, a.bars, a.skip_bars, a.xfade, a.peak, a.beats_per_bar)
    else:
        analyze(a.paths, a.window)


if __name__ == "__main__":
    main()
