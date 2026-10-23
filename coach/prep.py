"""Prep before a game (0.8, flagship 1): how a chess.com player plays, from their public games, and what to do.

Type a username (or open their chess.com profile): Knightwise reads their last few months of public games
(chess.com's public API, no login) and says which openings they choose as White and as Black, how their games
usually end, and how you do against those openings in your own games.
Fair play: this is for before a game. Knightwise is never active during one.
"""
import collections
import io
import time

import chess.pgn

from coach import fetch, insights
from coach.review import DRAWS

MONTHS = 3  # their last three months of games
_CACHE = {}  # username -> (time, result): an hour


def _first_moves(pgn, n=2):
    game = chess.pgn.read_game(io.StringIO(pgn or ""))
    if not game:
        return ()
    board, out = game.board(), []
    for move in list(game.mainline_moves())[:n]:
        out.append(board.san(move))
        board.push(move)
    return tuple(out)


def _opening(g):
    return g.get("eco", "").rstrip("/").split("/")[-1].replace("-", " ") or None


_GAMES = {}  # username -> (time, their games): an hour, shared by prep and sparring


def games_of(user):
    """Their public games of the last three months (kept an hour)."""
    hit = _GAMES.get(user)
    if hit and time.time() - hit[0] < 3600:
        return hit[1]
    games = _games_of(user)
    _GAMES[user] = (time.time(), games)
    return games


def _games_of(user):
    archives = fetch.get_json(f"https://api.chess.com/pub/player/{user}/games/archives")["archives"][-MONTHS:]
    games = []
    for url in archives:
        games += [g for g in fetch.get_json(url).get("games", []) if g.get("rules") == "chess"]
    return games


def scout(user, me=None, games=None, mine=None):
    """{user, games, rating, as_white, as_black, endings, advice}, or None when there are no games to read."""
    user = user.strip().lower()
    me = (me or insights._player() or "").lower()
    games = games if games is not None else games_of(user)
    if not games:
        return None
    side = lambda g: "white" if g["white"]["username"].lower() == user else "black"
    as_white = [g for g in games if side(g) == "white"]
    as_black = [g for g in games if side(g) == "black"]

    def top(gs, pick):
        c = collections.Counter(pick(g) for g in gs if pick(g))
        return [{"what": k, "games": n, "share": round(100 * n / len(gs))} for k, n in c.most_common(3)] if gs else []
    first = lambda g: " ".join(_first_moves(g.get("pgn"), 1))  # their first move as White
    answer = lambda g: _first_moves(g.get("pgn"), 2)[1:2] and " ".join(_first_moves(g.get("pgn"), 2))  # 1.e4 e5: their answer
    results = collections.Counter()
    for g in games:
        s = side(g)
        res = g[s]["result"]
        results["won" if res == "win" else "drew" if res in DRAWS else
                {"checkmated": "lost by checkmate", "timeout": "lost on time", "resigned": "resigned"}.get(res, "lost another way")] += 1
    latest = max(games, key=lambda g: g.get("end_time", 0))
    out = {"user": user, "games": len(games), "rating": latest[side(latest)]["rating"],
           "time_class": collections.Counter(g["time_class"] for g in games).most_common(1)[0][0],
           "as_white": top(as_white, first), "as_black": top(as_black, answer),
           "openings": top(games, _opening), "endings": dict(results), "advice": []}
    out["advice"] = advice(out, me, mine)
    return out


def advice(s, me, mine=None):
    """What to do about it, from your own games: your score when the game started the way they like."""
    lines = []
    total = sum(s["endings"].values())
    lost_on_time = s["endings"].get("lost on time", 0)
    if total and lost_on_time / total >= 0.2:
        lines.append(f"They lose on time a lot ({lost_on_time} of {total} games). Keep it simple and keep your clock.")
    mated = s["endings"].get("lost by checkmate", 0)
    if total and mated / total >= 0.25:
        lines.append(f"They get checkmated often ({mated} of {total}). Look for checks against their king.")
    mine = mine if mine is not None else insights._games()
    if me and mine and s["as_white"]:
        fav = s["as_white"][0]["what"]  # their favourite first move as White: how do you do against it as Black?
        vs = [g for g in mine if g["black"]["username"].lower() == me and _first_moves(g.get("pgn"), 1) == (fav,)]
        if len(vs) >= 3:
            score = sum(1 if insights._result(g, "black") == "win" else 0.5 if insights._result(g, "black") == "draw" else 0
                        for g in vs) / len(vs)
            lines.append(f"As White they open {fav} in {s['as_white'][0]['share']}% of games. Against {fav} you score "
                         f"{round(100 * score)}% in {len(vs)} games{': that one is yours.' if score >= 0.55 else '.'}")
    if not lines:
        lines.append("Nothing stands out: play your own game, one move at a time, and check what they can take.")
    return lines


def cached(user, **kw):
    key = user.strip().lower()
    hit = _CACHE.get(key)
    if hit and time.time() - hit[0] < 3600:
        return hit[1]
    out = scout(key, **kw)
    _CACHE[key] = (time.time(), out)
    return out


# ---------- the "Homework done" badge (24 Oct, owner): prep someone, then win your very next game against them ----------
def _preps_file():
    from coach.paths import DATA
    return DATA / "preps.json"


def remember(user):
    """Note that you prepped against this player now (kept on this PC; the last 500)."""
    import json
    f = _preps_file()
    try:
        rows = json.loads(f.read_text())
    except (OSError, ValueError):
        rows = []
    rows = (rows + [{"user": user.strip().lower(), "at": int(time.time())}])[-500:]
    try:
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(rows))
    except OSError:
        pass


def beaten(mine, me, preps=None):
    """How many times you won the very next game against a player after prepping them. Each game counts once,
    however many times you prepped before it; other games in between don't matter."""
    import json
    if preps is None:
        try:
            preps = json.loads(_preps_file().read_text())
        except (OSError, ValueError):
            preps = []
    me = (me or "").lower()
    won = set()
    for p in preps:
        theirs = [g for g in mine if g.get("end_time", 0) > p["at"] and p["user"] in
                  (g["white"]["username"].lower(), g["black"]["username"].lower()) and me in
                  (g["white"]["username"].lower(), g["black"]["username"].lower())]
        if not theirs:
            continue
        nxt = min(theirs, key=lambda g: g["end_time"])
        side = "white" if nxt["white"]["username"].lower() == me else "black"
        if insights._result(nxt, side) == "win":
            won.add(nxt["url"])
    return len(won)
