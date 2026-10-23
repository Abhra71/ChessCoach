"""The report (1.0): your week (or month) in facts, for a human coach to read, or to print and save as a PDF; the same
facts are Knightwise Wrapped, played as cards (coach/ui/app.js).

Every number comes from your checked chess.com games and your own practice in Knightwise; nothing is estimated.
Against the period before it, so a coach sees what changed, not only where you are.
"""
import collections
import time
from datetime import date, datetime

from coach import daily, insights, memory
from coach.progress import _per_game
from coach.review import ABOUT, LOSING_MATERIAL, biggest


def _rating(games, player):
    """(first, last) rating of yours in these games (oldest first), or (None, None)."""
    rs = [g[insights._side(g, player)[0]].get("rating") for g in sorted(games, key=lambda g: g["end_time"])]
    rs = [r for r in rs if r]
    return (rs[0], rs[-1]) if rs else (None, None)


THIN = 5  # fewer games than this in the period: the numbers swing a lot, and the report says so


def _ratings(period, every, player, start):
    """Your rating for each kind of game you played in the period (23 Oct test: "293 to 100" mixed rapid and blitz):
    from your last game of that kind before the period (or the first in it) to the last in it. Most played first."""
    out = []
    kinds = collections.Counter(g.get("time_class", "") for g in period)
    mine = lambda g: g[insights._side(g, player)[0]].get("rating")
    for kind, n in kinds.most_common():
        these = sorted((g for g in period if g.get("time_class") == kind), key=lambda g: g["end_time"])
        earlier = [g for g in every if g.get("time_class") == kind and g["end_time"] < start and mine(g)]
        first = mine(max(earlier, key=lambda g: g["end_time"])) if earlier else mine(these[0])
        last = mine(these[-1])
        if first and last:
            out.append({"kind": kind, "games": n, "from": first, "to": last})
    return out


def _practice(since, until):
    """Your practice in Knightwise in the period: answers, right first time, and the days you practised."""
    entries = [e for e in memory._first_each_day() if since <= e["day"] <= until]
    days = {e["day"] for e in entries} | {d for d in daily._memory().get("days", []) if since <= d <= until}
    return {"answers": len(entries), "right": sum(1 for e in entries if e["right"]), "days": len(days)}


def _lessons(since_ts):
    from coach import course
    try:
        return sum(1 for e in course._state().values() if isinstance(e, dict) and e.get("studied", 0) >= since_ts)
    except Exception:  # never let one part stop the report
        return 0


def report(days=7, now=None):
    """{period, games, results, rating, habits, clock, practice, best, worst, next, lines} or {"player": None}."""
    player = insights._player()
    if not player:
        return {"player": None}
    now = now or time.time()
    moves = insights._moves()
    checked = [g for g in insights._games() if g["url"] in moves]
    span = days * 86400
    period = [g for g in checked if g["end_time"] >= now - span]
    before = [g for g in checked if now - 2 * span <= g["end_time"] < now - span]
    since, until = date.fromtimestamp(now - span).isoformat(), date.fromtimestamp(now).isoformat()
    out = {"player": player, "days": days, "title": "Your week" if days <= 7 else "Your month",
           "from": datetime.fromtimestamp(now - span).strftime("%d %b %Y"), "to": datetime.fromtimestamp(now).strftime("%d %b %Y"),
           "games": len(period), "before_games": len(before)}
    side = lambda g: insights._side(g, player)[0]
    out["results"] = dict(collections.Counter(insights._result(g, side(g)) for g in period))
    out["kinds"] = dict(collections.Counter(g.get("time_class", "") for g in period))
    out["ratings"] = _ratings(period, insights._games(), player, now - span)
    main = out["ratings"][0] if out["ratings"] else {}
    out["rating"] = {"from": main.get("from"), "to": main.get("to"), "kind": main.get("kind")}  # the most played kind
    out["thin"] = 0 < len(period) < THIN
    # habits: per game in this period against the one before, the biggest ones first
    habits = []
    for pattern, (what, habit) in ABOUT.items():
        now_rate, then = _per_game(period, moves, {pattern}), _per_game(before, moves, {pattern}) if before else None
        if now_rate or then:
            habits.append({"pattern": pattern, "what": what, "habit": habit, "now": round(now_rate, 2),
                           "before": round(then, 2) if then is not None else None})
    out["habits"] = sorted(habits, key=lambda h: -h["now"])[:5]
    out["pieces"] = {"now": round(_per_game(period, moves, set(LOSING_MATERIAL)), 1),
                     "before": round(_per_game(before, moves, set(LOSING_MATERIAL)), 1) if before else None}
    out["big"] = round(sum(len(biggest(moves[g["url"]])) for g in period) / len(period), 1) if period else 0
    from coach import clock
    out["clock"] = clock.summary(period, moves, player, n=len(period) or 1) if period else None
    out["practice"] = _practice(since, until)
    out["lessons"] = _lessons(now - span)
    # the best game and the costliest moment, with what was better
    if period:
        def score(g):
            rows = moves[g["url"]]
            return (insights._result(g, side(g)) == "win", -len(biggest(rows)), -sum(1 for r in rows if r["pattern"] in LOSING_MATERIAL))
        played = [g for g in period if insights._moves_played(g.get("pgn", "")) >= 10] or period
        # the best game is a win, or a draw; a loss is never called your best (23 Oct test)
        good = [g for g in played if insights._result(g, side(g)) in ("win", "draw")]
        if good:
            best = max(good, key=score)
            out["best"] = insights.game_row(best, moves[best["url"]], player)
        worst = max(((r, g) for g in period for r in moves[g["url"]]), key=lambda x: x[0]["loss"], default=None)
        if worst and worst[0]["loss"] >= 15:
            r, g = worst
            out["worst"] = {"opponent": g[insights._side(g, player)[1]]["username"], "move": r["move"], "best": r["best"],
                            "move_number": r["ply"] // 2 + 1, "pattern": r["pattern"], "id": insights.game_id(g["url"]),
                            "loss": round(r["loss"])}
    home = insights.home()
    focus = home.get("focus") or {}
    out["next"] = {"habit": focus.get("habit"), "pattern": focus.get("pattern")}
    try:
        from coach import course
        c = course.course()
        row = next((r for r in c["lessons"] if r["id"] == c["next"]), None)
        out["next"]["lesson"] = row["title"] if row else None
    except Exception:  # never let one part stop the report
        out["next"]["lesson"] = None
    out["lines"] = lines(out)
    return out


def lines(r):
    """The report in a few plain sentences, the way a coach would say it."""
    if not r["games"]:
        return [f"No games in these {r['days']} days. One game is enough to have something to look at."]
    res = r["results"]
    w, d, l = res.get("win", 0), res.get("draw", 0), res.get("loss", 0)
    out = [f"{r['games']} game{'s' if r['games'] != 1 else ''}: {w} won, {d} drawn, {l} lost."]
    if r.get("thin"):
        out.insert(0, f"Only {r['games']} game{'s' if r['games'] != 1 else ''} in these {r['days']} days, so these numbers "
                      "can swing a lot." + (" The month view has more." if r["days"] <= 7 else ""))
    moved = [x for x in r.get("ratings", []) if x["from"] != x["to"]]
    if moved:
        out.append("Rating: " + ", ".join(f"{x['kind']} {x['from']} to {x['to']} ({x['to'] - x['from']:+d})" for x in moved) + ".")
    p = r["pieces"]
    if p["before"] is not None:
        change = "fewer than" if p["now"] < p["before"] else "more than" if p["now"] > p["before"] else "the same as"
        out.append(f"{p['now']} pieces given away a game, {change} the period before ({p['before']}).")
    if r["habits"]:
        h = r["habits"][0]
        out.append(f"The habit that costs most: {h['pattern']} ({h['now']} a game).")
    pr = r["practice"]
    if pr["answers"]:
        out.append(f"Practised on {pr['days']} day{'s' if pr['days'] != 1 else ''}: {pr['answers']} positions, "
                   f"{pr['right']} right first time.")
    else:
        out.append("No practice in Knightwise in this period.")
    if r["next"].get("habit"):
        out.append(f"Next: {r['next']['habit']}")
    return out
