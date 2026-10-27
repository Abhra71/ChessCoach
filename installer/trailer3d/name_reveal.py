"""The maker's name for the trailer's last moment: revealed left to right as if a cover were being rubbed off it
(a soft, slightly uneven edge with a warm glint along it), in Palatino. Transparent PNG frames for the cut.

Run: python installer/trailer3d/name_reveal.py <outdir>     (writes <outdir>/name/name_0001.png ...)
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

NAME = "Abhra Chakraborty"  # the owner's full name (27 Oct)
OUT = os.path.join(sys.argv[1] if len(sys.argv) > 1 else ".", "name")
W, H, FPS = 1920, 1080, 24
LENGTH, REVEAL_START, REVEAL = 4.4, 0.25, 1.6  # seconds
FEATHER = 70.0  # how soft the rubbed edge is, in pixels
FONT = ImageFont.truetype(r"C:\Windows\Fonts\pala.ttf", 128)
Y = int(H * 0.535)  # just under "DEVELOPED BY"

text_img = Image.new("L", (W, H), 0)
d = ImageDraw.Draw(text_img)
box = d.textbbox((W // 2, Y), NAME, font=FONT, anchor="mm")
d.text((W // 2, Y), NAME, font=FONT, fill=255, anchor="mm")
text = np.asarray(text_img, dtype=np.float32) / 255
glow = np.asarray(text_img.filter(ImageFilter.GaussianBlur(9)), dtype=np.float32) / 255
x0, x1 = box[0] - 20, box[2] + 20

rng = np.random.default_rng(7)
jag = np.convolve(rng.uniform(-1, 1, H), np.ones(9) / 9, mode="same") * 16  # the edge, a little uneven down its height
xs = np.arange(W, dtype=np.float32)[None, :]
WHITE, GOLD = np.array([246, 241, 232], np.float32), np.array([255, 196, 110], np.float32)


def ease(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


os.makedirs(OUT, exist_ok=True)
frames = int(LENGTH * FPS)
for f in range(frames):
    t = f / FPS
    edge = x0 + (x1 - x0 + FEATHER) * ease((t - REVEAL_START) / REVEAL)
    e = edge + jag[:, None]                        # the edge for each row
    shown = np.clip((e - xs) / FEATHER, 0, 1)     # behind the edge: revealed
    alpha = text * shown
    moving = REVEAL_START < t < REVEAL_START + REVEAL + 0.15
    near = np.exp(-((xs - (e - FEATHER * 0.4)) / 38.0) ** 2) if moving else 0 * xs  # a warm light on the edge
    g = np.clip(glow * near * 2.4, 0, 1)
    a = np.maximum(alpha, g * 0.85)
    rgb = WHITE[None, None, :] * (1 - g[..., None]) + GOLD[None, None, :] * g[..., None]
    out = np.dstack([rgb, a[..., None] * 255]).astype(np.uint8)
    Image.fromarray(out, "RGBA").save(os.path.join(OUT, f"name_{f + 1:04d}.png"))
print("DONE", frames, "frames", OUT)
