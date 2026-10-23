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
MAX_DAYS = 2  # any other suggestion: shown on 2 days at most, opened or not (24 Oct: the same rematch again and again)
CHESSCOM_SECTIONS = ("home", "puzzles", "lessons", "progress")  # never play, review or someone's profile
_LOCK = threading.Lock()

# The tour (23 Oct test: "the coaches should navigate the user through every feature"): everything Knightwise has,
# brought one at a time by the coach it belongs to, a few a day with space between them, until each one has been
# opened. (id, coach, where to point, opened when the player has been to, needs, line). "where" can end in
# "@selector": the ring goes on to that thing once the page is open.
TOUR_A_DAY = 3  # new things a day
IN_HER_VOICE = {"ask", "extension"}  # lines that say "I": only the coach they belong to says them
TOUR_GAP = 20 * 60  # seconds between two of them
GAP = 10 * 60  # seconds between any two suggestions in the app ("not together"); a new game is never held back
TOUR = [
    ("level", "viktor", "level", "level", None,
     "Do you know your level? Open Your level in the menu: five steps from beginner to 2,000, each counted in your real games."),
    ("practice", "maya", "practice", "practice", None,
     "Practice, in the menu, is built from your own mistakes. Each position comes back after 1, 3 and 7 days until it sticks."),
    ("plan", "viktor", "plan", "plan", None,
     "Open Your plan in the menu: a few cards picked for you from thousands of Lichess puzzles and openings."),
    ("ask", "maya", "home@.askbar", "ask", None,
     "You can ask me anything about your chess: type it in the box at the bottom of Home. Why you lose, what to practise, anything."),
    ("blindfold", "viktor", "blindfold", "blindfold", None,
     "Something fun: in Train, open Blindfold. A game is read out and you follow it in your head. It sharpens seeing ahead."),
    ("course", "viktor", "course", "course", None,
     "Open Your course in the menu: lessons in order, each one passed only when your games show it."),
    ("explore", "viktor", "plan@.explore-box", "plan/explore", "plan",
     "Want something specific? In Your plan, type any opening or tactic into the Explore bar under the cards."),
    ("repertoire", "viktor", "repertoire", "repertoire", None,
     "In Train, open Repertoire: the openings you play, as lines you can drill until they're automatic."),
    ("guess", "viktor", "guess", "guess", None,
     "In Train, try Guess the move: five real positions a week. What would players of that rating play?"),
    ("progress", "viktor", "progress", "progress", None,
     "Open Progress in the menu: your week as a story, and badges you earn in real games."),
    ("done", "viktor", "plan@.plan-done-sec", "plan/done", "has_done",
     "Everything you finish is kept in Done, at the bottom of Your plan. Play any of it again whenever you like."),
    ("prep", "viktor", "prep", "prep", None,
     "Before a game, open Prep in Train: type a chess.com name and Stockfish works out how to beat them."),
    ("punish", "maya", "prep", "punish", "prep",
     "In Prep, after you look someone up, press Punish: their real mistakes, as puzzles for you to solve."),
    ("calc", "viktor", "calc", "calc", None,
     "In Train, try In your head: put a whole line in as arrows before the board moves. It trains calculation."),
    ("endgames", "viktor", "endgames", "endgames", None,
     "In Train, open Endgames: the endings every player must know, against perfect defence."),
    ("openings", "viktor", "openings", "openings", None,
     "In Train, the Opening tree shows where your games go well and where they go wrong, from move one."),
    ("spar", "viktor", "prep", "spar", "prep",
     "In Train, Spar lets you play the opening against someone's real moves from their own games."),
    ("report", "viktor", "report/week", "report", None,
     "In Progress, press Report: one page about your week, ready to print for a coach or a parent."),
    ("film", "maya", "progress", "film", None,
     "In Progress, press Game of the month: your best win of the month, as a short 3D film."),
    ("wrapped", "maya", "report/month", "report/month", None,
     "In Progress, open Report and press Play it as Wrapped: your chess story in cards, with music."),
    ("talk", "maya", "settings", "settings", None,
     "You can talk to us out loud: press the mic and speak. Settings, at the bottom left, has the switch."),
    ("extension", "maya", "extension", "extension", "no_extension",
     "Do you play on chess.com? I can sit beside you there too. Settings, at the bottom left, sets it up."),
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


# where things are, said in words (23 Oct test: a ring in the app pointed at the wrong place; words can't)
WHERE = {"daily": "It's the first card on Home.", "games": "It's on Home, or in Games.",
         "rematch": "It's in that game's review, in Games.", "progress": "It's in Progress, in the menu.",
         "clockdrill": "In Progress, press Slow down.", "prep": "It's in Train, under Prep.",
         "course": "It's in Your course, in the menu."}


def tour_next(coach=None, today=None, now=None, extension=False):
    """The next new thing to show, or None: at most TOUR_A_DAY a day, TOUR_GAP apart; never one already opened; one
    shown before but not opened can come again on another day, after the ones never shown; the speaking coach's own
    first when there's a choice."""
    m = _load()
    day = (today or datetime.date.today()).isoformat()
    now = now or time.time()
    t = m.get("tour", {})
    if t.get("day") == day and (t.get("n", 0) >= TOUR_A_DAY or now - t.get("at", 0) < TOUR_GAP):
        return None
    done = set(m.get("seen", []))
    opened = lambda key: any(d == key or d.startswith(key + "/") for d in done)
    from coach import plan
    needs = {None: True, "plan": opened("plan"), "no_extension": not extension,
             "has_done": bool(plan._memory().get("done"))}
    shown = t.get("shown", {})
    needs["prep"] = opened("prep")
    left = [x for x in TOUR if not opened(x[3]) and needs.get(x[4], True) and day not in shown.get(x[0], [])
            and not (x[0] in IN_HER_VOICE and coach and coach != x[1])]  # "I can…" only from the coach it's about
    left.sort(key=lambda x: len(shown.get(x[0], [])))  # never shown first; stable, so the tour's order otherwise
    if not left:
        return None
    first = left[:3]
    x = next((y for y in first if y[1] == coach), first[0]) if coach else first[0]
    return {"kind": "tour", "id": f"tour-{x[0]}", "line": x[5], "route": x[2], "coach": x[1]}


def _tour_shown(m, tid, day, now):
    t = m.get("tour", {})
    if t.get("day") != day:
        t = {**t, "day": day, "n": 0}
    t["n"] = t.get("n", 0) + 1
    t["at"] = now
    t.setdefault("shown", {}).setdefault(tid, []).append(day)
    m["tour"] = t


def candidates(place, home, lesson=None, rematch=None, prog=None, games=None, player=None):
    """Everything worth suggesting now, the most useful first (23 Oct test: "does she have the mindset to suggest
    everything, anywhere?"). place "app" points with a route; "chesscom" with a red-ring route (guide)."""
    from coach import coaches
    app = place == "app"
    out, done = [], set(_load().get("seen", []))

    def opened(route):  # done or seen: never again
        return any(d == route or d.startswith(route + "/") for d in done)

    def add(kind, cid, line, route=None, guide=None):
        if app and route and WHERE.get(route.split("/")[0]):  # in the app she says where it is (no rings there)
            line = f"{line} {WHERE[route.split('/')[0]]}"
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
    if not app:  # a warm-up before rated games, at your level (in the app, the tour brings new things)
        add("bots", "bots", "Before a rated game, warm up against a bot at your level. I'll show you where.", guide="bots")
    return out


def pick(place, section, home=None, today=None, lesson=None, rematch=None, prog=None, games=None, player=None,
         coach=None, now=None, extension=False):
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
    now = now or time.time()
    with _LOCK:
        m = _load()
        shown = m.get("shown", {}) if m.get("day") == today else {}
        mine = shown.get(place, [])
        kinds = m.get("kinds", {})
        before = set(kinds.get(yesterday, []))
        ever = m.get("ever", {})  # suggestion id -> the days it was shown
        options = [c for c in candidates(place, home, lesson, rematch, prog, games, player)
                   if c["id"] not in mine and c.get("guide") != section
                   and (c["kind"] in DAILY or len([d for d in ever.get(c["id"], []) if d != today]) < MAX_DAYS)]  # not "this way to puzzles" on that page
        options.sort(key=lambda c: c["kind"] in before and c["kind"] not in DAILY)  # stable: yesterday's kinds go last
        if len(mine) >= A_DAY:
            options = []
        spaced = now - (m.get("at") or {}).get(place, 0) >= GAP  # never two suggestions together
        options = [c for c in options if spaced or c["kind"] == "game"]
        new_thing = tour_next(coach, day, now, extension) if place == "app" and spaced else None
        # the day's own things first (a new game, the 5 minutes), then something new, then the rest
        if options and options[0]["kind"] in DAILY:
            c = options[0]
        else:
            c = new_thing or (options[0] if options else None)
        if not c:
            return None
        if c["kind"] == "tour":
            _tour_shown(m, c["id"][len("tour-"):], today, now)
            m["shown"] = shown  # today's list only (a new day starts it again)
        else:
            m["shown"] = {**shown, place: mine + [c["id"]]}
            days = ever.get(c["id"], [])
            m["ever"] = {**ever, c["id"]: days if today in days else (days + [today])[-MAX_DAYS - 1:]}
        m["day"] = today
        m["at"] = {**(m.get("at") or {}), place: now}
        m["kinds"] = {d: k for d, k in kinds.items() if d in (today, yesterday)}
        m["kinds"][today] = m["kinds"].get(today, []) + [c["kind"]]
        _save(m)
        if c.get("guide"):
            from coach import coaches
            c = {**c, "route_guide": coaches.guide(c["guide"])["guide"]}
        return c
