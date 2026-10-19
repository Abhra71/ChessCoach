"""The coach's voice: Kokoro (open-source, Apache-2.0) speaking on this computer, no internet needed.

say(text) -> WAV bytes. Sentences are spoken one at a time by the app, so the first one starts in about a second.
Model files: voice/kokoro-v1.0.int8.onnx and voice/voices-v1.0.bin (python -m coach.get_voice downloads them).
"""
import hashlib
import io
import re
import threading
import wave

from coach.paths import APP, DATA, FROZEN, PROJECT

VOICE_DIR = (APP if FROZEN else PROJECT) / "voice"
MODEL = VOICE_DIR / "kokoro-v1.0.int8.onnx"
VOICES = VOICE_DIR / "voices-v1.0.bin"
CACHE = DATA / "voice-cache"
CHOICES = {  # the voices offered in Settings
    "af_heart": "Heart, American", "bf_emma": "Emma, British", "am_michael": "Michael, American",
    "bm_george": "George, British",
}
# the coaches' voices (coach/coaches.py): Maya af_heart at normal speed, with pauses between sentences, was "the
# optimum" in the 13 Oct test; Viktor am_michael, a little slower. Zara and Arjun were removed that day.
COACH_VOICES = ("af_heart", "am_michael")
SPEED = {"am_michael": 0.9}
DEFAULT = "af_heart"  # chosen by the player who tested the beta

_engine = None
_lock = threading.Lock()


def available():
    return MODEL.exists() and VOICES.exists()


def tidy_leftovers(temp=None):
    """The speech library copies espeak-ng.dll into a new temp folder every start and only deletes it on a clean
    exit, so closed apps left 144 of them (60 MB) by 14 Oct. Remove the old ones; a copy in use is locked, and kept."""
    import shutil
    import tempfile
    from pathlib import Path
    removed = 0
    for d in Path(temp or tempfile.gettempdir()).glob("tmp*"):
        try:
            if d.is_dir() and [f.name for f in d.iterdir()] == ["espeak-ng.dll"]:
                shutil.rmtree(d)
                removed += 1
        except OSError:
            pass
    return removed


def _kokoro():
    global _engine
    if _engine is None:
        tidy_leftovers()
        from kokoro_onnx import Kokoro
        _engine = Kokoro(str(MODEL), str(VOICES))
    return _engine


def warm():
    """Load the model and run it once, without the cache (19 Oct: the start-up "Ready." came from the cache, so the
    model wasn't loaded and the coach's first new sentence waited about 5 s)."""
    with _lock:
        _kokoro().create("Ready.", voice=DEFAULT, speed=SPEED.get(DEFAULT, 1.0), lang="en-us")


def sentences(text):
    """Split into short pieces to speak one after another (keeps the first words fast)."""
    parts = re.split(r"(?<=[.!?])\s+", " ".join(text.split()))
    return [p for p in parts if p.strip()]


def speakable(text):
    """Chess notation read aloud: 'Nf3' -> 'knight f3', 'Qxd4+' -> 'queen takes d4, check'."""
    names = {"K": "king", "Q": "queen", "R": "rook", "B": "bishop", "N": "knight"}

    def move(m):
        san = m.group(0)
        if san.startswith("O-O-O"):
            return "castles long"
        if san.startswith("O-O"):
            return "castles"
        piece = names.get(san[0], "")
        rest = san[1:] if piece else san
        rest = rest.replace("x", " takes ").replace("+", ", check").replace("#", ", checkmate").replace("=", " promotes to ")
        for k, v in names.items():
            rest = rest.replace(f"to {k}", f"to {v}")
        return f"{piece} {rest}".strip()

    text = re.sub(r"\b(?:O-O(?:-O)?|[KQRBN]?[a-h]?[1-8]?x?[a-h][1-8](?:=[QRBN])?)[+#]?", move, text)
    return re.sub(r"\s+", " ", text).replace(" ,", ",")


def say(text, voice=DEFAULT):
    """WAV bytes for one short piece of text (cached, so repeated phrases are instant)."""
    voice = voice if voice in CHOICES or voice in COACH_VOICES else DEFAULT
    text = speakable(text)[:600]
    speed = SPEED.get(voice, 1.0)
    key = hashlib.sha1(f"{voice}|{speed}|{text}".encode()).hexdigest()
    cached = CACHE / f"{key}.wav"
    if cached.exists():
        return cached.read_bytes()
    with _lock:  # one sentence at a time: the model uses all cores anyway
        samples, rate = _kokoro().create(text, voice=voice, speed=speed, lang="en-gb" if voice[0] == "b" else "en-us")
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes((samples.clip(-1, 1) * 32767).astype("<i2").tobytes())
    CACHE.mkdir(parents=True, exist_ok=True)
    cached.write_bytes(buf.getvalue())
    return buf.getvalue()
