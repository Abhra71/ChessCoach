"""The app's quick flashes for trailer 2: the 1.0 Store screenshots, with every opponent's name replaced by
"Opponent" (they never said yes to being in a trailer). Run: python installer/trailer3d/prep_flashes.py <outdir>"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

SRC = os.path.join(os.path.dirname(__file__), "..", "store-shots-1.0", "upload")
OUT = sys.argv[1] if len(sys.argv) > 1 else "flashes"
BOLD = ImageFont.truetype(r"C:\Windows\Fonts\seguisb.ttf", 23)
TITLE = ImageFont.truetype(r"C:\Windows\Fonts\seguisb.ttf", 27)
SMALL = ImageFont.truetype(r"C:\Windows\Fonts\seguisb.ttf", 15)

# file: [(box to cover, the colour behind it is sampled at, replacement text, font, text colour)]
NAMES = {
    "02-review.png": [((560, 60, 840, 100), (550, 80), "vs Opponent", TITLE, (240, 240, 236))],
    "04-practice.png": [((1192, 158, 1420, 192), (1180, 150), "vs Opponent", BOLD, (240, 240, 236))],
    "03-home.png": [((916, 98, 1040, 120), (912, 140), "Opponent", SMALL, (215, 215, 210))],
    "08-guess.png": [((14, 376, 212, 402), (100, 420), "", SMALL, (0, 0, 0))],  # a passing status line
}
KEEP = ["02-review.png", "04-practice.png", "03-home.png", "05-train.png", "07-level.png", "06-course.png", "08-guess.png"]

os.makedirs(OUT, exist_ok=True)
for name in KEEP:
    src = os.path.join(SRC, name) if os.path.exists(os.path.join(SRC, name)) else os.path.join(OUT, name)
    im = Image.open(src).convert("RGB")
    d = ImageDraw.Draw(im)
    for box, sample, text, font, colour in NAMES.get(name, []):
        d.rectangle(box, fill=im.getpixel(sample))
        d.text((box[0] + 4, box[1] + (box[3] - box[1]) // 2), text, font=font, fill=colour, anchor="lm")
    im.save(os.path.join(OUT, name))
    print("ok", name)
