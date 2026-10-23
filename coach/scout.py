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

GAMES = 30  # their latest games: the time class they play most first, then the others
DEPTH = 10  # a quick check: enough to see pieces left hanging, forks and mates, in about half a minute
PUZZLES = 10
PER_GAME = 2  # at most this many puzzles from one game
KEEP = 3600  # an hour, like Prep's games
_JOBS, _LOCK = {}, threading.Lock()

# their habit, said about them
THEY = {"left a piece hanging": ("leave pieces hanging", "pieces left hanging"),
        "walked into a fork or trick": ("walk into forks and tricks", "forks and tricks walked into"),
        "walked into checkmate": ("walk into checkmates", "checkmates walked into"),
        "missed a checkmate": ("miss checkmates they have", "checkmates missed"),
        "missed a free capture": ("miss free pieces", "free pieces missed"),
        "stalemated a won game": ("stalemate won games", "won games stalemated")}
HINT = {"left a piece hanging": ["Something of theirs has no defender now.", "Count what each of their pieces has guarding it.",
                                 "One of their pieces is loose. Which one?"],
        "walked into a fork or trick": ["Look for a move that attacks two things at once.", "A knight or queen move can hit two targets here.",
                                        "There's a double attack waiting."],
        "walked into checkmate": ["Look at every check you can give.", "Their king is short of squares.", "Checks first: one of them ends it."]}
# the task line, a different one each puzzle (24 Oct, owner: "punish" every time was too much)
INTRO = ["{u} just played {m}. You're {c}: punish it.",
         "{u} played {m} here. Your move as {c}.",
         "After {m}, something in {u}'s position gives way. You're {c}.",
         "{m} was a mistake. Show why, as {c}.",
         "{u} went {m}. What's your best reply as {c}?",
         "This is {u}'s real game: they played {m}. Find the move that makes them pay.",
         "{u} thought {m} was fine. As {c}, prove it wasn't.",
         "Your move as {c}, after {u}'s {m}."]
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
        result["puzzles"] = None  # the page shows everything else now; the puzzles follow
        _set(user, result=result, phase="puzzles")
        result = {**result, "puzzles": punish(user, picked, rows, lambda n: _set(user, done=len(picked) + n))}
        _set(user, state="done", done=len(picked) + PUZZLES, result=result)
    except Exception as e:  # noqa: BLE001  (shown to the player in plain words; the page keeps the quick stats)
        import logging
        logging.getLogger("knightwise").exception("scout %s", user)
        _set(user, state="error", message="The deeper look didn't work this time. The numbers above still stand.")


def _side(g, user):
    return "white" if g["white"]["username"].lower() == user else "black"


def latest(games, user, n=GAMES):
    """Their newest n games with a game record and at least 10 moves: the time class they play most first, then
    the others (newest first), so the clock numbers mostly come from one kind of game."""
    if not games:
        return []
    kind = collections.Counter(g["time_class"] for g in games).most_common(1)[0][0]
    ok = sorted((g for g in games if g.get("pgn") and g["pgn"].count(".") >= 10 and g["time_class"] != "daily"),
                key=lambda g: (g["time_class"] == kind, g.get("end_time", 0)), reverse=True)
    return ok[:n]


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
           "killers": killers(user, games, picked, rows, big),
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
        found += [(g, r) for r in sorted(cands, key=lambda r: -r["loss"])[:PER_GAME]]
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
            pattern, i = classify(r), len(out)
            out.append({"id": f"scout:{r['url']}#{r['ply']}", "kind": "puzzle", "flip": board.turn == chess.BLACK,
                        "pattern": None, "hint": HINT[pattern][i % len(HINT[pattern])],
                        "intro": INTRO[i % len(INTRO)].format(u=user, m=r["move"], c=colour),
                        "played": r["move"], "best": board.san(best), "their_move": r["move"],
                        "where": f"From {user}'s game, move {(r['ply'] + 1) // 2}", "url": g["url"],
                        "link": "open game on chess.com", "start": drills.squares(before),
                        "last": [their.uci()[:2], their.uci()[2:4]],
                        "end": ending(board, best, user, i),
                        "steps": [drills.step(board, good, lambda m, b=board, s=scores: drills.why_wrong(b, m, s[m][1]), close=close)]})
            if progress:
                progress(n)
    return out


def ending(board, best, user, i):
    """What the right move does, said plainly, in a different way each time."""
    san, after = board.san(best), board.copy()
    after.push(best)
    if after.is_checkmate():
        return ["Checkmate. Their mistake ended the game.", f"{san} is mate. That's what {user} missed."][i % 2]
    taken = board.piece_at(best.to_square) if board.is_capture(best) else None
    name = {chess.PAWN: "pawn", chess.KNIGHT: "knight", chess.BISHOP: "bishop", chess.ROOK: "rook", chess.QUEEN: "queen"}
    if taken:
        return [f"Right: {san} wins their {name[taken.piece_type]}.", f"{san}: their {name[taken.piece_type]} was there for the taking.",
                f"That's it. {user} left the {name[taken.piece_type]} without enough cover."][i % 3]
    if after.is_check():
        return [f"{san}: a check, and something falls after it.", f"Right: {san} starts the attack they didn't see."][i % 2]
    return [f"Right: after {san} they can't hold everything.", f"{san} is the move. Spot it in your game against them."][i % 2]


# ---------- the killer insights: two or three things that give you an edge, each with a number ----------
def _sans(pgn, n):
    import io
    import chess.pgn
    game = chess.pgn.read_game(io.StringIO(pgn or ""))
    if not game:
        return []
    board, out = game.board(), []
    for move in list(game.mainline_moves())[:n]:
        out.append(board.san(move))
        board.push(move)
    return out


def line_text(sans):
    return " ".join((f"{i // 2 + 1}. " if i % 2 == 0 else "") + m for i, m in enumerate(sans))


def _score(g, user):
    res = g[_side(g, user)]["result"]
    return 1 if res == "win" else 0.5 if res in prep.DRAWS else 0


def opening_line(games, user, their, least=3):
    """The opening line (2 to 10 half-moves) where they score worst when they're `their` colour, from all their
    games: {you, line, score, games, of}. None unless they score 40% or less there, in 3 games or more."""
    mine = [g for g in games if _side(g, user) == their]
    stats = collections.defaultdict(list)
    for g in mine:
        sans = _sans(g.get("pgn"), 10)
        for k in range(2, len(sans) + 1):
            stats[tuple(sans[:k])].append(_score(g, user))
    least = max(least, round(0.1 * len(mine)))  # a line they really reach, not a one-off
    rows = [(sum(v) / len(v), -len(v), -len(k), k) for k, v in stats.items() if len(v) >= least]
    if not rows:
        return None
    score, n, _, key = min(rows)
    if score > 0.4:
        return None
    return {"you": "black" if their == "white" else "white", "line": line_text(list(key)), "score": round(100 * score),
            "games": -n, "of": len(mine)}


def king(games, user):
    """How often they castle, and when: {castled, of, median_move}."""
    import io
    import chess.pgn
    moves, n = [], 0
    for g in games:
        game = chess.pgn.read_game(io.StringIO(g.get("pgn") or ""))
        if not game:
            continue
        me = chess.WHITE if _side(g, user) == "white" else chess.BLACK
        board, when = game.board(), None
        for ply, move in enumerate(game.mainline_moves(), 1):
            if board.turn == me and board.is_castling(move):
                when = (ply + 1) // 2
                break
            board.push(move)
            if ply > 80:
                break
        n += 1
        if when:
            moves.append(when)
    moves.sort()
    return {"castled": len(moves), "of": n, "median_move": moves[len(moves) // 2] if moves else None}


def rush(picked, rows, user, big):
    """Their big mistakes played in a rush, and games where they got short of time: {fast, of, short, games}."""
    fast = timed = short = clocked = 0
    bigs = collections.defaultdict(set)
    for r in big:
        bigs[r["url"]].add(r["ply"])
    for g in picked:
        tc = clock.base_and_increment(g.get("time_control"))
        side = _side(g, user)
        times = [(ply, s, left) for ply, who, s, left in clock.spent(g.get("pgn"), g.get("time_control")) if who == side]
        if not tc or not times:
            continue
        clocked += 1
        short += min(left for _, _, left in times) < tc[0] * 0.1
        for ply, s, _ in times:
            if ply in bigs[g["url"]]:
                timed += 1
                fast += s < clock.rushed_under(tc[0])
    return {"fast": fast, "of": timed, "short": short, "games": clocked}


def tilt(games, user):
    """How they do in the game straight after a loss (within two hours), against their usual score."""
    order = sorted(games, key=lambda g: g.get("end_time", 0))
    after = [_score(b, user) for a, b in zip(order, order[1:])
             if _score(a, user) == 0 and 0 < b.get("end_time", 0) - a.get("end_time", 0) < 7200]
    usual = sum(_score(g, user) for g in games) / len(games) if games else 0
    return {"after": round(100 * sum(after) / len(after)) if after else None, "n": len(after), "usual": round(100 * usual)}


def killers(user, games, picked, rows, big):
    """The two or three strongest edges, strongest first: [{kind, title, big, text, practise?}]."""
    out = []
    for their in ("white", "black"):
        o = opening_line(games, user, their)
        if o:
            out.append((1 - o["score"] / 100 + min(o["games"], 8) / 20, {
                "kind": "opening", "title": f"Your opening as {o['you'].capitalize()}", "big": f"{o['score']}%",
                "text": f"Aim for {o['line']}. They reach it in {o['games']} of their {o['of']} games as "
                        f"{'Black' if o['you'] == 'white' else 'White'}, and score only {o['score']}% from there.",
                "practise": f"spar/{user}/{o['you']}"}))
    k = king(games, user)
    if k["of"] >= 5:
        share = k["castled"] / k["of"]
        late = k["median_move"] and k["median_move"] >= 12
        if share < 0.6 or late:
            out.append(((1 - share) + (0.3 if late else 0), {
                "kind": "king", "title": "Their king", "big": f"{k['castled']}/{k['of']}",
                "text": (f"They castle in only {k['castled']} of {k['of']} games" if share < 0.6 else
                         f"They castle late, around move {k['median_move']}") +
                        ". Their king stays in the middle: open the centre and go after it."}))
    r = rush(picked, rows, user, big)
    if r["of"] >= 4 and r["fast"] / r["of"] >= 0.35:
        out.append((r["fast"] / r["of"], {
            "kind": "clock", "title": "They rush", "big": f"{r['fast']}/{r['of']}",
            "text": f"{r['fast']} of their {r['of']} big mistakes came in a few seconds. Keep it tricky: hasty moves are their weakness."}))
    elif r["games"] >= 5 and r["short"] / r["games"] >= 0.3:
        out.append((r["short"] / r["games"], {
            "kind": "clock", "title": "Their clock", "big": f"{r['short']}/{r['games']}",
            "text": f"They got short of time in {r['short']} of {r['games']} games. Keep it complicated and keep your own clock healthy."}))
    t = tilt(games, user)
    if t["after"] is not None and t["n"] >= 5 and t["usual"] - t["after"] >= 15:
        out.append(((t["usual"] - t["after"]) / 100 + 0.2, {
            "kind": "tilt", "title": "After a loss", "big": f"{t['after']}%",
            "text": f"Straight after a loss they score {t['after']}% (usually {t['usual']}%). Beat them once and a rematch suits you."}))
    return [x for _, x in sorted(out, key=lambda x: -x[0])][:3]
