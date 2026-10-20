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
    first, last = _rating(period, player)
    out["rating"] = {"from": first, "to": last}
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
        best = max(played, key=score)
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
    rt = r["rating"]
    if rt["from"] and rt["to"] and rt["from"] != rt["to"]:
        out.append(f"Rating {rt['from']} to {rt['to']} ({rt['to'] - rt['from']:+d}).")
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
