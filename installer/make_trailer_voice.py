"""The trailer's voices (coach/ui/trailer.html), as sound files in coach/ui/vendor/trailer/voice: the narrator (Viktor's
voice, slower, like a film trailer) and Maya's one line, when she first comes on screen. Kokoro, on this PC; nothing
is played. Run: python installer/make_trailer_voice.py
"""
import io
import sys
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from coach import voice  # noqa: E402

VIKTOR, MAYA = "am_michael", "af_heart"  # coach/coaches.py
LINES = {  # name: (voice, speed, words)
    "n1": (VIKTOR, 0.8, "Every game you lose..."),
    "n2": (VIKTOR, 0.8, "has a lesson in it."),
    "n3": (VIKTOR, 0.82, "Most players never find it."),
    "n4": (VIKTOR, 0.75, "Now... you will."),
    "n5": (VIKTOR, 0.8, "Knightwise."),
    "n6": (VIKTOR, 0.8, "Free... and fair."),
    "m1": (MAYA, 1.0, "I'm Maya. I'll go through every game with you."),
    "v1": (VIKTOR, 0.9, "I'm Viktor. I'll show you how far you've come."),
}
OUT = Path(__file__).resolve().parent.parent / "coach" / "ui" / "vendor" / "trailer" / "voice"


def main():
    if not voice.available():
        sys.exit("The voice isn't installed: python -m coach.get_voice")
    OUT.mkdir(parents=True, exist_ok=True)
    for name, (who, speed, text) in LINES.items():
        samples, rate = voice._kokoro().create(text, voice=who, speed=speed, lang="en-us")
        buf = io.BytesIO()
        with wave.open(buf, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(rate)
            w.writeframes((samples.clip(-1, 1) * 32767).astype("<i2").tobytes())
        (OUT / f"{name}.wav").write_bytes(buf.getvalue())
        print(f"{name}  {len(samples) / rate:.2f} s  {text}")
    print(f"-> {OUT}")


if __name__ == "__main__":
    main()
