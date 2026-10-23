"""Today's challenge: five minutes a day. One position from your own games, one puzzle on today's theme and the
first moves of your opening. The same three all day; a gentle streak that forgives one missed day.
"""
import json
import random
from datetime import date, timedelta

from coach import memory, plan
from coach.paths import DATA

FILE = DATA / "daily.json"
OPENING_MOVES = 3  # your first three moves of the opening are enough for a daily warm-up


def _memory():
    try:
        return json.loads(FILE.read_text())
    except (OSError, ValueError):
        return {"days": []}


def streak(days, today):
    """Days in the current run. One missed day between two done days doesn't break it; two do.
    The run is still alive if the last done day was today, yesterday or the day before."""
    done = sorted({date.fromisoformat(d) for d in days}, reverse=True)
    if not done or (today - done[0]).days > 2:
        return 0
    n = 1
    for newer, older in zip(done, done[1:]):
        if (newer - older).days > 2:
            break
        n += 1
    return n


def _own(focus, rng, today=None):
    """One of your own positions, one you didn't answer on an earlier day (in Practice or here), so it doesn't repeat while
    there are new ones (23 Oct test: "same puzzles shouldn't repeat")."""
    path = DATA / "drills.json"
    try:
        own = [d for d in json.loads(path.read_text()) if d.get("kind") == "game"]
    except (OSError, ValueError):
        return None
    done = memory.seen_before(today)  # earlier days only: today's set must not change once you answer it
    for pool in ([d for d in own if d.get("pattern") == focus and d["id"] not in done], [d for d in own if d["id"] not in done],
                 [d for d in own if d.get("pattern") == focus], own):
        if pool:
            return rng.choice(pool)
    return None


def challenge(home, games=None, engine=None, today=None):
    today = today or date.today()
    rng = random.Random("daily" + today.isoformat())
    focus = (home.get("focus") or {}).get("pattern") or plan.HANG
    themes = plan.THEMES_FOR.get(focus, plan.ROTATION)
    theme = themes[today.toordinal() % len(themes)]
    items = []
    own = _own(focus, rng, today)
    if own:
        items.append({**own, "intro": "From your own game. " + own["intro"]})
    puzzle = plan._puzzles(theme, home.get("rating"), rng, avoid=memory.seen_before(today))[:1]
    if puzzle:
        items.append({**puzzle[0], "intro": f"Today's idea: {plan.THEME_NAME[theme]}. {puzzle[0]['intro']}"})
    if engine is not None and games:
        lesson = plan.opening_lesson(games, home["player"], focus in (plan.HANG, plan.FORK), engine, set())
        if lesson:
            drill = dict(lesson["drills"][0])
            drill["steps"] = drill["steps"][:OPENING_MOVES]
            drill["intro"] = f"Your opening: the first moves of the {lesson['name']}."
            items.append(drill)
    days = _memory().get("days", [])
    return {"date": today.isoformat(), "theme": plan.THEME_NAME[theme], "drills": items,
            "done_today": today.isoformat() in days, "streak": streak(days, today), "total": len(set(days)),
            "week": week_dots(days, today)}


def done(today=None):
    today = today or date.today()
    mem = _memory()
    days = sorted(set(mem.get("days", [])) | {today.isoformat()})
    mem["days"] = days[-400:]
    FILE.parent.mkdir(parents=True, exist_ok=True)
    FILE.write_text(json.dumps(mem))
    return {"streak": streak(days, today), "total": len(days)}


def week_dots(days, today):
    """The last seven days, oldest first: True where the challenge was done."""
    have = set(days)
    return [(today - timedelta(days=i)).isoformat() in have for i in range(6, -1, -1)]
