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
# 20 badges in four groups. "run": games in a row without a habit; "count": a number from your games or practice.
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
    ("Results", "streak", "On a roll", "flame", "wins in a row, best run", ("count", "streak"), [2, 3, 5]),
    ("Results", "mates", "Checkmater", "mate", "wins by checkmate", ("count", "mates"), [5, 20, 50]),
    ("Results", "giant", "Giant slayer", "up", "wins against someone rated 100 or more above you", ("count", "giant"), [1, 5, 15]),
    ("Results", "black", "Dark side", "pawn", "wins with the black pieces", ("count", "black"), [5, 20, 60]),
    ("Results", "allround", "All-rounder", "games", "time controls you've won in", ("count", "allround"), [2, 3, 4]),
    ("Results", "games", "Regular", "games", "games played", ("count", "games"), [25, 100, 300]),
    ("Practice", "daily", "Daily habit", "bolt", "days of Today's 5 minutes", ("count", "daily"), [3, 7, 30]),
    ("Practice", "right", "Sharp", "practice", "positions solved on the first try", ("count", "right"), [10, 50, 200]),
    ("Practice", "learned", "Memory", "plan", "positions learned for good", ("count", "learned"), [5, 20, 50]),
    ("Practice", "lessons", "Student", "plan", "lessons finished in Your plan", ("count", "lessons"), [1, 5, 15]),
]


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


def counts(checked, moves, player, daily_days=(), practice=None, lessons=0):
    """Every count the badges need, from the checked games (newest first) and your practice."""
    out = collections.Counter()
    best_streak = streak = 0
    won_in = set()
    for g in reversed(checked):  # oldest first, for the win streak
        me, them = insights._side(g, player)
        result = insights._result(g, me)
        rows = moves[g["url"]]
        out["games"] += 1
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
    out["streak"], out["allround"] = best_streak, len(won_in)
    out["daily"] = len(set(daily_days))
    practice = practice or {}
    out["right"], out["learned"], out["lessons"] = practice.get("right_first", 0), practice.get("learned", 0), lessons
    return out


def badges(checked, moves, daily_days=(), player=None, practice=None, lessons=0):
    have = counts(checked, moves, player or "", daily_days, practice, lessons) if player else collections.Counter()
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
    if len(week) >= 2:
        best = max(week, key=score)
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
    return {"player": player, "story": story(checked, moves, player),
            "badges": badges(checked, moves, days, player, memory.practice_stats(), lessons)}
