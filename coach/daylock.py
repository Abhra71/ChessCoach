"""A day's set of positions stays exactly as first made until midnight (23 Oct test: Today's 5 minutes changed after
a restart; Practice and the lessons could too, because each was worked out again from a list that new games or a
restart rebuild). The first set made each day for a key is kept; every later ask that day gets the same one back."""
import json
import threading
from datetime import date

from coach.paths import DATA

FILE = DATA / "today-sets.json"
KEPT = DATA / "kept-sets.json"  # sets kept until they're finished, not just for the day (lessons, 25 Oct)
_LOCK = threading.Lock()


def keep(key, drills, today=None):
    """Today's drills for this key: the ones kept earlier today, else these (kept from now on)."""
    day = (today or date.today()).isoformat()
    with _LOCK:
        try:
            m = json.loads(FILE.read_text())
        except (OSError, ValueError):
            m = {}
        if m.get("day") != day:
            m = {"day": day, "sets": {}}
        if m["sets"].get(key):
            return m["sets"][key]
        if drills:
            m["sets"][key] = drills
            try:
                FILE.parent.mkdir(parents=True, exist_ok=True)
                FILE.write_text(json.dumps(m))
            except OSError:
                pass
        return drills


def keep_until_done(key, drills):
    """A lesson's positions stay the same until it's finished (25 Oct, owner: a lesson left halfway goes on from the
    next position, even on another day). release(key) when it's finished: the next go gets new ones."""
    with _LOCK:
        try:
            m = json.loads(KEPT.read_text())
        except (OSError, ValueError):
            m = {}
        if m.get(key):
            return m[key]
        if drills:
            m[key] = drills
            try:
                KEPT.parent.mkdir(parents=True, exist_ok=True)
                KEPT.write_text(json.dumps(m))
            except OSError:
                pass
        return drills


def release(key):
    """The set is finished: the next time gets new positions."""
    with _LOCK:
        try:
            m = json.loads(KEPT.read_text())
        except (OSError, ValueError):
            return
        if m.pop(key, None) is not None:
            try:
                KEPT.write_text(json.dumps(m))
            except OSError:
                pass
