"""The numbers and lists the desktop app shows: home dashboard, list of games, one game in detail.

Everything is computed from data/ (the player's games and the engine's checks); nothing leaves the computer.
"""
import collections
import io
import json
import re
from datetime import datetime

import chess
import chess.pgn

from coach import memory
from coach.paths import DATA
from coach.patterns import classify
from coach.review import ABOUT, DRAWS, LOSING_MATERIAL, biggest, move_number
from coach.service import game_id, moment

TREND_WINDOW = 10  # games per point on the trend line


def _player():
    path = DATA / "player.txt"
    return path.read_text().strip() if path.exists() else None


_GAMES = {"key": None, "games": None}


def _games():
    """All archived games of the player, newest first (re-read only when a month file changes)."""
    files = sorted(DATA.glob("games-*.json"))
    key = tuple((f.name, f.stat().st_mtime) for f in files)
    if key != _GAMES["key"]:
        games = [g for f in files for g in json.loads(f.read_text())["games"] if g.get("rules") == "chess"]
        _GAMES.update(key=key, games=sorted(games, key=lambda g: g["end_time"], reverse=True))
    return _GAMES["games"]


_CACHE = {"mtime": None, "rows": None}


def _moves():
    """Checked moves per game, each with its pattern worked out once (re-read only when the file changes)."""
    path = DATA / "moves.jsonl"
    mtime = path.stat().st_mtime if path.exists() else None
    if mtime != _CACHE["mtime"] or _CACHE["rows"] is None:  # no games yet: empty, not None (26 Oct: a new account)
        rows = collections.defaultdict(list)
        if path.exists():
            for line in open(path):
                r = json.loads(line)
                r["pattern"] = classify(r)
                rows[r["url"]].append(r)
        _CACHE.update(mtime=mtime, rows=rows)
    return _CACHE["rows"]


def _side(g, player):
    me = "white" if g["white"]["username"].lower() == player.lower() else "black"
    return me, ("black" if me == "white" else "white")


def _result(g, me):
    res = g[me]["result"]
    return "win" if res == "win" else "draw" if res in DRAWS else "loss"


def game_row(g, rows, player):
    me, them = _side(g, player)
    return {
        "id": game_id(g["url"]), "url": g["url"], "end_time": g["end_time"], "date": datetime.fromtimestamp(g["end_time"]).strftime("%d %b %Y"),
        "time_class": g["time_class"], "color": me, "result": _result(g, me),
        "opponent": g[them]["username"], "opponent_rating": g[them]["rating"], "rating": g[me]["rating"],
        "opening": g.get("eco", "").rstrip("/").split("/")[-1].replace("-", " ") or None,
        "pieces_lost": sum(1 for r in rows if r.get("pattern", classify(r)) in LOSING_MATERIAL),
        "moments": len(biggest(rows)), "checked": bool(rows),
        "moves": _moves_played(g.get("pgn", "")), "how": g[them if _result(g, me) == "win" else me]["result"],
    }


def _moves_played(pgn):
    """How many moves the game lasted (so a game they left after 2 moves isn't called "a clean game")."""
    text = pgn.split("\n\n", 1)[-1]
    return max((int(n) for n in re.findall(r"(?<![\d.])(\d+)\.\s", text)), default=0)


def games_list():
    player, moves = _player(), _moves()
    return [game_row(g, moves.get(g["url"], []), player) for g in _games()] if player else []


def home():
    """The dashboard: focus habit, the score to bring down and its trend, last game, practice, rating."""
    player = _player()
    if not player:
        return {"player": None}
    games, moves = _games(), _moves()
    checked = [g for g in games if g["url"] in moves]
    rows = [r for g in checked for r in moves[g["url"]]]
    counts = collections.Counter(r["pattern"] for r in rows if r["pattern"] in ABOUT)
    focus = counts.most_common(1)[0][0] if counts else None
    lost = [sum(1 for r in moves[g["url"]] if r["pattern"] in LOSING_MATERIAL) for g in reversed(checked)]  # oldest first
    # each point a full window, counted back from the newest game, so the last point is always your last games
    # (23 Oct number check: it ended on a window of 3 games, 0.67, next to "0.7 in your last 20")
    window = TREND_WINDOW if len(lost) >= 2 * TREND_WINDOW else max(1, len(lost) // 4)
    trend = [round(sum(lost[i:i + window]) / window, 2) for i in range(len(lost) % window, len(lost) - window + 1, window)]
    results = collections.Counter(_result(g, _side(g, player)[0]) for g in checked)
    rapid = next((g for g in games if g["time_class"] == "rapid"), games[0] if games else None)
    last = game_row(checked[0], moves[checked[0]["url"]], player) if checked else None
    if last:  # its final position, for the small board on Home (22 Oct: pictures, not sentences)
        try:
            board = chess.pgn.read_game(io.StringIO(checked[0]["pgn"])).end().board()
            last["fen"], last["flip"] = board.fen(), last["color"] == "black"
        except (ValueError, AttributeError):
            pass
    recent = {g["url"] for g in checked[:20]}  # each habit: per game overall, and per game in the last 20
    recent_counts = collections.Counter(r["pattern"] for r in rows if r["url"] in recent and r["pattern"] in ABOUT)
    due = len(memory.boxes())  # positions practised so far
    return {
        "player": player, "games": len(checked), "results": dict(results),
        "rating": rapid[_side(rapid, player)[0]]["rating"] if rapid else None,
        "rating_class": rapid["time_class"] if rapid else None,
        "focus": {"pattern": focus, "times": counts[focus], "games": len({r["url"] for r in rows if r["pattern"] == focus}),
                  "meaning": ABOUT[focus][0], "habit": ABOUT[focus][1]} if focus else None,
        "patterns": [{"pattern": p, "times": n, "per_game": round(n / len(checked), 2),
                      "recent": round(recent_counts[p] / len(recent), 2)} for p, n in counts.most_common(4)],
        "rating_change": rating_change(games, player, rapid["time_class"]) if rapid else None,
        "pieces_per_game": round(sum(lost) / len(lost), 2) if lost else 0,
        "pieces_last20": round(sum(lost[-20:]) / len(lost[-20:]), 2) if lost else 0,
        "trend": trend, "trend_window": window,
        "last_game": last, "practice": {**memory.practice_stats(), "seen": due},
        "week": week(checked, moves),
        "you_vs_you": you_vs_you(checked, moves, player),
        "daily": daily_summary(),
    }


def daily_summary():
    from datetime import date
    from coach import daily
    days = daily._memory().get("days", [])
    today = date.today()
    return {"done_today": today.isoformat() in days, "streak": daily.streak(days, today), "week": daily.week_dots(days, today)}


def you_vs_you(checked, moves, player, now=None, size=20):
    """You now against you before: the last month against the month before when both have enough games,
    else your last 20 games against the 20 before them."""
    import time
    now = now or time.time()
    month = 30 * 86400
    a = [g for g in checked if g["end_time"] >= now - month]
    b = [g for g in checked if now - 2 * month <= g["end_time"] < now - month]
    label = ("This month", "Last month")
    if len(a) < 5 or len(b) < 5:
        a, b, label = checked[:size], checked[size:2 * size], (f"Last {size} games", f"The {size} before")
    if len(b) < 5:
        return None

    def score(gs):
        lost = [sum(1 for r in moves[g["url"]] if r["pattern"] in LOSING_MATERIAL) for g in gs]
        keys = [len(biggest(moves[g["url"]])) for g in gs]
        wins = sum(1 for g in gs if _result(g, _side(g, player)[0]) == "win")
        return {"games": len(gs), "pieces": round(sum(lost) / len(gs), 1), "moments": round(sum(keys) / len(gs), 1),
                "wins": round(100 * wins / len(gs))}
    return {"now": {**score(a), "label": label[0]}, "then": {**score(b), "label": label[1]}}


def rating_change(games, player, time_class, days=30, now=None):
    """How the rating moved in this time control over the last month (None without a game from before then)."""
    import time
    now = now or time.time()
    mine = [g for g in games if g["time_class"] == time_class]  # newest first
    old = next((g for g in mine if g["end_time"] < now - days * 86400), None)
    if not mine or not old:
        return None
    return mine[0][_side(mine[0], player)[0]]["rating"] - old[_side(old, player)[0]]["rating"]


def week(checked, moves, now=None):
    """This week against last week: games played and pieces given away (for the progress coach's memory)."""
    import time
    now = now or time.time()
    out = {}
    for name, start, end in (("this", now - 7 * 86400, now), ("last", now - 14 * 86400, now - 7 * 86400)):
        games = [g for g in checked if start <= g["end_time"] < end]
        lost = sum(1 for g in games for r in moves[g["url"]] if r["pattern"] in LOSING_MATERIAL)
        out[name] = {"games": len(games), "pieces": lost}
    return out


def game_detail(gid):
    """One game: every position (for stepping through), and its key moments with arrows and words."""
    player, moves = _player(), _moves()
    g = next((g for g in _games() if game_id(g["url"]) == str(gid)), None)
    if not g or not player:
        return None
    rows = moves.get(g["url"], [])
    game = chess.pgn.read_game(io.StringIO(g["pgn"]))
    board = game.board()
    positions = [{"fen": board.fen(), "san": None, "uci": None}]
    played = list(game.mainline_moves())
    for move in played:
        san = board.san(move)
        board.push(move)
        positions.append({"fen": board.fen(), "san": san, "uci": move.uci()})
    key = []
    for r in biggest(rows):
        m = moment(r, played)
        m["habit"] = ABOUT[classify(r)][1] if classify(r) in ABOUT else None
        key.append(m)
    from coach import narrate  # the whole game, move by move, no AI (22 Oct)
    side, other = _side(g, player)
    every = narrate.game(positions, played, rows, chess.WHITE if side == "white" else chess.BLACK, g[other]["username"])
    return {**game_row(g, rows, player), "positions": positions, "key_moments": key, "narration": every,
            "summary": narrate.summary(every),
            "move_numbers": [move_number({"ply": i}) for i in range(1, len(positions))], **extras(g, rows, player)}


def extras(g, rows, player):
    """The clock coach's lines for one game, and where a rematch of a game you didn't win would start: the moment
    that cost the most (flagships 4 and 5)."""
    from coach import clock
    me = _side(g, player)[0]
    worst = max(biggest(rows), key=lambda r: r["loss"], default=None)
    rematch = ({"ply": worst["ply"], "move_number": move_number(worst)}
               if worst and _result(g, me) != "win" else None)
    return {"clock": clock.game_clock(g, me, rows), "rematch": rematch}


def extras_for(gid):
    player, moves = _player(), _moves()
    g = next((g for g in _games() if game_id(g["url"]) == str(gid)), None)
    return extras(g, moves.get(g["url"], []), player) if g and player else {"clock": None, "rematch": None}
