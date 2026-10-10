"""The coach listens: Whisper (faster-whisper, MIT) turns the player's spoken question into text, on this computer.

The app sends plain 16 kHz mono samples (recorded in the window), so no audio decoder is needed.
Model: voice/whisper-<size> (python -m coach.get_voice copies or downloads it).
"""
import threading

import numpy as np

from coach.paths import FROZEN, HOME
from coach.voice import VOICE_DIR

SIZE = "small.en"  # small.en hears chess words (knight, e4, Nf3) far better than base.en; see logbook
# installed app: downloaded once into the player's own folder; from source: voice/ in the project
MODEL_DIR = (HOME / "voice" if FROZEN else VOICE_DIR) / f"whisper-{SIZE}"
RATE = 16000
HINT = ("Chess questions. Words: knight, bishop, rook, queen, king, pawn, castle, check, checkmate, fork, pin, "
        "e4, d4, c3, Nf3, Bc4, Qxd5, take, capture, hanging, defend.")

_model = None
_lock = threading.Lock()


def available():
    return (MODEL_DIR / "model.bin").exists()


def _whisper():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        _model = WhisperModel(str(MODEL_DIR), device="cpu", compute_type="int8")
    return _model


def transcribe(samples):
    """float32 samples at 16 kHz -> the words said."""
    audio = np.asarray(samples, dtype=np.float32)
    if audio.size < RATE // 4:  # under a quarter of a second: nothing said
        return ""
    with _lock:
        segments, _ = _whisper().transcribe(audio, language="en", beam_size=5, initial_prompt=HINT,
                                            vad_filter=True)
        return " ".join(s.text.strip() for s in segments).strip()


def resample(samples, rate):
    """Any rate -> 16 kHz (linear; fine for speech)."""
    samples = np.asarray(samples, dtype=np.float32)
    if rate == RATE:
        return samples
    n = int(len(samples) * RATE / rate)
    return np.interp(np.linspace(0, len(samples) - 1, n), np.arange(len(samples)), samples).astype(np.float32)
