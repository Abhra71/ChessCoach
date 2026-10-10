"""Sort the player's big mistakes (from data/moves.jsonl) into patterns.

Run:  python -m coach.patterns
"""
import collections
import json
import sys

import chess

from coach.analyze import material
from coach.paths import DATA

BLUNDER = 25  # lost at least this many points of winning chance (0..100) in one move


def classify(r):
    """Return the pattern name for one move record, or None if it was not a big mistake."""
    if r["stalemate"] and r["cp_before"] > 300:
        return "stalemated a won game"
    if r["loss"] < BLUNDER:
        return None
    if r["best_mates"]:
        return "missed a checkmate"
    if r["allows_mate"] and r["cp_before"] > -1000:
        return "walked into checkmate"
    board = chess.Board(r["fen"])
    me = board.turn
    board.push_san(r["move"])
    balance = []  # material balance after each ply of the engine's expected line
    for uci in r["reply_pv"][:4]:
        board.push_uci(uci)
        balance.append(material(board, me) - material(board, not me))
    # count after their capture AND our best reply, so a capture we can take back is not "hanging"
    if balance and balance[min(1, len(balance) - 1)] <= r["mat_before"] - 2:
        return "left a piece hanging"
    if len(balance) > 2 and balance[-1] <= r["mat_before"] - 2:
        return "walked into a fork or trick"
    if r["best_is_capture"]:
        before = chess.Board(r["fen"])
        taken = before.piece_at(before.parse_san(r["best"]).to_square)
        if taken and taken.piece_type != chess.PAWN:  # a whole piece was there to take (a pawn grab is rarely the point)
            return "missed a free capture"
    return "other"


def main():
    rows = [json.loads(l) for l in open(DATA / "moves.jsonl")]
    hits = collections.defaultdict(list)
    for r in rows:
        p = classify(r)
        if p:
            hits[p].append(r)
    games = {r["url"] for r in rows}
    print(f"{len(rows)} of your moves checked, {len(games)} games")
    for p, rs in sorted(hits.items(), key=lambda kv: -len(kv[1])):
        g = len({r["url"] for r in rs})
        low = sum(1 for r in rs if r["clock"] is not None and r["clock"] < 30)
        print(f"{len(rs):4} x {p:28} in {g:3} games  (under 30s on clock: {low})")
    if "--json" in sys.argv:
        json.dump({p: rs for p, rs in hits.items()}, open(DATA / "patterns.json", "w"))


if __name__ == "__main__":
    main()
