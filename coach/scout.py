"""How to beat them (24 Oct, owner's idea): Prep goes deeper on one player, in one view.

Stockfish checks only *their* moves in their last games (lighter than your own check: a quick depth), and the same
sorting Knightwise uses on your games names their habits. From that and the game records: where they go wrong
(opening, middlegame, endgame), under the clock, with a winning game; three tips; and "Punish their mistakes":
the real positions where they blundered, as puzzles you solve on the practice board.
Fair play: this is for before a game, from public games. Knightwise is never active during one.
"""
import collections
import functools
import os
import threading
import time
from concurrent.futures import ProcessPoolExecutor

import chess

from coach import clock, prep
from coach.analyze import analyse_game, open_engine
from coach.patterns import BLUNDER, classify

GAMES = 12  # their latest games of the time class they play most
DEPTH = 10  # a quick check: enough to see pieces left hanging, forks and mates, in about half a minute
PUZZLES = 5
KEEP = 3600  # an hour, like Prep's games
_JOBS, _LOCK = {}, threading.Lock()

# their habit, said about them
THEY = {"left a piece hanging": ("leave pieces hanging", "pieces left hanging"),
        "walked into a fork or trick": ("walk into forks and tricks", "forks and tricks walked into"),
        "walked into checkmate": ("walk into checkmates", "checkmates walked into"),
        "missed a checkmate": ("miss checkmates they have", "checkmates missed"),
        "missed a free capture": ("miss free pieces", "free pieces missed"),
        "stalemated a won game": ("stalemate won games", "won games stalemated")}
HINT = {"left a piece hanging": "They just left something undefended. Find it and take it.",
        "walked into a fork or trick": "Look for a move that attacks two things at once.",
        "walked into checkmate": "Look at every check you can give."}
PUNISH = tuple(HINT)


def status(user):
    """Start the check if it isn't running or fresh, and say where it is: {state, done, total[, result | message]}."""
    user = user.strip().lower()
    with _LOCK:
        job = _JOBS.get(user)
        if job and (job["state"] == "running" or time.time() - job["at"] < KEEP):
            return dict(job)
        job = _JOBS[user] = {"state": "running", "done": 0, "total": 0, "at": time.time()}
    threading.Thread(target=_run, args=(user,), daemon=True, name=f"scout-{user}").start()
    return dict(job)


def _set(user, **kw):
    with _LOCK:
        _JOBS[user].update(kw, at=time.time())


def _run(user):
    try:
        games = prep.games_of(user)
        picked = latest(games, user)
        if not picked:
            return _set(user, state="none", message="Not enough of their games to read.")
        _set(user, total=len(picked) + PUZZLES)
        rows = {}
        work = functools.partial(analyse_game, player=user, depth=DEPTH)
        with ProcessPoolExecutor(max_workers=max(1, min(4, (os.cpu_count() or 2) - 1))) as pool:
            for n, (g, out) in enumerate(zip(picked, pool.map(work, picked)), 1):
                rows[g["url"]] = out
                _set(user, done=n)
        result = summary(user, games, picked, rows)
        result["puzzles"] = punish(user, picked, rows, lambda n: _set(user, done=len(picked) + n))
        _set(user, state="done", done=len(picked) + PUZZLES, result=result)
    except Exception as e:  # noqa: BLE001  (shown to the player in plain words; the page keeps the quick stats)
        import logging
        logging.getLogger("knightwise").exception("scout %s", user)
        _set(user, state="error", message="The deeper look didn't work this time. The numbers above still stand.")


def _side(g, user):
    return "white" if g["white"]["username"].lower() == user else "black"


def latest(games, user, n=GAMES):
    """Their newest n games of the time class they play most, with a game record and at least 10 moves."""
    if not games:
        return []
    kind = collections.Counter(g["time_class"] for g in games).most_common(1)[0][0]
    ok = [g for g in games if g["time_class"] == kind and g.get("pgn") and g["pgn"].count(".") >= 10]
    return sorted(ok, key=lambda g: g.get("end_time", 0), reverse=True)[:n]


def phase(r):
    """opening (first 12 moves), endgame (6 or fewer pieces besides kings and pawns), else middlegame."""
    if r["ply"] <= 24:
        return "opening"
    board = chess.Board(r["fen"])
    pieces = sum(1 for p in board.piece_map().values() if p.piece_type not in (chess.KING, chess.PAWN))
    return "endgame" if pieces <= 6 else "middlegame"


def summary(user, games, picked, rows):
    every = [r for g in picked for r in rows.get(g["url"], [])]
    big = [r for r in every if r["loss"] >= BLUNDER]
    n = len(picked)
    habits = collections.Counter(p for p in (classify(r) for r in every) if p and p != "other" and p in THEY)
    top = [{"pattern": p, "say": THEY[p][0], "what": THEY[p][1], "count": c, "per_game": round(c / n, 1)}
           for p, c in habits.most_common(2)]
    phases = collections.Counter(phase(r) for r in big)
    # the clock: big mistakes made with under a fifth of their time left
    low = with_clock = 0
    for r in big:
        tc = clock.base_and_increment(next((g["time_control"] for g in picked if g["url"] == r["url"]), None))
        if tc and r.get("clock") is not None:
            with_clock += 1
            low += r["clock"] < tc[0] * 0.2
    # a winning game (3 pawns up or more) that they didn't win
    ahead = [g for g in picked if any(r["cp_before"] >= 300 for r in rows.get(g["url"], []))]
    slipped = [g for g in ahead if g[_side(g, user)]["result"] != "win"]
    out = {"games": n, "time_class": picked[0]["time_class"], "big_per_game": round(len(big) / n, 1),
           "habits": top, "phases": {k: phases.get(k, 0) for k in ("opening", "middlegame", "endgame")},
           "clock": {"low": low, "of": with_clock}, "slipped": {"lost": len(slipped), "of": len(ahead)},
           "worst_opening": worst_opening(games, user)}
    out["tips"] = tips(out)
    return out


def worst_opening(games, user, least=3):
    """The opening they score worst in (3 games or more, under 45%), from all their games: {name, score, games}."""
    by = collections.defaultdict(list)
    for g in games:
        name = prep._opening(g)
        if name:
            res = g[_side(g, user)]["result"]
            by[name].append(1 if res == "win" else 0.5 if res in prep.DRAWS else 0)
    rows = [(sum(v) / len(v), len(v), k) for k, v in by.items() if len(v) >= least]
    if not rows:
        return None
    score, count, name = min(rows)
    return {"name": name, "score": round(100 * score), "games": count} if score < 0.45 else None


def tips(s):
    """Three short tips, the strongest first, each from a number above."""
    out = []
    if s["habits"]:
        h = s["habits"][0]
        out.append({"left a piece hanging": "After every move they make, look for what they've left undefended.",
                    "walked into a fork or trick": "Look for forks: a knight or queen attacking two things at once.",
                    "walked into checkmate": "Go for their king: they don't see mating threats coming.",
                    "missed a checkmate": "Keep your king covered: they miss mates, but don't hand them chances.",
                    "missed a free capture": "Trades are fine: they often miss free pieces, so keep things simple.",
                    "stalemated a won game": "Never give up a lost-looking ending: they stalemate won games.",
                    }[h["pattern"]])
    total = sum(s["phases"].values())
    if total >= 3:
        where, n = max(s["phases"].items(), key=lambda kv: kv[1])
        if n / total >= 0.45:
            out.append({"opening": "Be sharp early: most of their big mistakes come in the first 12 moves.",
                        "middlegame": "Keep pieces on and the game busy: they go wrong in the middlegame.",
                        "endgame": "Trade pieces and head for an endgame: that's where they slip."}[where])
    c = s["clock"]
    if c["of"] >= 3 and c["low"] / c["of"] >= 0.4:
        out.append("Keep your clock healthy: when theirs runs low, their mistakes come.")
    sl = s["slipped"]
    if sl["of"] >= 2 and sl["lost"] / sl["of"] >= 0.3:
        out.append(f"Don't resign a bad position early: they let {sl['lost']} of {sl['of']} winning games slip.")
    if s["worst_opening"]:
        w = s["worst_opening"]
        out.append(f"Steer towards the {w['name']} if you can: they score {w['score']}% in it.")
    if not out:
        out.append("No clear weakness: play solid, safe moves and check what they can take.")
    return out[:3]


def punish(user, picked, rows, progress=None):
    """Up to PUZZLES positions just after one of their big mistakes, the worst first, one a game: find the move
    that punishes it. Every move is scored by the engine, like your own practice (coach/drills.py)."""
    from coach import drills
    found = []
    for g in picked:
        cands = [r for r in rows.get(g["url"], []) if r["loss"] >= BLUNDER and r["cp_before"] > -300 and classify(r) in PUNISH]
        if cands:
            found.append((g, max(cands, key=lambda r: r["loss"])))
    found = sorted(found, key=lambda x: -x[1]["loss"])[:PUZZLES]
    out = []
    with open_engine() as eng:
        eng.configure({"Threads": 1, "Hash": 64})
        for n, (g, r) in enumerate(found, 1):
            before = chess.Board(r["fen"])
            their = before.parse_san(r["move"])
            board = before.copy()
            board.push(their)
            if board.is_game_over():
                continue
            scores = drills.score_moves(eng, board.fen())
            good, close, best = drills.right_moves(eng, board, scores)
            colour = "White" if board.turn == chess.WHITE else "Black"
            pattern = classify(r)
            out.append({"id": f"scout:{r['url']}#{r['ply']}", "kind": "puzzle", "flip": board.turn == chess.BLACK,
                        "pattern": None, "hint": HINT[pattern],
                        "intro": f"{user} just played {r['move']}. You are {colour}: punish it.",
                        "played": r["move"], "best": board.san(best), "their_move": r["move"],
                        "where": f"From {user}'s game, move {(r['ply'] + 1) // 2}", "url": g["url"],
                        "link": "open game on chess.com", "start": drills.squares(before),
                        "last": [their.uci()[:2], their.uci()[2:4]],
                        "end": "That's how you punish it. Next time they play like this, you'll see it.",
                        "steps": [drills.step(board, good, lambda m, b=board, s=scores: drills.why_wrong(b, m, s[m][1]), close=close)]})
            if progress:
                progress(n)
    return out
