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


def close():
    global _engine
    if _engine is not None:
        try:
            _engine.quit()
        except Exception:  # already gone
            pass
        _engine = None


# An open engine keeps a thread running that Python waits for at exit, so a Knightwise that had used Stockfish never
# finished closing (14 Oct test: every such process hung on exit). Close it before Python starts waiting.
threading._register_atexit(close)
