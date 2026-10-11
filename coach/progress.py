"""Viktor's corner: the story of your week, and badges earned in your real chess.com games.

Every number comes from your games and the engine's checks; nothing here is made up or estimated.
"""
import collections
import time
from datetime import datetime

from coach import daily, insights
from coach.review import ABOUT, LOSING_MATERIAL, biggest

HANG, FORK, MATED = "left a piece hanging", "walked into a fork or trick", "walked into checkmate"
# a badge: games in a row without a habit (or a count), with three tiers
BADGES = [
    {"id": "safe", "name": "Safe pieces", "icon": "hang", "what": "games in a row without a hanging piece",
     "run_without": HANG, "tiers": [3, 5, 10]},
    {"id": "forkproof", "name": "Fork-proof", "icon": "fork", "what": "games in a row without walking into a fork",
     "run_without": FORK, "tiers": [5, 10, 20]},
    {"id": "king", "name": "Safe king", "icon": "mate", "what": "games in a row without walking into mate",
     "run_without": MATED, "tiers": [10, 20, 40]},
    {"id": "clean", "name": "Clean games", "icon": "capture", "what": "games with no big mistake",
     "count": "clean", "tiers": [1, 5, 15]},
    {"id": "daily", "name": "Daily habit", "icon": "bolt", "what": "days of Today's 5 minutes",
     "count": "daily", "tiers": [3, 7, 30]},
]
TIER = ["Bronze", "Silver", "Gold"]


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


def badges(checked, moves, daily_days=()):
    out = []
    for b in BADGES:
        if "run_without" in b:
            current, best = runs(checked, moves, b["run_without"])
            value = best
        elif b["count"] == "clean":
            current = value = sum(1 for g in checked if not biggest(moves[g["url"]]))
        else:
            current = value = len(set(daily_days))
        tier = sum(1 for t in b["tiers"] if value >= t)
        nxt = b["tiers"][tier] if tier < len(b["tiers"]) else None
        out.append({"id": b["id"], "name": b["name"], "icon": b["icon"], "what": b["what"], "tier": tier,
                    "tier_name": TIER[tier - 1] if tier else None, "best": value, "current": current,
                    "next": nxt, "tiers": b["tiers"]})
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
    best = max(week, key=score)
    best_row = insights.game_row(best, moves[best["url"]], player)
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
    days = daily._memory().get("days", [])
    return {"player": player, "story": story(checked, moves, player), "badges": badges(checked, moves, days)}
