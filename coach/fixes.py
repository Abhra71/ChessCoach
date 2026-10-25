"""The fix file (1.0, flagship 6: Knightwise looks after itself).

fixes.json in the GitHub repo lists new names for what the extension looks for on chess.com, and features to pause
for everyone. Every copy reads it once a day, so when chess.com changes its site, one edit on github.com fixes every
user by the next day, with no new release. The file is only read, never sent anything; what it may contain is
checked here (short strings and the known features only), so a bad edit can't break the app.
"""
import json
import logging
import time
import urllib.request

from coach.paths import DATA

URL = "https://raw.githubusercontent.com/Abhra71/ChessCoach/main/fixes.json"
FILE = DATA / "fixes.json"
EVERY = 86400  # once a day
LISTS = ("boards", "archive_rows", "archive_slots", "game_addresses")
FEATURES = {"review", "tags", "warmup", "prep", "talk", "coach", "guide"}  # what "off" may pause
log = logging.getLogger("knightwise")


def clean(raw):
    """Only what the extension knows how to use: lists of short strings, nav targets, known features."""
    if not isinstance(raw, dict):
        raw = {}
    listed = lambda v: v if isinstance(v, list) else []  # "boards": 5 is ignored, never a crash (cloud review, 26 Oct)
    out = {k: [s for s in listed(raw.get(k)) if isinstance(s, str) and 0 < len(s) <= 200][:20] for k in LISTS}
    nav = raw.get("nav") if isinstance(raw.get("nav"), dict) else {}
    out["nav"] = {str(k)[:40]: [s for s in v if isinstance(s, str) and 0 < len(s) <= 200][:10]
                  for k, v in list(nav.items())[:50] if isinstance(v, list)}
    out["off"] = [f for f in listed(raw.get("off")) if isinstance(f, str) and f in FEATURES]
    return out


def current():
    """The fixes as last downloaded (empty when there are none yet)."""
    try:
        return clean(json.loads(FILE.read_text()).get("fixes"))
    except Exception:  # anything odd in the saved file: as if there were no fixes
        return clean({})


def refresh(force=False, fetch=None):
    """Download the fix file if a day has passed. Never raises: offline, the last copy stays."""
    try:
        saved = json.loads(FILE.read_text())
    except (OSError, ValueError):
        saved = {}
    if not force and time.time() - saved.get("at", 0) < EVERY:
        return current()
    try:
        if fetch:
            raw = fetch()
        else:
            req = urllib.request.Request(URL, headers={"User-Agent": "Knightwise (open source chess coach)"})
            with urllib.request.urlopen(req, timeout=15) as r:
                raw = json.loads(r.read(100_000))
    except Exception as e:  # offline, GitHub down, a broken edit: keep what we had
        log.info("fix file not refreshed: %s", e)
        return current()
    try:
        fixes = clean(raw)
    except Exception as e:  # a broken edit: keep what we had, and don't ask again for a day
        log.info("fix file ignored: %s", e)
        fixes = current()
    FILE.parent.mkdir(parents=True, exist_ok=True)
    FILE.write_text(json.dumps({"at": time.time(), "fixes": fixes}))
    return current()
