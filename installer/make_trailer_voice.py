"""Maya's lines for the trailer (docs/TRAILER.md), as sound files in Videos/Knightwise/trailer, in her own voice
(Kokoro, on this PC). Run: python installer/make_trailer_voice.py. Nothing is played; the files are only written.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from coach import voice  # noqa: E402

LINES = [
    "I go through your games with you, one moment at a time.",
    "Only two in ten players at your level find this. So let's learn it.",
    "Your practice comes from your own games.",
    "Play it again from where it went wrong, against someone at their level.",
    "Before you play someone, I show you how they play.",
    "Click Play Bots, in the red ring.",
    "When chess.com changes, I find my way again.",
    "Knightwise. Free, and fair.",
]
OUT = Path.home() / "Videos" / "Knightwise" / "trailer"
MAYA = "af_heart"  # Maya's voice (coach/coaches.py)


def main():
    if not voice.available():
        sys.exit("The voice isn't installed: python -m coach.get_voice")
    OUT.mkdir(parents=True, exist_ok=True)
    for i, line in enumerate(LINES, 1):
        (OUT / f"{i:02d} maya.wav").write_bytes(voice.say(line, MAYA))
        print(f"{i:02d}  {line}")
    print(f"-> {OUT}")


if __name__ == "__main__":
    main()
