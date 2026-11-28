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
# from the player's own mistakes: one of these comes before the tour each day (25 Oct, owner: "nudge them to explore,
# on their mistakes: why, the benefit, and exactly where")
MISTAKE = ("rematch", "lesson", "clock", "endgame", "opening", "calc", "guess")
MAX_DAYS = 2  # any other suggestion: shown on 2 days at most, opened or not (24 Oct: the same rematch again and again)
# Step 2 of docs/CONNECTIONS.md (28 Nov, owner: "everything on the right time", "nothing unused"): a suggestion from the
# player's own data no longer stops for good once its page was opened, or once it was shown on MAX_DAYS days. It rests
# REST_DAYS, then comes back if the player's games still show the need. The tour's introductions still come once.
REST_DAYS = 21
TOUR_TRIES = 4  # an introduction is tried on at most 4 days in all
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
    # first: Knightwise is built around chess.com (30 Oct test: "it never nudges for setting the extension up";
    # it was last of 20, so it came after about ten days)
    ("extension", "maya", "extension", "extension", "no_extension",
     "Do you play on chess.com? I can sit beside you there too. Settings, at the bottom left, sets it up."),
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
     "In Prep, after you look someone up, press Spar: play against their real openings, at their level."),
    ("report", "viktor", "report/week", "report", None,
     "In Progress, press Report: one page about your week, ready to print for a coach or a parent."),
    ("film", "maya", "progress", "film", None,
     "In Progress, press Game of the month: your best win of the month, as a short 3D film."),
    ("wrapped", "maya", "report/month", "report/month", None,
     "In Progress, open Report and press Play it as Wrapped: your chess story in cards, with music."),
    ("talk", "maya", "settings", "settings", None,
     "You can talk to us out loud: press the mic and speak. Settings, at the bottom left, has the switch."),
    # the club (storyline 3.4 and 3.6, 28 Nov)
    ("coaches", "maya", "coaches", "coaches", None,
     "You can meet us properly: click my name, up here in this bubble. Where we're from, and why we coach."),
    ("words", "viktor", "words", "words", None,
     "Chess has its own words. Tap any underlined one for its meaning; all of them are on Chess words, under Explore in Your plan.")
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


def seen(route, day=None):
    """The player opened this page or game: dated, so its suggestion rests REST_DAYS (a new game, or a tour item, is
    never suggested again)."""
    route = str(route or "").strip("/")[:60]
    if not route:
        return
    today = (day or datetime.date.today()).isoformat()
    with _LOCK:
        m = _load()
        _dated(m, today)
        done = m.get("seen", [])
        if route not in done:
            m["seen"] = (done + [route])[-500:]
        on = m["opened_on"]
        on.pop(route, None)
        on[route] = today  # newest last, so the oldest go first when it's trimmed
        m["opened_on"] = dict(list(on.items())[-500:])
        _use(m, route=route, what="opened", day=today)
        _save(m)


def _dated(m, today):
    """Pages opened before dates were kept (1.2 and older) count as opened today, so returns start gradually."""
    if "opened_on" not in m:
        m["opened_on"] = {r: today for r in m.get("seen", [])}


def _use(m, day, what, route=None, kind=None, tour=None):
    """The use record (CONNECTIONS.md step 2): per feature, how often it was brought up and opened, and when last."""
    from coach import features
    fid = features.feature_of(route=route, kind=kind, tour=tour)
    if not fid:
        return
    u = m.setdefault("use", {}).setdefault(fid, {})
    u[what] = u.get(what, 0) + 1
    u[f"last_{what}"] = day


def opened_lately(m, route, today, days=REST_DAYS):
    """Opened within REST_DAYS (this route or anything under it): the coach doesn't bring it up again yet."""
    cutoff = (datetime.date.fromisoformat(today) - datetime.timedelta(days=days)).isoformat()
    return any((r == route or r.startswith(route + "/")) and d > cutoff for r, d in (m.get("opened_on") or {}).items())


# where things are, said in words (23 Oct test: a ring in the app pointed at the wrong place; words can't)
WHERE = {"daily": "It's the first card on Home.", "games": "It's on Home, or in Games.",
         "rematch": "It's in that game's review, in Games.", "progress": "It's in Progress, in the menu.",
         "clockdrill": "In Progress, scroll down to Your clock and press Slow down.", "prep": "It's in Train, under Prep.",
         "course": "It's the card at the top of Your course, in the menu.",
         "endgame": "In Train, open Endgames.", "openings": "In Train, open Opening tree.",
         "calc": "In Train, open In your head.", "practice": "It's Practice, in the menu.",
         "level": "It's in Your level, in the menu.",
         "report": "In Progress, press Report.", "film": "In Progress, press Game of the month.",
         "blindfold": "In Train, open Blindfold.", "words": "It's in Your plan, under Explore: Chess words.",
         "coaches": "Click my name up here, or open Settings: Meet your coaches.", "guess": "In Train, open Guess the move."}


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
    # respect (28 Nov simulation: Punish, Spar, Explore, Ask and the film came back every other day, forever, for a
    # player who opened the page but never used them): shown on MAX_DAYS days lately -> rests REST_DAYS; TOUR_TRIES in
    # all, then only a moment from the player's own data brings it up
    rest = ((today or datetime.date.today()) - datetime.timedelta(days=REST_DAYS)).isoformat()
    left = [x for x in TOUR if not opened(x[3]) and needs.get(x[4], True) and day not in shown.get(x[0], [])
            and len([d for d in shown.get(x[0], []) if d > rest]) < MAX_DAYS and len(shown.get(x[0], [])) < TOUR_TRIES
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


def candidates(place, home, lesson=None, rematch=None, prog=None, games=None, player=None, day=None):
    """Everything worth suggesting now, the most useful first (23 Oct test: "does she have the mindset to suggest
    everything, anywhere?"). place "app" points with a route; "chesscom" with a red-ring route (guide)."""
    from coach import coaches
    app = place == "app"
    out, m = [], _load()
    today = (day or datetime.date.today()).isoformat()
    _dated(m, today)

    def opened(route):  # opened lately: not yet (it comes back after REST_DAYS if the need is still there)
        return opened_lately(m, route, today)

    def add(kind, cid, line, route=None, guide=None):
        if app and route and WHERE.get(route.split("/")[0]):  # in the app she says exactly where it is (no rings there)
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
        if rematch.get("play_on"):  # gave up a game that wasn't lost (28 Nov): play it on from the end
            add("rematch", f"rematch-{g['id']}", f"Your game against {opp}: {rematch.get('say') or 'it was not lost.'} "
                "Play it on from there?", f"rematch/{g['id']}/{rematch['ply']}")
        else:
            add("rematch", f"rematch-{g['id']}", f"Against {opp} it went wrong at move {rematch['move_number']}. "
                "Play it again from there?", f"rematch/{g['id']}/{rematch['ply']}")
    try:  # a new club rank: Viktor brings it up, with the notebook page it opens (step 3.1, 28 Nov)
        from coach import story
        up = story.pending_rank()
    except Exception:
        up = None
    if up:
        add("rank", f"rank-{up['id']}", f"A new rank: {up['rank']}, and a story from my notebook. {up['story']}",
            "level")
    if app:  # the coaches' memories, the club's story moments and "on this day" (storyline 3.3 and 3.5, 28 Nov)
        _club(out, add, home, games, player, prog, day or datetime.date.today(), m)
    for b in (prog or {}).get("badges") or []:  # close to the next badge: a reason to play carefully today
        need = (b.get("next") or 0) - (b.get("current") or 0)
        if b.get("group") == "Habits" and b.get("next") and 1 <= need <= 2:
            add("badge", f"badge-{b['id']}-{b['next']}", f"{need} more {b['what']} and you earn the next "
                f"{b['name']} badge.", "progress")
            break
    try:  # the repertoire re-check: your games moved away from a line (every 50 games and a month at most)
        from coach import repertoire
        old = repertoire.stale(games, player) if games and player else []
    except Exception:
        old = []
    if old and not opened("repertoire"):
        add("repertoire", f"repertoire-{old[0]['name']}", f"Your games have changed: {old[0]['name']}, {old[0]['why']}. "
            "Want new repertoire lines? In Train, open Repertoire.", "repertoire")
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
        why = (lesson.get("why") or "").split(". ")[0].rstrip(".")
        habit = (lesson.get("habit") or "").strip()
        habit = habit if not habit or habit[-1] in ".?!" else habit + "."
        why = f"{why}. " if why else (f"It teaches: {habit} " if habit else "")
        add("lesson", f"lesson-{lesson['title']}"[:80], f"{why}Your next lesson: {lesson['title']}.",
            f"course/{lesson['id']}" if lesson.get("id") else "course")
    _right_time(add, lambda route, days=REST_DAYS: opened_lately(m, route, today, days), day or datetime.date.today(),
                home, games, player)
    out.extend(_more_nerves(add, opened, games, player))
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



STORY = ("rank", "memory", "story", "history", "word")  # the club's own moments: before the day's other things, one a day
TOLD = ("memory", "story", "history", "word")  # said once ever: remembered when said, not when opened


def _club(out, add, home, games, player, prog, day, m):
    try:
        from coach import memories
        said = memories.candidates(home, games, player, day, m)
        clock = memories.clock_memory(prog, day)
        for kind, cid, coach, line, route, _ in said + ([clock] if clock else []):
            add(kind, cid, line, route)
            out[-1]["voice"] = coach
        from coach import words  # a chess word, introduced by a coach (owner, 28 Nov: one at a time)
        for word, coach, line in words.introductions(home, games, player, day)[:1]:
            out.append({"kind": "word", "id": f"word-{word}", "line": line, "voice": coach})
        h = memories.on_this_day(day) if home.get("games") else None
        if h:
            out.append({"kind": "history", "id": h[0], "line": h[1], "voice": "viktor",
                        "action": {"label": "The source", "url": h[2]}})
    except Exception:  # a story is never worth an error
        import logging
        logging.getLogger("knightwise").warning("nudge club", exc_info=True)


# Step 3.2 (28 Nov, owner: "nothing unused"): six of the seven features only the tour used to bring up, each now
# brought at its right time by its own coach, from the player's own data (docs/STORYLINE.md, the moments table). Each one is
# quiet when its data isn't there, and never breaks the other suggestions. (The seventh, Your plan, already had one:
# Home's "Something new for you", coach/coaches.py, from plan.novelty(); features.SPOKEN.)
THREATS = ("walked into a fork or trick", "walked into checkmate")  # moves that missed what they had planned
GUESS_AFTER = 4  # this many in the last 10 checked games: think like them
OWN_VOICE = ("rank", "blindfold", "report", "wrapped")  # lines in Viktor's first person: he says them, on any page
PRACTICE_DUE = 3  # positions due again today before Maya mentions them


def _right_time(add, opened, day, home, games, player):
    import logging
    for moment in (_practice_due, _week_letter, _month_film, _month_wrapped, _blindfold, _guess, _words, _meet):
        try:
            moment(add, opened, day, home, games, player)
        except Exception:  # a suggestion is never worth an error
            logging.getLogger("knightwise").warning("nudge %s", moment.__name__, exc_info=True)


def _practice_due(add, opened, day, home, games, player):
    """Maya: positions from your own mistakes due again today (1, 3, 7... days), when none were practised today."""
    from coach import memory
    if not home.get("games") or memory.today(day=day) or opened("practice", 3):
        return
    due = sum(1 for box, last in memory.boxes().values() if memory.is_due(box, last, day))
    if due >= PRACTICE_DUE:
        add("practice", f"practice-{day.isoformat()}", f"{due} positions from your own mistakes are due again today. "
            "Seen again now, they stick.", "practice")


def _week_letter(add, opened, day, home, games, player):
    """Viktor, on Sunday after a week with games: his short letter about it."""
    if day.weekday() != 6 or opened("report/week", 6):
        return
    this = (home.get("week") or {}).get("this") or {}
    if this.get("games", 0) >= 3:
        y, w, _ = day.isocalendar()
        add("report", f"report-{y}-W{w:02d}", f"Your week is written up: {this['games']} games, and what they say. "
            "My short letter is in your report.", "report/week")


def _month_film(add, opened, day, home, games, player):
    """Maya, in the first days of a month: the month's best win, as a film."""
    from coach import film, insights
    if day.day > 3 or not games or opened("film", 20):
        return
    gid = film.month_game()
    if not gid:
        return
    g = next((x for x in games if insights.game_id(x["url"]) == gid), None)
    them = ""
    if g and player:
        them = (g["black"] if g["white"]["username"].lower() == player else g["white"])["username"]
    add("film", f"film-{day.strftime('%Y-%m')}", f"Your best win of the month{f', against {them},' if them else ''} "
        "deserves to be watched. It's ready as a film.", "film/month")


def _month_wrapped(add, opened, day, home, games, player):
    """Viktor, in the first days of a month with games: the month told as cards."""
    import time
    if day.day > 3 or not games or opened("report/month", 20):
        return
    n = sum(1 for x in games if (x.get("end_time") or 0) >= time.time() - 30 * 86400)
    if n >= 5:
        add("wrapped", f"wrapped-{day.strftime('%Y-%m')}", f"A month of chess, {n} games. I've written it up as "
            "cards: your month as Wrapped.", "report/month")


def _blindfold(add, opened, day, home, games, player):
    """Viktor, once you're a Club player or above: whole games in your head, as he trained as a boy in Berlin."""
    from coach import story
    told = story._load().get("told")
    if not games or not isinstance(told, int) or told < 1 or opened("blindfold"):
        return
    rank = story.RANKS[story.ORDER[min(told, len(story.ORDER) - 1)]]
    add("blindfold", "blindfold", f"You're a {rank} now. As a boy in Berlin I played whole games in my head. Blindfold "
        "trains it, from your own games.", "blindfold")


def _guess(add, opened, day, home, games, player):
    """Maya: you keep walking into what they had planned, and this week's Guess the move isn't tried yet."""
    from coach import guess, insights, maia
    if not games or not player or opened("guess", 6) or not maia.enabled():
        return
    g = guess._load()
    if g.get("week") == guess.week(day) and g.get("tries"):
        return
    moves = insights._moves()
    recent = [x for x in sorted(games, key=lambda x: x.get("end_time") or 0, reverse=True) if x.get("url") in moves][:10]
    n = sum(1 for x in recent for r in moves[x["url"]] if r.get("pattern") in THREATS)
    if len(recent) >= 5 and n >= GUESS_AFTER:
        add("guess", f"guess-{guess.week(day)}", f"{n} times in your last {len(recent)} games you walked into something "
            "they had planned. Guess the move: five minutes of thinking like them.", "guess")

def _words(add, opened, day, home, games, player):
    """Viktor: you've started tapping chess words for their meaning; the whole list is on one page."""
    from coach import words
    n = words.count_looked()
    if n >= words.LOOKED_UP and not opened("words"):
        add("words", "words", f"You've looked up {n} chess words. All {len(words.WORDS)} are on one page, with what "
            "they mean.", "words")


def _meet(add, opened, day, home, games, player):
    """Maya, after two days in the club: the coaches introduce themselves properly."""
    from coach import memories
    if home.get("games") and (day - memories.joined(day)).days >= 2 and not opened("coaches", 3650):
        add("meet", "meet", "We haven't been introduced properly. Meet your coaches: where we're from, and why we "
            "coach.", "coaches")


def _more_nerves(add, opened, games, player):
    """Endgames, the Opening tree and In your head, each linked to the mistake it trains (25 Oct). Never breaks the
    suggestions: anything missing means no suggestion of that kind."""
    if not games or not player:
        return []
    try:
        from coach import course, insights, ladder, scout
        moves = insights._moves()
        recent = sorted(games, key=lambda x: x.get("end_time") or 0)[-20:]
        rows = {x.get("url"): moves.get(x.get("url"), []) for x in recent if x.get("url")}
        stalemates = sum(1 for rs in rows.values() for r in rs if r.get("pattern") == ladder.STALEMATE)
        if stalemates and not opened("endgame/queen"):
            add("endgame", "endgame-queen", f"You stalemated {stalemates} won game{'s' if stalemates > 1 else ''} in your "
                "last 20. Mate with king and queen ends that.", "endgame/queen")
        else:
            recent = [x for x in recent if x.get("url")]
            winning = [x for x in recent if any(r["cp_before"] >= ladder.WINNING for r in rows[x["url"]])]
            conv = ladder._conversion(recent, rows, {"player": insights._player() or player})
            if len(winning) >= 3 and conv is not None and conv < 70 and not opened("endgame/pawn"):
                add("endgame", "endgame-pawn", f"You won {round(conv)}% of your last games where you were winning. "
                    "Win with king and pawn trains finishing them.", "endgame/pawn")
        worst = scout.worst_opening(sorted(games, key=lambda x: x.get("end_time") or 0)[-60:], player, least=5)
        if worst and worst["score"] <= 35:
            add("opening", f"opening-{worst['name']}"[:80], f"You score {worst['score']}% with the {worst['name']} "
                f"({worst['games']} games). The Opening tree shows where those games go wrong.", "openings")
        tricks = next((r for r in course.course()["lessons"] if r["id"] == "tac-tricks"), None)
        if tricks and tricks.get("rate") and tricks.get("goal") is not None and tricks["rate"] > tricks["goal"] \
                and not opened("calc"):
            add("calc", "calc", f"Tricks a few moves deep cost you {tricks['rate']} a game lately. In your head trains "
                "seeing them before you move.", "calc")
    except Exception:  # a suggestion is never worth an error
        import logging
        logging.getLogger("knightwise").warning("nudge nerves", exc_info=True)
    return []


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
    no_games = not home.get("games")  # a brand-new account: no suggestions from games, but the tour still shows the app (26 Oct)
    if no_games and place != "app":
        return None
    now = now or time.time()
    with _LOCK:
        m = _load()
        _dated(m, today)  # kept with this save, so the gradual start is stamped once, not every day
        shown = m.get("shown", {}) if m.get("day") == today else {}
        mine = shown.get(place, [])
        kinds = m.get("kinds", {})
        before = set(kinds.get(yesterday, []))
        ever = m.get("ever", {})  # suggestion id -> the days it was shown
        rest = (day - datetime.timedelta(days=REST_DAYS)).isoformat()  # shown on MAX_DAYS days: it rests, then may return
        options = [] if no_games else [c for c in candidates(place, home, lesson, rematch, prog, games, player, day)
                   if c["id"] not in mine and c.get("guide") != section
                   and (c["kind"] in DAILY or len([d for d in ever.get(c["id"], []) if d != today and d > rest]) < MAX_DAYS)]  # not "this way to puzzles" on that page
        options.sort(key=lambda c: c["kind"] in before and c["kind"] not in DAILY)  # stable: yesterday's kinds go last
        tour = m.get("tour") or {}
        used = len(mine) + (tour.get("n", 0) if place == "app" and tour.get("day") == today else 0)
        if used >= A_DAY:  # 3 a day in all, new things included: a heavy user sees 3, someone who opens it once sees 1
            return None
        spaced = now - (m.get("at") or {}).get(place, 0) >= GAP  # never two suggestions together
        options = [c for c in options if spaced or c["kind"] == "game"]
        new_thing = tour_next(coach, day, now, extension) if place == "app" and spaced else None
        # the day's own things first (a new game, the 5 minutes), then one from their own mistakes, then something new
        mistakes = [c for c in options if c["kind"] in MISTAKE and c["kind"] not in before]  # a new kind each day
        mistake_today = any(k in MISTAKE for k in kinds.get(today, []))
        stories = [c for c in options if c["kind"] in STORY]
        story_today = any(k in STORY for k in kinds.get(today, []))
        if options and options[0]["kind"] in DAILY:
            c = options[0]
        elif stories and not story_today:
            c = stories[0]
        elif mistakes and not mistake_today:
            c = mistakes[0]
        else:
            c = new_thing or (options[0] if options else None)
        if not c:
            return None
        if c["kind"] == "tour":
            _tour_shown(m, c["id"][len("tour-"):], today, now)
            m["shown"] = shown  # today's list only (a new day starts it again)
            _use(m, today, "brought", tour=c["id"][len("tour-"):])
        else:
            _use(m, today, "brought", kind=c["kind"])
            if c["kind"] == "word":
                from coach import words
                words.introduced(c["id"][len("word-"):], day)
            elif c["kind"] in TOLD:
                from coach import memories
                memories.told(c["id"], day)
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
        if c["kind"] in OWN_VOICE and not c.get("voice"):  # said in a coach's own words ("my notebook", "as a boy in Berlin I"): that coach says it
            from coach import features
            f = next((x for x in features.FEATURES if x["id"] == features.feature_of(kind=c["kind"])), None)
            c = {**c, "voice": f["coach"] if f else None}
        return c
