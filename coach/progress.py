"""Progress: the story of your week, and badges earned in your real chess.com games.

Every number comes from your games and the engine's checks; nothing here is made up or estimated.
"""
import collections
import re
import time
from datetime import datetime

from coach import daily, insights
from coach.review import ABOUT, LOSING_MATERIAL, biggest

HANG, FORK, MATED = "left a piece hanging", "walked into a fork or trick", "walked into checkmate"
FREE, MISSED_MATE, STALEMATE = "missed a free capture", "missed a checkmate", "stalemated a won game"
TIER = ["Bronze", "Silver", "Gold"]
# 50 badges. "run": games in a row without a habit; "count": a number from your games or your training. Each one says
# something true about your chess when it's earned (23 Oct test: "the user will know they are good at something").
BADGES = [
    ("Habits", "safe", "Safe pieces", "hang", "games in a row without a hanging piece", ("run", HANG), [3, 5, 10]),
    ("Habits", "forkproof", "Fork-proof", "fork", "games in a row without walking into a fork", ("run", FORK), [5, 10, 20]),
    ("Habits", "king", "Safe king", "mate", "games in a row without walking into mate", ("run", MATED), [10, 20, 40]),
    ("Habits", "eagle", "Eagle eye", "capture", "games in a row without missing a free piece", ("run", FREE), [5, 10, 20]),
    ("Habits", "finisher", "Finisher", "mate", "games in a row without missing a mate", ("run", MISSED_MATE), [10, 20, 40]),
    ("Habits", "closer", "Closer", "draw", "games in a row without stalemating a win", ("run", STALEMATE), [10, 25, 50]),
    ("Clean play", "clean", "Clean games", "capture", "games with no big mistake", ("count", "clean"), [1, 5, 15]),
    ("Clean play", "steady", "Steady hand", "hang", "games without giving a piece away", ("count", "steady"), [5, 20, 50]),
    ("Clean play", "longwin", "Long game", "progress", "wins in games of 40 moves or more", ("count", "longwin"), [3, 10, 30]),
    ("Results", "wins", "Winner", "medal", "games won", ("count", "wins"), [10, 50, 150]),
    ("Results", "streak", "On a roll", "flame", "wins in a row, best run", ("count", "onaroll"), [2, 3, 5]),
    ("Results", "mates", "Checkmater", "mate", "wins by checkmate", ("count", "mates"), [5, 20, 50]),
    ("Results", "giant", "Giant slayer", "up", "wins against someone rated 100 or more above you", ("count", "giant"), [1, 5, 15]),
    ("Results", "black", "Dark side", "pawn", "wins with the black pieces", ("count", "black"), [5, 20, 60]),
    ("Results", "allround", "All-rounder", "games", "time controls you've won in", ("count", "allround"), [2, 3, 4]),
    ("Results", "games", "Regular", "games", "games played", ("count", "games"), [25, 100, 300]),
    ("Practice", "daily", "Daily habit", "bolt", "days of Today's 5 minutes", ("count", "daily"), [3, 7, 30]),
    ("Practice", "right", "Sharp", "practice", "positions solved on the first try", ("count", "right"), [10, 50, 200]),
    ("Practice", "learned", "Memory", "plan", "positions learned for good", ("count", "learned"), [5, 20, 50]),
    ("Practice", "lessons", "Student", "plan", "lessons finished in Your plan", ("count", "lessons"), [1, 5, 15]),
    # 30 more (23 Oct): the moments that decide games, accuracy, the clock, rating, openings, and training that shows
    ("Big moments", "comeback", "Comeback", "up", "wins from a losing position (your chance under a quarter)", ("count", "comeback"), [3, 10, 30]),
    ("Big moments", "survivor", "Survivor", "draw", "draws saved from a losing position", ("count", "survivor"), [2, 5, 15]),
    ("Big moments", "converter", "Converter", "medal", "wins where you were clearly ahead by move 20 and never let it slip", ("count", "converter"), [10, 30, 75]),
    ("Big moments", "grinder", "Endgame grinder", "pawn", "wins that went down to an endgame", ("count", "grinder"), [5, 15, 40]),
    ("Big moments", "promotion", "Promotion", "up", "wins where you promoted a pawn", ("count", "promotion"), [2, 8, 20]),
    ("Big moments", "miniature", "Miniature", "mate", "checkmate wins in under 25 moves", ("count", "miniature"), [1, 3, 10]),
    ("Big moments", "equaliser", "Holding your own", "users", "wins or draws against someone rated 200 or more above you", ("count", "equaliser"), [1, 3, 10]),
    ("Big moments", "underdog", "Underdog run", "flame", "wins in a row against stronger players, best run", ("count", "underdog"), [2, 3, 5]),
    ("Accuracy", "sharp80", "Sharp game", "bolt", "games at 80% accuracy or better while the game was still open", ("count", "sharp80"), [3, 10, 25]),
    ("Accuracy", "master90", "Masterclass", "sparkles", "games at 90% accuracy or better while the game was still open", ("count", "master90"), [1, 3, 10]),
    ("Accuracy", "noblunder", "No blunders", "hang", "games in a row without a blunder, best run", ("count", "noblunder"), [3, 8, 15]),
    ("Accuracy", "bestmoves", "Engine eye", "search", "moves you played that were Stockfish's first choice", ("count", "bestmoves"), [250, 1000, 3000]),
    ("Accuracy", "goodstart", "Good starts", "book", "games with no mistake in your first 10 moves", ("count", "goodstart"), [15, 40, 100]),
    ("Clock", "timekeeper", "Time keeper", "clock", "games in a row not lost on time, best run", ("count", "timekeeper"), [20, 50, 100]),
    ("Clock", "coolhead", "Cool head", "clock", "wins with a third of your time still left", ("count", "coolhead"), [10, 30, 75]),
    ("Rating", "climber", "Climber", "up", "rating points above where you started, at your best", ("count", "climber"), [50, 150, 300]),
    ("Rating", "peak", "New heights", "progress", "times you set a new best rating", ("count", "peak"), [3, 10, 25]),
    ("Openings", "scholar", "Opening scholar", "book", "different openings you've won with", ("count", "scholar"), [5, 15, 30]),
    ("Openings", "loyal", "Loyal", "book", "wins with your favourite opening", ("count", "loyal"), [10, 25, 50]),
    ("Openings", "castle", "Castle early", "pawn", "games where you castled in your first 10 moves", ("count", "castle"), [15, 40, 100]),
    ("Training", "endings", "Endgame master", "mate", "endings beaten against perfect defence", ("count", "endings"), [2, 4, 6]),
    ("Training", "blindfold", "Blindfold", "ear", "longest line followed in your head, in moves each side", ("count", "blindfold"), [3, 5, 8]),
    ("Training", "guess", "Mind reader", "users", "best Guess the move score, out of 500", ("count", "guess"), [250, 350, 450]),
    ("Training", "tactician", "Tactician", "bolt", "tactic themes finished in Your plan", ("count", "tactician"), [3, 10, 20]),
    ("Training", "openlearn", "Opening learner", "book", "openings learned in Your plan", ("count", "openlearn"), [3, 10, 25]),
    ("Training", "thinker", "Thinker", "sparkles", "ways of thinking finished in Your plan", ("count", "thinker"), [1, 3, 5]),
    ("Training", "graduate", "Graduate", "plan", "course lessons passed, judged by your games", ("count", "graduate"), [2, 6, 15]),
    ("Training", "level", "Level up", "up", "your level on the ladder", ("count", "level"), [2, 3, 4]),
    ("Training", "dailyrun", "Streak keeper", "flame", "Today's 5 minutes, days in a row, best run", ("count", "streak"), [7, 30, 60]),
    ("Training", "puzzlerun", "On target", "practice", "positions right first time in a row, best run", ("count", "puzzlerun"), [5, 15, 30]),
]
LOSING = -300  # centipawns for you: about a quarter of a chance to win
AHEAD = 300


def _patterns(moves, g):
    return {r["pattern"] for r in moves[g["url"]]}


def runs(checked, moves, pattern):
    """(current run, best run) of games without the pattern; checked is newest first."""
    current, best, run, still = 0, 0, 0, True
    for g in checked:
        if pattern in _patterns(moves, g):
            still = False
            run = 0
            continue
        run += 1
        best = max(best, run)
        if still:
            current = run
    return current, best


def _moves_in(pgn):
    moves = re.sub(r"\{[^}]*\}", "", pgn.split("\n\n", 1)[-1])  # without the clock comments
    numbers = re.findall(r"(?<![\d.])(\d+)\.(?!\.)", moves)
    return max(map(int, numbers)) if numbers else 0


def _base(g):
    """The game's starting time in seconds, or None (daily games)."""
    tc = str(g.get("time_control", ""))
    return int(tc.split("+")[0]) if tc.split("+")[0].isdigit() else None


def _family(g):
    name = g.get("eco", "").rstrip("/").split("/")[-1]
    return " ".join(name.split("-")[:2]) or None


def _endgame(fen):
    """At most four pieces besides kings and pawns left on the board."""
    return sum(1 for c in fen.split(" ")[0] if c.isalpha() and c.lower() not in "kp") <= 4


def counts(checked, moves, player, daily_days=(), practice=None, lessons=0, extra=None):
    """Every count the badges need, from the checked games (newest first) and your practice."""
    from coach.narrate import accuracy
    out = collections.Counter()
    best_streak = streak = 0
    won_in = set()
    runs_now = collections.Counter()
    wins_with = collections.Counter()
    for g in reversed(checked):  # oldest first, for the win streak
        me, them = insights._side(g, player)
        result = insights._result(g, me)
        rows = moves[g["url"]]
        out["games"] += 1
        low = any(r.get("cp_before", 0) <= LOSING for r in rows)
        opp_up = g[them]["rating"] - g[me]["rating"]
        base, family = _base(g), _family(g)
        if result == "win" and low:
            out["comeback"] += 1
        if result == "draw" and low:
            out["survivor"] += 1
        if result == "win":
            early = [r for r in rows if r["ply"] <= 40]
            later = [r.get("cp_after", 0) for r in rows if r["ply"] > 40]
            if any(r.get("cp_after", 0) >= AHEAD for r in early) and (not later or min(later) >= 100):
                out["converter"] += 1
            if rows and _endgame(rows[-1]["fen"]):
                out["grinder"] += 1
            out["promotion"] += any("=" in r["move"] for r in rows)
            out["miniature"] += g[them]["result"] == "checkmated" and _moves_in(g.get("pgn", "")) < 25
            if base and rows and rows[-1].get("clock") is not None:
                out["coolhead"] += rows[-1]["clock"] >= base / 3
            if family:
                wins_with[family] += 1
        if result in ("win", "draw") and opp_up >= 200:
            out["equaliser"] += 1
        if opp_up > 0:  # against stronger players: a win carries the run, anything else ends it
            runs_now["underdog"] = runs_now["underdog"] + 1 if result == "win" else 0
            out["underdog"] = max(out["underdog"], runs_now["underdog"])
        open_ = [r for r in rows if abs(r.get("cp_before", 0)) <= AHEAD]  # while the game was still open: a decided
        if len(open_) >= 10:  # game makes every move look accurate (23 Oct number check)
            acc = sum(accuracy(r["loss"]) for r in open_) / len(open_)
            out["sharp80"] += acc >= 80
            out["master90"] += acc >= 90
        runs_now["noblunder"] = 0 if any(r["loss"] >= 30 for r in rows) else runs_now["noblunder"] + 1
        out["noblunder"] = max(out["noblunder"], runs_now["noblunder"])
        out["bestmoves"] += sum(1 for r in rows if r["move"] == r.get("best"))
        out["goodstart"] += bool(rows) and not any(r["ply"] <= 20 and r["loss"] >= 15 for r in rows)
        runs_now["timekeeper"] = 0 if result == "loss" and g[me]["result"] == "timeout" else runs_now["timekeeper"] + 1
        out["timekeeper"] = max(out["timekeeper"], runs_now["timekeeper"])
        out["castle"] += any(r["ply"] <= 20 and r["move"].startswith("O-O") for r in rows)
        if not biggest(rows):
            out["clean"] += 1
        if not any(r["pattern"] in LOSING_MATERIAL for r in rows):
            out["steady"] += 1
        if result == "win":
            out["wins"] += 1
            won_in.add(g["time_class"])
            out["mates"] += g[them]["result"] == "checkmated"
            out["giant"] += g[them]["rating"] >= g[me]["rating"] + 100
            out["black"] += me == "black"
            out["longwin"] += _moves_in(g.get("pgn", "")) >= 40
            streak += 1
            best_streak = max(best_streak, streak)
        else:
            streak = 0
    out["onaroll"], out["allround"] = best_streak, len(won_in)
    out["scholar"], out["loyal"] = len(wins_with), max(wins_with.values(), default=0)
    # rating: in each kind of game, from your first rating to your best, and how often you set a new best
    by_kind = collections.defaultdict(list)
    for g in sorted(insights._games(), key=lambda g: g["end_time"]):
        r = g[insights._side(g, player)[0]].get("rating")
        if r:
            by_kind[g.get("time_class")].append(r)
    for rs in by_kind.values():
        out["climber"] = max(out["climber"], max(rs) - rs[0])
        top = max(rs[:10])
        for r in rs[10:]:  # after the first 10 games of that kind, so the start doesn't count as records
            if r > top:
                top, out["peak"] = r, out["peak"] + 1
    out.update(extra or {})
    out["daily"] = len(set(daily_days))
    practice = practice or {}
    out["right"], out["learned"], out["lessons"] = practice.get("right_first", 0), practice.get("learned", 0), lessons
    return out


def badges(checked, moves, daily_days=(), player=None, practice=None, lessons=0, extra=None):
    have = counts(checked, moves, player or "", daily_days, practice, lessons, extra) if player else collections.Counter()
    out = []
    for group, bid, name, icon, what, (how, key), tiers in BADGES:
        if how == "run":
            current, value = runs(checked, moves, key)
        elif not player:
            continue
        else:
            current = value = have[key]
        tier = sum(1 for t in tiers if value >= t)
        out.append({"group": group, "id": bid, "name": name, "icon": icon, "what": what, "tier": tier,
                    "tier_name": TIER[tier - 1] if tier else None, "best": value, "current": current,
                    "next": tiers[tier] if tier < len(tiers) else None, "tiers": tiers})
    return out


def _per_game(gs, moves, patterns):
    return sum(1 for g in gs for r in moves[g["url"]] if r["pattern"] in patterns) / len(gs) if gs else 0


def story(checked, moves, player, now=None):
    """This week in a few facts: games, results, pieces given away against the week before, your best game,
    the habit that improved most, and next week's one thing."""
    now = now or time.time()
    week = [g for g in checked if g["end_time"] >= now - 7 * 86400]
    before = [g for g in checked if now - 14 * 86400 <= g["end_time"] < now - 7 * 86400]
    title = "Your week"
    if not week:  # no games this week: the story of the last 10 instead, said plainly
        week, before, title = checked[:10], checked[10:20], "Your last 10 games"
    if not week:
        return None
    results = collections.Counter(insights._result(g, insights._side(g, player)[0]) for g in week)
    pieces = round(_per_game(week, moves, LOSING_MATERIAL), 1)
    pieces_before = round(_per_game(before, moves, LOSING_MATERIAL), 1) if before else None

    def score(g):  # the best game: a win first, then the fewest big mistakes and pieces given away
        rows = moves[g["url"]]
        won = insights._result(g, insights._side(g, player)[0]) == "win"
        return (won, -len(biggest(rows)), -sum(1 for r in rows if r["pattern"] in LOSING_MATERIAL))
    # with a single game there's no "best"; when the best of them is still a loss, it's the closest one, not the best
    # (13 Oct test: a week of one lost game showed it as the "Best game")
    best_row = None
    played = [g for g in week if insights._moves_played(g.get("pgn", "")) >= 10]  # not a game they left after 2 moves (19 Oct)
    if len(played) >= 2:
        best = max(played, key=score)
        best_row = insights.game_row(best, moves[best["url"]], player)
        best_row["label"] = "Best game" if best_row["result"] == "win" else "Your closest game"
    improved = None
    if before:
        changes = [(_per_game(before, moves, {p}) - _per_game(week, moves, {p}), p) for p in ABOUT]
        drop, pattern = max(changes)
        if drop > 0.05:
            improved = {"pattern": pattern, "before": round(_per_game(before, moves, {pattern}), 1),
                        "now": round(_per_game(week, moves, {pattern}), 1)}
    counts = collections.Counter(r["pattern"] for g in week for r in moves[g["url"]] if r["pattern"] in ABOUT)
    focus = counts.most_common(1)[0][0] if counts else None
    return {"title": title, "from": datetime.fromtimestamp(week[-1]["end_time"]).strftime("%d %b %Y"),
            "to": datetime.fromtimestamp(week[0]["end_time"]).strftime("%d %b %Y"), "games": len(week),
            "results": dict(results), "pieces": pieces, "pieces_before": pieces_before,
            "best": best_row, "improved": improved,
            "next": {"pattern": focus, "habit": ABOUT[focus][1]} if focus else None}


def page():
    player = insights._player()
    if not player:
        return {"player": None}
    games, moves = insights._games(), insights._moves()
    checked = [g for g in games if g["url"] in moves]
    from coach import memory, plan
    days = daily._memory().get("days", [])
    lessons = len(plan._memory().get("done", []))
    from coach import clock
    return {"player": player, "story": story(checked, moves, player), "clock": clock.summary(checked, moves, player),
            "badges": badges(checked, moves, days, player, memory.practice_stats(), lessons, training(games, moves, player, days))}


def _longest_days(days):
    """The longest run of days in a row."""
    from datetime import date, timedelta
    ds = sorted({date.fromisoformat(d) for d in days})
    best = run = 0
    for i, d in enumerate(ds):
        run = run + 1 if i and d - ds[i - 1] == timedelta(days=1) else 1
        best = max(best, run)
    return best


def training(games, moves, player, days):
    """The Training badges' numbers, from Knightwise's own records; a part that fails counts 0, never stops the page."""
    import json
    from coach.paths import DATA
    out = {}

    def safe(key, how):
        try:
            out[key] = int(how() or 0)
        except Exception:
            out[key] = 0
    from coach import blindfold, course, endgames, ladder, memory, plan
    safe("endings", lambda: sum(1 for e in endgames.listing() if e["solved"]))
    safe("blindfold", lambda: (json.loads((DATA / "blindfold.json").read_text()).get("best", 0) + 1) // 2)
    safe("guess", lambda: json.loads((DATA / "guess.json").read_text()).get("ever") or json.loads((DATA / "guess.json").read_text()).get("best"))
    done = plan._memory().get("done", [])
    out["tactician"] = sum(1 for i in done if i.startswith("tactic:"))
    out["openlearn"] = sum(1 for i in done if i.startswith("opening:"))
    out["thinker"] = sum(1 for i in done if i.startswith("idea:"))
    safe("graduate", lambda: sum(1 for l in course.course()["lessons"] if l["status"] == "passed"))
    safe("level", lambda: ladder.ladder(games, moves, player)["current"] + 1)
    out["streak"] = _longest_days(days)

    def run():
        best = now = 0
        for e in memory._first_each_day():
            now = now + 1 if e["right"] else 0
            best = max(best, now)
        return best
    safe("puzzlerun", run)
    return out


# ---------- a badge completed: shown once, where it's calm (23 Oct test) ----------
CHECK_EVERY = 60  # seconds: the badges are worked out at most this often for the pop-up
_LAST = {"at": 0.0, "badges": None}
SOURCE = {"Practice": "your Knightwise training", "Training": "your Knightwise training"}


def _golds_file():
    from coach.paths import DATA
    return DATA / "badges-golds.json"


def new_gold(now=None):
    """The first badge completed (Gold) and not shown yet, or None. The very first time, every Gold already held is
    recorded quietly: your history counts, and only what you complete from now on pops up (the owner's choice)."""
    import json
    now = now or time.time()
    if _LAST["badges"] is None or now - _LAST["at"] >= CHECK_EVERY:
        p = page()
        _LAST.update(at=now, badges=p.get("badges") or [])
    golds = [b for b in _LAST["badges"] if b["tier"] == 3]
    f = _golds_file()
    try:
        m = json.loads(f.read_text())
    except (OSError, ValueError):
        m = None
    if m is None:
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps({"shown": [b["id"] for b in golds]}))
        return None
    b = next((b for b in golds if b["id"] not in m.get("shown", [])), None)
    if not b:
        return None
    return {"id": b["id"], "name": b["name"], "icon": b["icon"], "group": b["group"], "what": b["what"],
            "gold": b["tiers"][2], "from": SOURCE.get(b["group"], "your real chess.com games")}


def gold_shown(bid):
    import json
    f = _golds_file()
    try:
        m = json.loads(f.read_text())
    except (OSError, ValueError):
        m = {"shown": []}
    if bid and bid not in m.get("shown", []):
        m.setdefault("shown", []).append(str(bid)[:40])
        f.write_text(json.dumps(m))
