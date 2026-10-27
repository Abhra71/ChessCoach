"""Trailer 2, version 3: the app's screens as floating windows (rounded corners, a thin edge, a soft shadow) and the
blurred, darkened 3D shots that sit behind them. Run after prep_flashes.py and scene.py:
    python installer/trailer3d/prep_cards.py <root>      (reads <root>/flashes and <root>/frames, writes <root>/cards)
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFilter

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
OUT = os.path.join(ROOT, "cards")
SCALE = 0.60          # a 1920x1080 screen shown 1152 wide
PAD = 70              # room for the shadow
RADIUS = 22

os.makedirs(OUT, exist_ok=True)


def window(src, dst):
    shot = Image.open(src).convert("RGB")
    w, h = int(shot.width * SCALE), int(shot.height * SCALE)
    shot = shot.resize((w, h), Image.LANCZOS)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), RADIUS, fill=255)
    card = Image.new("RGBA", (w + 2 * PAD, h + 2 * PAD), (0, 0, 0, 0))
    shadow = Image.new("L", card.size, 0)
    ImageDraw.Draw(shadow).rounded_rectangle((PAD + 6, PAD + 22, PAD + w + 6, PAD + h + 22), RADIUS, fill=200)
    shadow = shadow.filter(ImageFilter.GaussianBlur(26))
    card.paste(Image.new("RGBA", card.size, (0, 0, 0, 255)), (0, 0), shadow)
    card.paste(shot, (PAD, PAD), mask)
    edge = Image.new("RGBA", card.size, (0, 0, 0, 0))  # a thin light edge, like glass catching the light
    ImageDraw.Draw(edge).rounded_rectangle((PAD, PAD, PAD + w - 1, PAD + h - 1), RADIUS, outline=(255, 255, 255, 46), width=2)
    card.alpha_composite(edge)
    card.save(dst)


def backdrop(src, dst):
    im = Image.open(src).convert("RGB").filter(ImageFilter.GaussianBlur(24))
    im = Image.eval(im, lambda v: int(v * 0.42))
    vignette = Image.new("L", im.size, 0)
    ImageDraw.Draw(vignette).ellipse((-300, -250, im.width + 300, im.height + 250), fill=255)
    vignette = vignette.filter(ImageFilter.GaussianBlur(180))
    im = Image.composite(im, Image.new("RGB", im.size, (0, 0, 0)), vignette)
    im.save(dst)


for name in ("03-home", "02-review", "04-practice", "08-guess", "05-train", "07-level"):
    window(os.path.join(ROOT, "flashes", name + ".png"), os.path.join(OUT, name + ".png"))
    print("card", name)
for i, frame in enumerate(("rank/rank_0040", "above/above_0060", "blunder/blunder_0012", "rise/rise_0020",
                           "rank/rank_0110", "above/above_0110")):
    src = os.path.join(ROOT, "frames", frame + ".png")
    if os.path.exists(src):
        backdrop(src, os.path.join(OUT, f"back{i}.png"))
        print("backdrop", i, frame)
