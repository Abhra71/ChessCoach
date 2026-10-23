"""The coach's one new thing for the page you just opened: she comes up by herself and points at it (23 Oct test:
"a teacher comes up and teaches every day, because she has a lot of knowledge"). No AI: the player's own games and
the app's own data decide, so it works for everyone, with or without a key.

One list for both places (the app and chess.com): something that lives in the other place gets one button there.
Each suggestion shows at most once a day, no more than A_DAY a day in each place, and a kind shown yesterday goes to
the back. Anything already done or opened is never suggested again. Never in a game against a real person, and never
in a review (it has its own work)."""
import datetime
import json
import threading
import time

from coach.paths import DATA

FILE = DATA / "nudges.json"  # what was suggested today, and which pages and games the player has already opened
A_DAY = 3
NEW_FOR = 3 * 86400  # seconds a finished game counts as new
DAILY = ("game", "daily")  # worth saying every day: never sent to the back for variety
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


def candidates(place, home, lesson=None, rematch=None, prog=None, games=None, player=None):
    """Everything worth suggesting now, the most useful first (23 Oct test: "does she have the mindset to suggest
    everything, anywhere?"). place "app" points with a route; "chesscom" with a red-ring route (guide)."""
    from coach import coaches
    app = place == "app"
    out, done = [], set(_load().get("seen", []))

    def opened(route):  # done or seen: never again
        return any(d == route or d.startswith(route + "/") for d in done)

    def add(kind, cid, line, route=None, guide=None):
        c = {"kind": kind, "id": cid, "line": line}
        if app and route:
            c["route"] = route
        elif not app and guide:
            c["guide"] = guide
        elif not app and route:  # it lives in the app: one button on chess.com
            c["action"] = {"label": "Open Knightwise", "app": route}
        out.append(c)

    g = home.get("last_game") or {}
    opp = g.get("opponent", "")
    fresh = time.time() - (g.get("end_time") or 0) < NEW_FOR  # only a game from the last few days is "new"
    if g.get("checked") and fresh and not opened(f"games/{g['id']}"):  # a new game nobody has looked at yet
        n = g.get("moments") or 0
        if app:
            add("game", f"game-{g['id']}", f"New game in, against {opp}: {n} key moment{'s' if n != 1 else ''} to "
                "look at." if n else f"New game in, against {opp}, and a clean one. Have a quick look.", f"games/{g['id']}")
        else:
            add("game", f"game-{g['id']}", f"Your game against {opp} is in. Open it from your game history and I'll "
                "go through it with you on this board.", guide="archive")
    daily = home.get("daily") or {}
    if home.get("games") and not daily.get("done_today"):
        streak = daily.get("streak") or 0
        line = (f"Today's 5 minutes are waiting. Keep your {streak}-day streak going." if streak > 1
                else "Today's 5 minutes are waiting: three positions from your own games.")
        add("daily", "daily", line + ("" if app else " They're in Knightwise."), "daily")
    if rematch and g.get("checked") and g.get("result") in ("loss", "draw") and not opened(f"rematch/{g['id']}"):
        add("rematch", f"rematch-{g['id']}", f"Against {opp} it went wrong at move {rematch['move_number']}. "
            "Play it again from there?", f"rematch/{g['id']}/{rematch['ply']}")
    for b in (prog or {}).get("badges") or []:  # close to the next badge: a reason to play carefully today
        need = (b.get("next") or 0) - (b.get("current") or 0)
        if b.get("group") == "Habits" and b.get("next") and 1 <= need <= 2:
            add("badge", f"badge-{b['id']}-{b['next']}", f"{need} more {b['what']} and you earn the next "
                f"{b['name']} badge.", "progress")
            break
    clk = (prog or {}).get("clock") or {}
    if clk.get("big", 0) >= 8 and clk.get("fast", 0) / clk["big"] >= 0.3 and not opened("clockdrill"):
        add("clock", "clock", f"{clk['fast']} of your {clk['big']} biggest mistakes lately were played in a rush. "
            "The slow-down drill trains it.", "clockdrill")
    if games and player:  # someone you keep playing: know them before the next one
        cutoff, count = time.time() - 60 * 86400, {}
        for x in games:
            if x["end_time"] >= cutoff:
                them = x["black"] if x["white"]["username"].lower() == player else x["white"]
                count[them["username"]] = count.get(them["username"], 0) + 1
        often = [(n, who) for who, n in count.items() if n >= 3 and not opened(f"prep/{who.lower()}")]
        if often:
            n, who = max(often)
            add("prep", f"prep-{who.lower()}", f"You've played {who} {n} times lately. Prep shows how they open and "
                "how their games end.", f"prep/{who.lower()}")
    if lesson and not (lesson.get("id") and opened(f"course/{lesson['id']}")):
        add("lesson", f"lesson-{lesson['title']}"[:80], f"Your next lesson: {lesson['title']}.",
            f"course/{lesson['id']}" if lesson.get("id") else "course")
    wk = home.get("week") or {}
    this, last = wk.get("this") or {}, wk.get("last") or {}
    if this.get("games", 0) >= 3 and last.get("games", 0) >= 3 and \
            this["pieces"] / this["games"] < last["pieces"] / last["games"]:
        add("week", f"week-{this['games']}", "Fewer pieces given away this week than last. Your Progress page shows it.",
            "progress")
    cc = coaches.CHESSCOM_FOR.get((home.get("focus") or {}).get("pattern"))
    if cc:  # chess.com's own place for the habit: the red ring there, a link out from the app
        where = {"puzzles": "chess.com's puzzles", "lessons": "chess.com's lessons"}.get(cc[0], cc[0])
        if app:
            out.append({"kind": "chesscom", "id": f"cc-{cc[0]}", "line": f"For your habit, try {where} too.",
                        "action": {"label": cc[1].split(":")[0], "url": coaches.ROUTES[cc[0]]["url"]}})
        else:
            add("chesscom", f"cc-{cc[0]}", f"Something for your habit: {where}. I'll show you the way.", guide=cc[0])
    if app:
        for route, line in UNTRIED:
            if not opened(route):
                add("try", f"try-{route}", line, route)
                break
    else:  # a warm-up before rated games, at your level
        add("bots", "bots", "Before a rated game, warm up against a bot at your level. I'll show you where.", guide="bots")
    return out


def pick(place, section, home=None, today=None, lesson=None, rematch=None, prog=None, games=None, player=None):
    """The one thing to point at on this page now, or None. Remembered, so it shows once a day; a kind shown
    yesterday goes to the back, so she doesn't say the same sort of thing two days running."""
    if place == "chesscom" and section not in CHESSCOM_SECTIONS:
        return None
    if place == "app" and section == "review":
        return None
    day = today or datetime.date.today()
    today, yesterday = day.isoformat(), (day - datetime.timedelta(days=1)).isoformat()
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
        kinds = m.get("kinds", {})
        before = set(kinds.get(yesterday, []))
        options = [c for c in candidates(place, home, lesson, rematch, prog, games, player)
                   if c["id"] not in mine and c.get("guide") != section]  # not "this way to puzzles" on that page
        options.sort(key=lambda c: c["kind"] in before and c["kind"] not in DAILY)  # stable: yesterday's kinds go last
        if not options:
            return None
        c = options[0]
        m["day"], m["shown"] = today, {**shown, place: mine + [c["id"]]}
        m["kinds"] = {d: k for d, k in kinds.items() if d in (today, yesterday)}
        m["kinds"][today] = m["kinds"].get(today, []) + [c["kind"]]
        _save(m)
        if c.get("guide"):
            from coach import coaches
            c = {**c, "route_guide": coaches.guide(c["guide"])["guide"]}
        return c
