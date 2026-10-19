"""What the coach heard, kept as text on this PC (1.0, flagship 6: Knightwise learns how you speak).

Never audio, never sent anywhere: one line per thing said, so the player can look back and mark what the coach got
wrong, and so the hearing learns the player's own words. When Talk works out who or what was meant (a misheard
"El Moungabs" turned out to be lmaongabs, because that's the review it opened), that name is remembered, and the
names the player uses most go into their own hearing hint (coach/ai.py). About 100 bytes a line: a year is under 1 MB.
"""
import collections
import json
import time

from coach.paths import DATA

FILE = DATA / "heard.jsonl"
WORDS = DATA / "heard-words.json"
KEEP = 5000  # lines kept; older ones go


def note(text, by):
    """One thing the player said, as heard."""
    text = " ".join(str(text).split())[:300]
    if not text:
        return
    DATA.mkdir(parents=True, exist_ok=True)
    with open(FILE, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"at": time.strftime("%Y-%m-%d %H:%M"), "text": text, "by": by}) + "\n")
    lines = FILE.read_text(encoding="utf-8").splitlines()
    if len(lines) > KEEP * 1.2:
        FILE.write_text("\n".join(lines[-KEEP:]) + "\n", encoding="utf-8")


def recent(n=50):
    try:
        return [json.loads(x) for x in FILE.read_text(encoding="utf-8").splitlines()[-n:]][::-1]
    except (OSError, ValueError):
        return []


def learn(word):
    """A name or word the player meant (from what Talk did): counted, so the hearing expects it."""
    word = str(word).strip()[:40]
    if not word:
        return
    try:
        counts = collections.Counter(json.loads(WORDS.read_text()))
    except (OSError, ValueError):
        counts = collections.Counter()
    counts[word] += 1
    DATA.mkdir(parents=True, exist_ok=True)
    WORDS.write_text(json.dumps(dict(counts.most_common(200))))


def words(n=10):
    """The player's own words, most used first."""
    try:
        return [w for w, _ in collections.Counter(json.loads(WORDS.read_text())).most_common(n)]
    except (OSError, ValueError):
        return []


def forget():
    """Delete everything kept (Settings)."""
    for f in (FILE, WORDS):
        try:
            f.unlink()
        except OSError:
            pass


def count():
    try:
        return len(FILE.read_text(encoding="utf-8").splitlines())
    except OSError:
        return 0
