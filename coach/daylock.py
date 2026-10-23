"""A day's set of positions stays exactly as first made until midnight (23 Oct test: Today's 5 minutes changed after
a restart; Practice and the lessons could too, because each was worked out again from a list that new games or a
restart rebuild). The first set made each day for a key is kept; every later ask that day gets the same one back."""
import json
import threading
from datetime import date

from coach.paths import DATA

FILE = DATA / "today-sets.json"
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
