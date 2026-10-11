"""Makes the extension set-up pictures from the builder's real Chrome screenshots.

Run:  python installer/make_guide_shots.py
Reads screenshots-raw/9.png (Developer mode off), 10.png (on) and 11.png (the folder dialog), kept out of git.
Writes coach/ui/guide/*.png: cropped to the part that matters, other extensions left out, the OneDrive name blurred,
the extension folder typed into the dialog's address bar, and the spot to click circled in red.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "screenshots-raw"
OUT = ROOT / "coach" / "ui" / "guide"
RED = (255, 77, 66)
FONT = "C:/Windows/Fonts/segoeui.ttf"
BOLD = "C:/Windows/Fonts/segoeuib.ttf"


def ring(img, box, pad=10, width=5):
    """A red rounded ring around the spot to click."""
    x0, y0, x1, y1 = box
    ImageDraw.Draw(img).rounded_rectangle((x0 - pad, y0 - pad, x1 + pad, y1 + pad), radius=min((y1 - y0) // 2 + pad, 22),
                                          outline=RED, width=width)


def blur(img, box):
    img.paste(img.crop(box).filter(ImageFilter.GaussianBlur(9)), box[:2])


def cover(img, box, text, size, color=(230, 230, 230), font=FONT, at=None):
    """Paint over a spot with the colour just left of it, then write text there."""
    bg = img.getpixel((box[0] + 2, box[1] + 2))
    draw = ImageDraw.Draw(img)
    draw.rectangle(box, fill=bg)
    draw.text(at or (box[0] + 6, box[1] + (box[3] - box[1] - size) // 2 - 2), text, font=ImageFont.truetype(font, size), fill=color)


def save(img, name):
    OUT.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(OUT / name, optimize=True)
    print(OUT / name, img.size)


def main():
    off, on, dialog = (Image.open(RAW / f"{n}.png").convert("RGB") for n in (9, 10, 11))

    shot = off.crop((0, 0, 960, 230))  # 1: the address bar
    ring(shot, (155, 60, 640, 100), pad=4)
    save(shot, "1-address.png")

    shot = off.crop((1100, 0, 1916, 230))  # 2: Developer mode, top right
    ring(shot, (1728 - 1100, 174, 1902 - 1100, 200), pad=7)
    save(shot, "2-developer-mode.png")

    shot = on.crop((0, 0, 960, 300))  # 3: Load unpacked
    ring(shot, (30, 234, 183, 279))
    save(shot, "3-load-unpacked.png")

    shot = dialog.crop((373, 305, 1316, 897))  # 4: the folder dialog
    ox, oy = 373, 305
    blur(shot, (380 - ox, 450 - oy, 660 - ox, 486 - oy))  # the OneDrive account name
    cover(shot, (552 - ox, 357 - oy, 1000 - ox, 392 - oy), r"C:\Users\you\Documents\Knightwise\extension", 15)
    ring(shot, (548 - ox, 354 - oy, 1036 - ox, 395 - oy), pad=5)
    ring(shot, (1037 - ox, 843 - oy, 1168 - ox, 873 - oy), pad=6)
    save(shot, "4-choose-folder.png")

    shot = on.crop((505, 430, 1005, 690))  # 5: done, the extension in the list
    cover(shot, (612 - 505, 452 - 430, 900 - 505, 478 - 430), "Knightwise  0.4.0", 16, color=(232, 234, 237))
    ring(shot, (8, 8, 492, 252), pad=0)
    save(shot, "5-done.png")


if __name__ == "__main__":
    main()
