"""Draws the Knightwise logo (white knight on black, a red line) and writes every icon size the app needs.

Run:  python installer/make_icons.py
Needs Microsoft Edge (to turn the drawing into a picture) and Pillow.
Writes: installer/msix/Assets/*.png (Store), installer/ChessCoach.ico (Windows), extension/icon128.png (browser).
"""
import json
import subprocess
import tempfile
import time
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
EDGE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
PIECES = ROOT / "extension" / "pieces.js"
ASSETS = ROOT / "installer" / "msix" / "Assets"
SIZE = 2160  # the Store asks for 2160x2160 box art


def knight():
    text = PIECES.read_text(encoding="utf-8")
    return json.loads(text[text.index("{"):text.rindex("}") + 1])["N"]


def logo_svg(square=True):
    """The knight is drawn on a 45x45 grid; centred and scaled to fill most of the tile."""
    tile = (f'<rect width="{SIZE}" height="{SIZE}" rx="{SIZE * 0.2}" fill="#0a0a0a"/>' if square else "")
    s = SIZE / 45 * 0.78
    off = (SIZE - 45 * s) / 2
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{SIZE}" height="{SIZE}" viewBox="0 0 {SIZE} {SIZE}">{tile}'
            f'<g transform="translate({off - 0.4 * s},{off - 0.6 * s}) scale({s})">{knight()}</g>'
            f'<rect x="{SIZE * 0.3}" y="{SIZE * 0.86}" width="{SIZE * 0.4}" height="{SIZE * 0.035}" rx="{SIZE * 0.017}" fill="#e5484d"/>'
            "</svg>")


def render(svg, out):
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "logo.html"
        page.write_text(f'<html><body style="margin:0;background:transparent">{svg}</body></html>', encoding="utf-8")
        subprocess.run([str(EDGE), "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        "--default-background-color=00000000", f"--user-data-dir={tmp}", f"--window-size={SIZE},{SIZE}",
                        f"--screenshot={out}", page.as_uri()], check=True, capture_output=True, timeout=60)
        for _ in range(100):  # Edge's launcher can return before the picture is written
            if Path(out).exists() and Path(out).stat().st_size:
                break
            time.sleep(0.2)
        time.sleep(0.5)
    return Image.open(out).convert("RGBA").crop((0, 0, SIZE, SIZE))


def fit(img, w, h, scale=1.0):
    """The logo centred on a transparent w x h canvas, taking `scale` of the shorter side."""
    side = max(1, round(min(w, h) * scale))
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    canvas.alpha_composite(img.resize((side, side), Image.LANCZOS), ((w - side) // 2, (h - side) // 2))
    return canvas


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        big = render(logo_svg(), Path(tmp) / "big.png")
    big.save(ROOT / "installer" / "StoreLogo2160.png")  # for the Store page, not inside the package
    sizes = {"StoreLogo.png": (50, 50, 1), "Square44x44Logo.png": (44, 44, 1), "Square150x150Logo.png": (150, 150, 0.7),
             "Wide310x150Logo.png": (310, 150, 0.7), "Square71x71Logo.png": (71, 71, 0.8), "Square310x310Logo.png": (310, 310, 0.7)}
    for name, (w, h, sc) in sizes.items():
        fit(big, w, h, sc).save(ASSETS / name)
        for pct in (100, 200, 400):  # crisp on high-DPI screens
            fit(big, w * pct // 100, h * pct // 100, sc).save(ASSETS / name.replace(".png", f".scale-{pct}.png"))
    for n in (16, 24, 32, 48, 256):  # taskbar icons, no tile plate
        fit(big, n, n).save(ASSETS / f"Square44x44Logo.targetsize-{n}_altform-unplated.png")
    big.resize((128, 128), Image.LANCZOS).save(ROOT / "extension" / "icon128.png")
    big.save(ROOT / "installer" / "ChessCoach.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("icons written to", ASSETS)


if __name__ == "__main__":
    main()
