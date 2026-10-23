"""Guess the human move (1.0), also the weekly challenge: what would a player of this rating play here?

Five real positions from strong players' games (coach/library/elite.json, Lichess Elite), the same five all week, so
the week has one score to beat. For each, a rating: the human-move model (coach/maia.py) says how many players of
that rating play each move. Your guess scores by how popular it is there, out of 100 for the most played move, and
the answer shows the three most played moves and what Stockfish prefers: where people and the engine differ is the
lesson. The ratings are Lichess ratings, said so on the page.
"""
import datetime
import json
import random

import chess
import chess.engine

from coach import live_engine, maia
from coach.analyze import score_cp
from coach.paths import DATA, PROJECT

FILE = DATA / "guess.json"
ELITE = PROJECT / "coach" / "library" / "elite.json"
COUNT = 5
RATINGS = (1000, 1300, 1600, 1900, 2200)  # one position at each, easiest first
CHECK = chess.engine.Limit(depth=12)


def week(today=None):
    y, w, _ = (today or datetime.date.today()).isocalendar()
    return f"{y}-W{w:02d}"


def _load():
    try:
        return json.loads(FILE.read_text())
    except (OSError, ValueError):
        return {}


def _save(d):
    FILE.parent.mkdir(parents=True, exist_ok=True)
    FILE.write_text(json.dumps(d))


def _candidates(rng):
    """(board, the real move) from the middle of strong players' games, in a random order for this week."""
    games = [g for s in json.loads(ELITE.read_text())["structures"].values() for g in s["games"]]
    rng.shuffle(games)
    for g in games:
        b = chess.Board()
        moves = [chess.Move.from_uci(u) for u in g["moves"]]
        stop = rng.randint(16, min(50, len(moves) - 2)) if len(moves) > 20 else None
        if stop is None:
            continue
        for m in moves[:stop]:
            b.push(m)
        yield b


def build(wk):
    """The week's five positions: a human favourite at each rating, played by 35% to 85% there."""
    rng = random.Random(wk)
    out = []
    for board in _candidates(rng):
        if len(out) == COUNT:
            break
        rating = RATINGS[len(out)]
        p = maia.policy(board, rating)
        top = sorted(p.items(), key=lambda kv: -kv[1])[:3]
        if not top or not 35 <= top[0][1] <= 85 or board.is_check():  # a real guess: not a giveaway (99%, a recapture)
            continue
        with live_engine.LOCK:
            info = live_engine.get().analyse(board, CHECK)
        best = info["pv"][0] if info.get("pv") else None
        out.append({
            "fen": board.fen(), "rating": rating, "white": board.turn == chess.WHITE,
            "last": [chess.square_name(board.peek().from_square), chess.square_name(board.peek().to_square)],
            "legal": [m.uci() for m in board.legal_moves],
            "chances": {m.uci(): round(v, 1) for m, v in p.items() if v >= 0.5},
            "top": [{"uci": m.uci(), "san": board.san(m), "pct": round(v)} for m, v in top],
            "engine": {"uci": best.uci(), "san": board.san(best),
                       "cp": score_cp(info["score"].pov(board.turn))} if best else None,
        })
    return out


def challenge(today=None):
    """This week's challenge: {week, positions, best} (built once a week, then kept)."""
    wk = week(today)
    d = _load()
    if d.get("week") != wk or len(d.get("positions") or []) < COUNT:
        if not maia.enabled():
            return {"week": wk, "positions": [], "best": None, "off": True}
        d = {"week": wk, "positions": build(wk), "best": None, "tries": 0, "ever": d.get("ever")}
        _save(d)
    return {"week": wk, "positions": d["positions"], "best": d.get("best"), "tries": d.get("tries", 0)}


def score(position, uci):
    """Out of 100: how popular your move is among players of that rating, against the most played one."""
    top = position["top"][0]
    if uci == top["uci"]:
        return 100
    return min(100, round(100 * position["chances"].get(uci, 0) / (position["chances"].get(top["uci"]) or top["pct"] or 1)))


def done(total, today=None):
    """A finished try: the week's best so far, and whether this beat it."""
    d = _load()
    if d.get("week") != week(today):
        return {"best": total, "record": True}
    record = d.get("best") is None or total > d["best"]
    d["tries"] = d.get("tries", 0) + 1
    d["ever"] = max(d.get("ever") or 0, total)  # your best of all weeks: the Mind reader badge (23 Oct)
    if record:
        d["best"] = total
    _save(d)
    return {"best": d["best"], "record": record}
