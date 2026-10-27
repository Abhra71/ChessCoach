"""The Store's 16:9 images, from a 4K still of the app's own 3D welcome board (source_welcome_board.png):
hero.png (3840x2160, no words: the Store writes the name over it) and trailer_thumb.png (1920x1080, logo and name).

Run: python installer/store-hero/make_hero.py
"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
src = Image.open(os.path.join(HERE, "source_welcome_board.png")).convert("RGB")
W, H = src.size  # 3840x2160


def shade(size, left, bottom, strength=235):
    """A soft dark edge: `left` and `bottom` are how far it reaches (0..1)."""
    w, h = size
    x = np.clip(1 - np.arange(w) / (w * left), 0, 1) ** 1.3 * strength
    y = np.clip(1 - np.arange(h)[::-1] / (h * bottom), 0, 1) ** 1.8 * 200
    return Image.fromarray(np.maximum(x[None, :], y[:, None]).astype(np.uint8))


# 1. hero art: the whole still, a quiet dark edge on the left and the bottom
hero = src.copy()
hero.paste(Image.new("RGB", hero.size, (5, 5, 5)), (0, 0), shade(hero.size, 0.42, 0.30))
hero.save(os.path.join(HERE, "hero.png"), optimize=True)

# 2. the trailer's thumbnail: the bishop to the right, the name on the left
crop = src.crop((0, 270, 2880, 270 + 1620)).resize((1920, 1080), Image.LANCZOS)
crop.paste(Image.new("RGB", crop.size, (5, 5, 5)), (0, 0), shade(crop.size, 0.66, 0.22, strength=252))
d = ImageDraw.Draw(crop)
logo = Image.open(os.path.join(HERE, "..", "StoreLogo2160.png")).convert("RGBA").resize((210, 210), Image.LANCZOS)
x0, y0 = 120, 330
crop = crop.convert("RGBA")
crop.alpha_composite(logo, (x0 - 18, y0))
F = "C:/Windows/Fonts/"
WORDS = [((x0, y0 + 230), "Knightwise", ImageFont.truetype(F + "palab.ttf", 118), (246, 242, 234)),
         ((x0 + 4, y0 + 380), "Your personal chess coach", ImageFont.truetype(F + "segoeuil.ttf", 46), (214, 208, 198)),
         ((x0 + 4, y0 + 460), "FREE ON THE MICROSOFT STORE", ImageFont.truetype(F + "segoeuib.ttf", 30), (230, 184, 96))]
glow = Image.new("L", crop.size, 0)  # a soft shadow under the words, so they read on the light squares
for at, txt, font, _ in WORDS:
    ImageDraw.Draw(glow).text(at, txt, font=font, fill=255, stroke_width=10, stroke_fill=255)
glow = glow.filter(ImageFilter.GaussianBlur(22)).point(lambda v: min(255, int(v * 1.6)))
crop.paste(Image.new("RGBA", crop.size, (0, 0, 0, 255)), (0, 0), glow)
d = ImageDraw.Draw(crop)
for at, txt, font, col in WORDS:
    d.text(at, txt, font=font, fill=col)
crop.convert("RGB").save(os.path.join(HERE, "trailer_thumb.png"), optimize=True)
print("hero", hero.size, "thumb", crop.size)
