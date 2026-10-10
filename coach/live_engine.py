"""One Stockfish kept open for the app's live questions (asking about a position, playing the coach)."""
import threading

from coach.analyze import open_engine

_engine = None
LOCK = threading.Lock()


def get():
    """The shared engine; use it inside `with LOCK:`."""
    global _engine
    if _engine is None:
        _engine = open_engine()
        _engine.configure({"Threads": 2, "Hash": 64})
    return _engine
