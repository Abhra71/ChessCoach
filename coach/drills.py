"""Practice page: positions from the player's own big mistakes. Click a move; the page says if it was good and why not.

Positions are different from the 3 examples per pattern on the review page; which ones come up is decided by
coach.memory (missed ones come back the next day, right ones after longer and longer gaps). If the Lichess puzzles are
downloaded (python -m coach.puzzles), matching puzzles are added, a different set every day.
Run:  python -m coach.drills
Output: data/drills.html  (user data, never committed) - open it in any browser.
Every legal move in each position is scored by Stockfish when the page is built, so the page itself needs nothing.
"""
import json
import random
from itertools import zip_longest
from datetime import date

import chess
import chess.engine

from coach import memory
from coach.analyze import open_engine, score_cp, win_chance
from coach.paths import DATA, TEMPLATES
from coach.patterns import classify
from coach.puzzles import OUT as PUZZLES, THEMES
from coach.review import ABOUT, EXAMPLES, NAME, move_number, pick_examples

OUT = DATA / "drills.html"
OUT_JSON = DATA / "drills.json"  # the same positions for the desktop app
PER_PATTERN = 4
PUZZLES_PER_PATTERN = 4
DEPTH = 12
GOOD = 10  # a move losing less than this much winning chance (0..100) vs the best move counts as right


def why_wrong(board, move, reply):
    """Plain sentence: what goes wrong after a wrong move (facts from the engine's answer)."""
    after = board.copy()
    after.push(move)
    if reply is None:
        return "That lets the advantage slip."
    if after.is_capture(reply):
        taker = NAME[after.piece_at(reply.from_square).piece_type]
        taken = after.piece_at(reply.to_square)
        what = NAME[taken.piece_type] if taken else "pawn"
        return f"Then their {taker} takes your {what} on {chess.square_name(reply.to_square)}."
    return f"Then they play {after.san(reply)} and you lose material soon after."


def score_moves(eng, fen):
    """Every legal move -> (win chance after it, engine's best answer)."""
    board = chess.Board(fen)
    me = board.turn
    out = {}
    for move in board.legal_moves:
        board.push(move)
        if board.is_checkmate():
            out[move] = (100.0, None)
        elif board.is_game_over():
            out[move] = (50.0, None)
        else:
            info = eng.analyse(board, chess.engine.Limit(depth=DEPTH))
            out[move] = (win_chance(score_cp(info["score"].pov(me))), info["pv"][0] if info.get("pv") else None)
        board.pop()
    return out


def squares(board):
    return {chess.square_name(s): p.symbol() for s, p in board.piece_map().items()}


def step(board, good, say, reply=None):
    """One move to find. good: set of right moves; say(move) -> why a wrong move is wrong.
    reply: the opponent's answer after the right move (puzzles with more than one move)."""
    moves = {}
    for move in board.legal_moves:
        entry = {"san": board.san(move), "good": move in good, "say": "" if move in good else say(move)}
        if move in good:
            after = board.copy()
            after.push(move)
            entry["after"] = squares(after)
        moves[move.uci()] = entry
    out = {"board": squares(board), "moves": moves, "reply": None}
    if reply:
        after = board.copy()
        after.push(next(iter(good)))
        out["reply"] = {"uci": reply.uci(), "san": after.san(reply)}
        after.push(reply)
        out["reply"]["board"] = squares(after)
    return out


def drill_id(r):
    return f"{r['url']}#{r['ply']}"


def drill(eng, pattern, r):
    """A position from the player's own game: every legal move scored by the engine."""
    board = chess.Board(r["fen"])
    scores = score_moves(eng, r["fen"])
    top = max(w for w, _ in scores.values())
    good = {m for m, (w, _) in scores.items() if top - w < GOOD}
    best = max(scores, key=lambda m: scores[m][0])
    color = "Black" if board.turn == chess.BLACK else "White"
    hint = ABOUT[pattern][1] if pattern in ABOUT else "Look at every check and capture, for both sides, before you move."
    return {"id": drill_id(r), "kind": "game", "flip": board.turn == chess.BLACK, "pattern": pattern, "hint": hint,
            "intro": f"You are {color}. Your move.", "played": r["move"], "best": board.san(best),
            "where": f"From your game: move {move_number(r)}, you are {color}", "url": r["url"],
            "link": "open game on chess.com", "start": squares(board), "last": None, "chance": round(top),
            "steps": [step(board, good, lambda m: why_wrong(board, m, scores[m][1]))]}


CLUE = {  # what to look for, per Lichess theme
    "hangingPiece": "Look for a piece of theirs that nobody protects.",
    "fork": "Look for a move that attacks two of their pieces at once.",
    "mateIn1": "Look at every check you can give: one of them is checkmate.",
    "mateIn2": "Look at every check you can give, starting with the most forcing one.",
    "pin": "Look for a piece that can't move because something more valuable is behind it.",
    "skewer": "Check or attack the big piece, and take the one behind it.",
    "discoveredAttack": "Move one piece out of the way so another one attacks.",
    "doubleCheck": "Find a move that gives check with two pieces at once.",
    "backRankMate": "Their king is stuck behind its own pawns on the back row.",
    "smotheredMate": "Their king is boxed in by its own pieces: a knight can mate.",
    "trappedPiece": "One of their pieces has no safe square left. Attack it.",
    "deflection": "Pull a defender away from the piece or square it guards.",
    "attraction": "Lure their king or queen onto a bad square.",
    "capturingDefender": "Take the piece that defends something, then take what it defended.",
    "promotion": "Get your pawn to the last row.",
    "defensiveMove": "They threaten something. Find the move that stops it.",
    "pawnEndgame": "In pawn endings the king is a strong piece: use it.",
    "rookEndgame": "Rooks belong behind passed pawns, and active.",
    "queenEndgame": "Checkmate, but leave their king a square: no stalemate.",
    "opening": "Early in the game: find the move that punishes their mistake.",
}


def puzzle(p, pattern, theme=None):
    """A Lichess puzzle: the opponent's move is shown first, then the player finds every move of the solution.
    theme: the Lichess theme it was chosen for (a new idea from the library), else the pattern's own theme."""
    board = chess.Board(p["fen"])
    first = chess.Move.from_uci(p["moves"][0])
    start = squares(board)
    their_first = board.san(first)
    board.push(first)
    color = "Black" if board.turn == chess.BLACK else "White"
    hint = CLUE.get(theme) or CLUE.get(THEMES.get(pattern)) or ABOUT.get(pattern, ("", "Take your time."))[1]
    steps = []
    solution = [chess.Move.from_uci(u) for u in p["moves"][1:]]
    for i in range(0, len(solution), 2):
        right = solution[i]
        good = {right}
        if i == len(solution) - 1:  # last move: any checkmate also counts
            for m in board.legal_moves:
                board.push(m)
                if board.is_checkmate():
                    good.add(m)
                board.pop()
        reply = solution[i + 1] if i + 1 < len(solution) else None
        steps.append(step(board, good, lambda m: "Not this one. " + hint, reply))
        board.push(right)
        if reply:
            board.push(reply)
    return {"id": p["id"], "kind": "puzzle", "flip": color == "Black", "pattern": pattern, "hint": hint,
            "intro": f"They just played {their_first}. You are {color}: find the best move.",
            "where": f"Lichess puzzle, rated {p['rating']}", "url": f"https://lichess.org/training/{p['id']}",
            "link": "open on lichess.org", "start": start, "last": [first.uci()[:2], first.uci()[2:4]],
            "steps": steps, "rating": p["rating"], "themes": p.get("themes", []), "their_move": their_first,
            "theme": theme or THEMES.get(pattern)}


def pick_puzzles(by_pattern, top, seed, rating=None):
    """PUZZLES_PER_PATTERN puzzles for each top pattern at the player's level, different every day, easiest first."""
    if not PUZZLES.exists():
        return []
    stock = json.loads(PUZZLES.read_text())
    rng = random.Random(seed)
    low, high = (rating or 800) - 150, (rating or 800) + 350
    out = []
    for p in top:
        every = stock.get(THEMES.get(p, ""), [])
        pool = [x for x in every if low <= x["rating"] <= high]
        if len(pool) < PUZZLES_PER_PATTERN:  # few at this level: the easiest ones there are
            pool = sorted(every, key=lambda x: x["rating"])[:PUZZLES_PER_PATTERN * 5]
        chosen = sorted(rng.sample(pool, min(PUZZLES_PER_PATTERN, len(pool))), key=lambda x: x["rating"])
        out += [puzzle(x, p) for x in chosen]
    return out


def build():
    rows = [json.loads(line) for line in open(DATA / "moves.jsonl")]
    by_pattern = {}
    for r in rows:
        p = classify(r)
        if p in ABOUT and p != "stalemated a won game":
            by_pattern.setdefault(p, []).append(r)
    top = sorted(by_pattern, key=lambda p: -len(by_pattern[p]))[:3]
    chosen = []
    for p in top:
        # every example of the pattern except the ones on the review page, clearest first
        candidates = {drill_id(r): r for r in pick_examples(by_pattern[p], len(by_pattern[p]))[EXAMPLES:]}
        chosen += [(p, candidates[i]) for i in memory.choose(list(candidates), PER_PATTERN)]
    with open_engine() as eng:
        eng.configure({"Threads": 4, "Hash": 128})
        drills = [drill(eng, p, r) for p, r in chosen]
    from coach import insights
    puzzles = pick_puzzles(by_pattern, top, seed=date.today().isoformat(), rating=insights.home().get("rating"))
    # organised by habit, biggest first: your own positions, then puzzles on the same habit, easiest first
    drills = [d for p in top for d in drills + puzzles if d["pattern"] == p]
    page = (TEMPLATES / "drills_template.html").read_text(encoding="utf-8")
    OUT.write_text(page.replace("/*DRILLS*/[]", json.dumps(drills)), encoding="utf-8")
    OUT_JSON.write_text(json.dumps(drills), encoding="utf-8")
    return OUT, len(drills)


if __name__ == "__main__":
    print(*build())
