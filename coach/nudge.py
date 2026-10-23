"""The coach's one new thing for the page you just opened: she comes up by herself and points at it (23 Oct test:
"a teacher comes up and teaches every day, because she has a lot of knowledge"). No AI: the player's own games and
the app's own data decide, so it works for everyone, with or without a key.

Each suggestion shows at most once a day, and no more than A_DAY a day in each place (the app, chess.com), so she
never nags. Never in a game against a real person, and never in a review (it has its own work)."""
import datetime
import json
import threading

from coach.paths import DATA

FILE = DATA / "nudges.json"  # what was suggested today, and which pages and games the player has already opened
A_DAY = 3
CHESSCOM_SECTIONS = ("home", "puzzles", "lessons", "progress")  # never play, review or someone's profile
_LOCK = threading.Lock()

# things in Knightwise worth trying once, in this order; the first one never opened is offered (one at a time)
UNTRIED = [
    ("guess", "Something you haven't tried: guess what players at your rating play. Five positions, a few minutes."),
    ("blindfold", "Something new: Blindfold. I read out a game and you follow it in your head. Great for seeing ahead."),
    ("endgames", "Have you tried the endgame trainer? The endings every player must know, learned once for good."),
    ("prep", "Before your next game, try Prep: type a chess.com name and see how they open and how they lose."),
    ("calc", "Try In your head: put a whole line in as arrows before the board moves. It trains seeing ahead."),
    ("openings", "Your opening tree shows where your games go well and where they go wrong, from move one."),
]


def _load():
    try:
        return json.loads(FILE.read_text())
    except (OSError, ValueError):
        return {}


def _save(m):
    try:
        FILE.parent.mkdir(parents=True, exist_ok=True)
        FILE.write_text(json.dumps(m))
    except OSError:
        pass


def seen(route):
    """The player opened this page or game (so a new game, or something untried, isn't suggested again)."""
    route = str(route or "").strip("/")[:60]
    if not route:
        return
    with _LOCK:
        m = _load()
        done = m.get("seen", [])
        if route not in done:
            m["seen"] = (done + [route])[-500:]
            _save(m)


def candidates(place, home, lesson=None, rematch=None):
    """Everything worth suggesting now, the most useful first. place: "app" (routes) or "chesscom" (red-ring routes)."""
    from coach import coaches
    out, done = [], set(_load().get("seen", []))
    g = home.get("last_game") or {}
    opp = g.get("opponent", "")
    if g.get("checked") and f"games/{g['id']}" not in done:  # a new game nobody has looked at yet
        n = g.get("moments") or 0
        if place == "app":
            line = (f"New game in, against {opp}: {n} key moment{'s' if n != 1 else ''} to look at." if n
                    else f"New game in, against {opp}, and a clean one. Have a quick look.")
            out.append({"id": f"game-{g['id']}", "line": line, "route": f"games/{g['id']}"})
        else:
            out.append({"id": f"game-{g['id']}", "line": f"Your game against {opp} is in. Open it from your game "
                        "history and I'll go through it with you on this board.", "guide": "archive"})
    daily = home.get("daily") or {}
    if place == "app" and home.get("games") and not daily.get("done_today"):
        streak = daily.get("streak") or 0
        out.append({"id": "daily", "route": "daily",
                    "line": f"Today's 5 minutes are waiting. Keep your {streak}-day streak going." if streak > 1
                    else "Today's 5 minutes are waiting: three positions from your own games."})
    if place == "app" and rematch and g.get("checked") and g.get("result") in ("loss", "draw"):
        out.append({"id": f"rematch-{g['id']}", "route": f"rematch/{g['id']}/{rematch['ply']}",
                    "line": f"Against {opp} it went wrong at move {rematch['move_number']}. Play it again from there?"})
    if place == "app" and lesson:
        out.append({"id": f"lesson-{lesson['title']}"[:80], "route": "course",
                    "line": f"Your next lesson: {lesson['title']}."})
    if place == "app":
        for route, line in UNTRIED:
            if route not in done:
                out.append({"id": f"try-{route}", "line": line, "route": route})
                break
    if place == "chesscom":
        f = (home.get("focus") or {}).get("pattern")
        pick = coaches.CHESSCOM_FOR.get(f)
        if pick:
            where = {"puzzles": "chess.com's puzzles", "lessons": "chess.com's lessons"}.get(pick[0], pick[0])
            out.append({"id": f"cc-{pick[0]}", "guide": pick[0],
                        "line": f"Something for your habit: {where}. I'll show you the way."})
    return out


def pick(place, section, home=None, today=None, lesson=None, rematch=None):
    """The one thing to point at on this page now, or None. Remembered, so it shows once a day."""
    if place == "chesscom" and section not in CHESSCOM_SECTIONS:
        return None
    if place == "app" and section == "review":
        return None
    today = (today or datetime.date.today()).isoformat()
    if home is None:
        from coach import insights
        home = insights.home()
    if not home.get("games"):
        return None
    with _LOCK:
        m = _load()
        shown = m.get("shown", {}) if m.get("day") == today else {}
        mine = shown.get(place, [])
        if len(mine) >= A_DAY:
            return None
        for c in candidates(place, home, lesson, rematch):
            if c["id"] not in mine and c.get("guide") != section:  # not "this way to puzzles" on the puzzles page
                m["day"], m["shown"] = today, {**shown, place: mine + [c["id"]]}
                _save(m)
                if c.get("guide"):
                    from coach import coaches
                    c = {**c, "route_guide": coaches.guide(c["guide"])["guide"]}
                return c
    return None
