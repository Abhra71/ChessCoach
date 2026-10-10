"""Practice page: positions from the player's own big mistakes. Click a move; the page says if it was good and why not.

Positions are different from the 3 examples per pattern on the review page.
Run:  python -m coach.drills
Output: data/drills.html  (user data, never committed) - open it in any browser.
Every legal move in each position is scored by Stockfish when the page is built, so the page itself needs nothing.
"""
import json
from pathlib import Path

import chess
import chess.engine

from coach.analyze import ENGINE, score_cp, win_chance
from coach.patterns import classify
from coach.review import ABOUT, EXAMPLES, NAME, move_number, pick_examples

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "drills.html"
PER_PATTERN = 4
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


def drill(eng, pattern, r):
    board = chess.Board(r["fen"])
    scores = score_moves(eng, r["fen"])
    top = max(w for w, _ in scores.values())
    moves = {}
    for move, (w, reply) in scores.items():
        good = top - w < GOOD
        moves[move.uci()] = {"san": board.san(move), "good": good,
                             "say": "" if good else why_wrong(board, move, reply)}
    best = max(scores, key=lambda m: scores[m][0])
    return {"fen": r["fen"], "flip": board.turn == chess.BLACK, "pattern": pattern,
            "hint": ABOUT[pattern][1], "played": r["move"], "best": board.san(best),
            "where": f"Move {move_number(r)}, you are {'Black' if board.turn == chess.BLACK else 'White'}",
            "url": r["url"], "moves": moves,
            "board": {chess.square_name(s): p.symbol() for s, p in board.piece_map().items()}}


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
    page = (Path(__file__).parent / "drills_template.html").read_text(encoding="utf-8")
    OUT.write_text(page.replace("/*DRILLS*/[]", json.dumps(drills)), encoding="utf-8")
    return OUT, len(drills)


if __name__ == "__main__":
    print(*build())
