"""The numbers and lists the desktop app shows: home dashboard, list of games, one game in detail.

Everything is computed from data/ (the player's games and the engine's checks); nothing leaves the computer.
"""
import collections
import io
import json
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
    if mtime != _CACHE["mtime"]:
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
        "id": game_id(g["url"]), "url": g["url"], "date": datetime.fromtimestamp(g["end_time"]).strftime("%d %b %Y"),
        "time_class": g["time_class"], "color": me, "result": _result(g, me),
        "opponent": g[them]["username"], "opponent_rating": g[them]["rating"], "rating": g[me]["rating"],
        "opening": g.get("eco", "").rstrip("/").split("/")[-1].replace("-", " ") or None,
        "pieces_lost": sum(1 for r in rows if r.get("pattern", classify(r)) in LOSING_MATERIAL),
        "moments": len(biggest(rows)), "checked": bool(rows),
    }


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
    trend = [round(sum(lost[i:i + TREND_WINDOW]) / len(lost[i:i + TREND_WINDOW]), 2)
             for i in range(0, len(lost), TREND_WINDOW)]
    results = collections.Counter(_result(g, _side(g, player)[0]) for g in checked)
    rapid = next((g for g in games if g["time_class"] == "rapid"), games[0] if games else None)
    last = game_row(checked[0], moves[checked[0]["url"]], player) if checked else None
    due = len(memory.boxes())  # positions practised so far
    return {
        "player": player, "games": len(checked), "results": dict(results),
        "rating": rapid[_side(rapid, player)[0]]["rating"] if rapid else None,
        "rating_class": rapid["time_class"] if rapid else None,
        "focus": {"pattern": focus, "times": counts[focus], "games": len({r["url"] for r in rows if r["pattern"] == focus}),
                  "meaning": ABOUT[focus][0], "habit": ABOUT[focus][1]} if focus else None,
        "patterns": [{"pattern": p, "times": n} for p, n in counts.most_common(4)],
        "pieces_per_game": round(sum(lost) / len(lost), 2) if lost else 0,
        "pieces_last20": round(sum(lost[-20:]) / len(lost[-20:]), 2) if lost else 0,
        "trend": trend, "trend_window": TREND_WINDOW,
        "last_game": last, "practice": {**memory.practice_stats(), "seen": due},
        "week": week(checked, moves),
    }


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
    for move in game.mainline_moves():
        san = board.san(move)
        board.push(move)
        positions.append({"fen": board.fen(), "san": san, "uci": move.uci()})
    key = []
    for r in biggest(rows):
        m = moment(r)
        m["habit"] = ABOUT[classify(r)][1] if classify(r) in ABOUT else None
        key.append(m)
    return {**game_row(g, rows, player), "positions": positions, "key_moments": key,
            "move_numbers": [move_number({"ply": i}) for i in range(1, len(positions))]}
