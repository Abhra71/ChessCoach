"""Trailer 2, the moving version: each recorded clip of the real app (rec.mjs) at 24 frames a second, full size, as a
floating window (rounded corners, a thin light edge, a soft shadow) in transparent PNGs, so a zoom stays pixel-sharp.

Run: python installer/trailer3d/prep_clips.py <root>     (reads <root>/clips2/<name>/, writes <root>/cards/clip_<name>/)
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFilter

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
FPS, PAD, RADIUS = 24, 90, 30
# name: (seconds skipped at the start, seconds used): timed so each clip's action lands in the zoom's hold
CLIPS = {"home": (1.0, 5.4), "review": (1.2, 5.4), "practice": (2.9, 5.4), "guess": (1.0, 5.4),
         "train": (0.0, 5.4), "level": (1.2, 5.4)}
SRC = os.environ.get("KW_CLIPS", "clips2")  # clips2: rec2.mjs, the pointer and live screencast (version 5)

W, H = 1920, 1080
mask = Image.new("L", (W, H), 0)
ImageDraw.Draw(mask).rounded_rectangle((0, 0, W - 1, H - 1), RADIUS, fill=255)
shadow = Image.new("L", (W + 2 * PAD, H + 2 * PAD), 0)
ImageDraw.Draw(shadow).rounded_rectangle((PAD + 8, PAD + 30, PAD + W + 8, PAD + H + 30), RADIUS, fill=210)
shadow = shadow.filter(ImageFilter.GaussianBlur(38))
base = Image.new("RGBA", shadow.size, (0, 0, 0, 0))
base.paste(Image.new("RGBA", shadow.size, (0, 0, 0, 255)), (0, 0), shadow)
edge = Image.new("RGBA", shadow.size, (0, 0, 0, 0))
ImageDraw.Draw(edge).rounded_rectangle((PAD, PAD, PAD + W - 1, PAD + H - 1), RADIUS, outline=(255, 255, 255, 50), width=3)

ONLY = sys.argv[2:]  # just these clips (default: all)
for name, (skip, length) in CLIPS.items():
    if ONLY and name not in ONLY:
        continue
    src = os.path.join(ROOT, SRC, name)
    meta = json.load(open(os.path.join(src, "frames.json")))
    times = meta["frames"]  # when each captured frame was taken, in seconds
    out = os.path.join(ROOT, "cards", f"clip_{name}")
    os.makedirs(out, exist_ok=True)
    last = None
    for k in range(int(length * FPS)):
        t = skip + k / FPS
        i = min(range(len(times)), key=lambda j: abs(times[j] - t)) if t <= times[-1] else len(times) - 1
        if i != last:  # a new captured frame: make its window (otherwise the same window is saved again)
            shot = Image.open(os.path.join(src, f"{i}.jpg")).convert("RGB")
            card = base.copy()
            card.paste(shot, (PAD, PAD), mask)
            card.alpha_composite(edge)
            last = i
        card.save(os.path.join(out, f"clip_{name}_{k + 1:04d}.png"), compress_level=1)
    print("clip", name, int(length * FPS), "frames")
