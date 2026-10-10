"""Practice page: positions from the player's own big mistakes. Click a move; the page says if it was good and why not.

Positions are different from the 3 examples per pattern on the review page. If the Lichess puzzles are
downloaded (python -m coach.puzzles), matching puzzles are added, a different set every day.
Run:  python -m coach.drills
Output: data/drills.html  (user data, never committed) - open it in any browser.
Every legal move in each position is scored by Stockfish when the page is built, so the page itself needs nothing.
"""
import json
import random
from itertools import zip_longest
from datetime import date
from pathlib import Path

import chess
import chess.engine

from coach.analyze import ENGINE, score_cp, win_chance
from coach.patterns import classify
from coach.puzzles import OUT as PUZZLES, THEMES
from coach.review import ABOUT, EXAMPLES, NAME, move_number, pick_examples

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "drills.html"
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
        return f"Then their {taker} takes your {what} on {chess.square_name(reply.to_square)} ({after.san(reply)})."
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


def drill(eng, pattern, r):
    """A position from the player's own game: every legal move scored by the engine."""
    board = chess.Board(r["fen"])
    scores = score_moves(eng, r["fen"])
    top = max(w for w, _ in scores.values())
    good = {m for m, (w, _) in scores.items() if top - w < GOOD}
    best = max(scores, key=lambda m: scores[m][0])
    color = "Black" if board.turn == chess.BLACK else "White"
    return {"kind": "game", "flip": board.turn == chess.BLACK, "pattern": pattern, "hint": ABOUT[pattern][1],
            "intro": f"You are {color}. Your move.", "played": r["move"], "best": board.san(best),
            "where": f"From your game: move {move_number(r)}, you are {color}", "url": r["url"],
            "link": "open game on chess.com", "start": squares(board), "last": None,
            "steps": [step(board, good, lambda m: why_wrong(board, m, scores[m][1]))]}


CLUE = {  # what to look for, per Lichess theme
    "hangingPiece": "Look for a piece of theirs that nobody protects.",
    "fork": "Look for a move that attacks two of their pieces at once.",
    "mateIn1": "Look at every check you can give: one of them is checkmate.",
    "mateIn2": "Look at every check you can give, starting with the most forcing one.",
}


def puzzle(p, pattern):
    """A Lichess puzzle: the opponent's move is shown first, then the player finds every move of the solution."""
    board = chess.Board(p["fen"])
    first = chess.Move.from_uci(p["moves"][0])
    start = squares(board)
    their_first = board.san(first)
    board.push(first)
    color = "Black" if board.turn == chess.BLACK else "White"
    hint = CLUE.get(THEMES.get(pattern), ABOUT[pattern][1])
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
    return {"kind": "puzzle", "flip": color == "Black", "pattern": pattern, "hint": hint,
            "intro": f"They just played {their_first}. You are {color}: find the best move.",
            "where": f"Lichess puzzle, rated {p['rating']}", "url": f"https://lichess.org/training/{p['id']}",
            "link": "open on lichess.org", "start": start, "last": [first.uci()[:2], first.uci()[2:4]],
            "steps": steps}


def pick_puzzles(by_pattern, top, seed):
    """PUZZLES_PER_PATTERN puzzles for each top pattern, different every day."""
    if not PUZZLES.exists():
        return []
    stock = json.loads(PUZZLES.read_text())
    rng = random.Random(seed)
    out = []
    for p in top:
        pool = stock.get(THEMES.get(p, ""), [])
        out += [puzzle(x, p) for x in rng.sample(pool, min(PUZZLES_PER_PATTERN, len(pool)))]
    return out


def build():
    rows = [json.loads(line) for line in open(ROOT / "data" / "moves.jsonl")]
    by_pattern = {}
    for r in rows:
        p = classify(r)
        if p in ABOUT and p != "stalemated a won game":
            by_pattern.setdefault(p, []).append(r)
    top = sorted(by_pattern, key=lambda p: -len(by_pattern[p]))[:3]
    with chess.engine.SimpleEngine.popen_uci(str(ENGINE)) as eng:
        eng.configure({"Threads": 4, "Hash": 128})
        drills = [drill(eng, p, r) for p in top for r in pick_examples(by_pattern[p], EXAMPLES + PER_PATTERN)[EXAMPLES:]]
    puzzles = pick_puzzles(by_pattern, top, seed=date.today().isoformat())
    drills = [d for pair in zip_longest(drills, puzzles) for d in pair if d]  # own position, puzzle, own, ...
    page = (Path(__file__).parent / "drills_template.html").read_text(encoding="utf-8")
    OUT.write_text(page.replace("/*DRILLS*/[]", json.dumps(drills)), encoding="utf-8")
    return OUT, len(drills)


if __name__ == "__main__":
    print(*build())
