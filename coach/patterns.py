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


VALUE = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}


def exchange(board, move):
    """What the side to move wins by this capture once both sides have recaptured with their cheapest piece
    (static exchange; either side may stop when going on would lose)."""
    target = move.to_square
    gain = [VALUE[board.piece_at(target).piece_type] if board.piece_at(target) else 0]
    b = board.copy(stack=False)
    piece = VALUE[b.piece_at(move.from_square).piece_type]
    b.push(move)
    while True:
        attackers = list(b.attackers(b.turn, target))
        if not attackers:
            break
        s = min(attackers, key=lambda sq: VALUE[b.piece_at(sq).piece_type])
        gain.append(piece - gain[-1])
        piece = VALUE[b.piece_at(s).piece_type]
        promote = chess.QUEEN if b.piece_at(s).piece_type == chess.PAWN and chess.square_rank(target) in (0, 7) else None
        m = chess.Move(s, target, promotion=promote)
        if not b.is_legal(m):  # pinned, or would leave the king in check: the exchange stops here
            gain.pop()
            break
        b.push(m)
    for i in range(len(gain) - 1, 0, -1):
        gain[i - 1] = -max(-gain[i - 1], gain[i])
    return gain[0]


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
        best = before.parse_san(r["best"])
        taken = before.piece_at(best.to_square)
        # a whole piece was there to take (a pawn grab is rarely the point), and really free: it wins 2 or more after
        # every recapture (23 Oct number check: 5 of 25 "free" pieces were trades or tactics, not free)
        if taken and taken.piece_type != chess.PAWN and exchange(before, best) >= 2:
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
