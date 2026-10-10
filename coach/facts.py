"""Hard facts about one moment, worked out from the board and the engine's line (never guessed).

The AI explanation is only allowed to put these facts into friendly words.
"""
import chess

from coach.review import NAME, move_number

VALUE = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}


def _piece(board, sq):
    p = board.piece_at(sq)
    return f"{NAME[p.piece_type]} on {chess.square_name(sq)}"


def loose_pieces(board, color):
    """Pieces of `color` the other side can take for free (or win material on): undefended, or attacked by a cheaper piece."""
    out = []
    for sq, p in board.piece_map().items():
        if p.color != color or p.piece_type == chess.KING:
            continue
        attackers = board.attackers(not color, sq)
        if not attackers:
            continue
        defended = bool(board.attackers(color, sq))
        takers = [a for a in attackers if not (defended and board.piece_at(a).piece_type == chess.KING)]
        if not takers:  # only their king touches it, and the king can't take a protected piece
            continue
        cheapest = min(VALUE[board.piece_at(a).piece_type] for a in takers)
        if not defended or cheapest < VALUE[p.piece_type]:
            out.append(_piece(board, sq))
    return out


def line_san(board, ucis, limit=4):
    b, out = board.copy(), []
    for u in ucis[:limit]:
        m = chess.Move.from_uci(u)
        if m not in b.legal_moves:
            break
        out.append(b.san(m))
        b.push(m)
    return out


def describe_move(board, move):
    """What a move does, in plain facts: captures, check, saves a loose piece."""
    facts, mover = [], board.piece_at(move.from_square)
    if board.is_capture(move):
        taken = board.piece_at(move.to_square)
        facts.append(f"takes the {NAME[taken.piece_type] if taken else 'pawn'} on {chess.square_name(move.to_square)}")
    if board.gives_check(move):
        facts.append("gives check")
    before = set(loose_pieces(board, board.turn))
    after = board.copy()
    after.push(move)
    saved = before - set(loose_pieces(after, board.turn))
    if saved:
        facts.append("makes safe: " + ", ".join(sorted(saved)))
    newly = set(loose_pieces(after, board.turn)) - before
    if newly:
        facts.append("leaves loose: " + ", ".join(sorted(newly)))
    if after.is_checkmate():
        facts.append("is checkmate")
    return f"{NAME[mover.piece_type]} {chess.square_name(move.from_square)} to {chess.square_name(move.to_square)}" + \
        (" (" + "; ".join(facts) + ")" if facts else "")


def moment_facts(r, pattern):
    """Everything the coach knows for sure about one key moment, as short lines."""
    board = chess.Board(r["fen"])
    mine, best = board.parse_san(r["move"]), board.parse_san(r["best"])
    after = board.copy()
    after.push(mine)
    them = line_san(after, r.get("reply_pv", []))
    return {
        "move_number": move_number(r), "side": "White" if board.turn == chess.WHITE else "Black",
        "pattern": pattern, "played": r["move"], "played_does": describe_move(board, mine),
        "best": r["best"], "best_does": describe_move(board, best),
        "loose_after_played": loose_pieces(after, board.turn),
        "engine_line_after_played": them,
        "win_chance_lost": round(r["loss"]),
        "fen": r["fen"],
    }


def position_facts(fen, engine, depth=14):
    """Facts about any position: the engine's top 3 moves (and what each does), loose pieces on both sides."""
    import chess.engine

    from coach.analyze import score_cp, win_chance
    board = chess.Board(fen)
    infos = engine.analyse(board, chess.engine.Limit(depth=depth), multipv=3)
    top = []
    for info in infos:
        if not info.get("pv"):
            continue
        move = info["pv"][0]
        top.append({"move": board.san(move), "does": describe_move(board, move),
                    "win_chance_after": round(win_chance(score_cp(info["score"].pov(board.turn)))),
                    "line": line_san(board, [m.uci() for m in info["pv"]], 5)})
    return {"side_to_move": "White" if board.turn == chess.WHITE else "Black", "engine_top_moves": top,
            "loose_white_pieces": loose_pieces(board, chess.WHITE), "loose_black_pieces": loose_pieces(board, chess.BLACK),
            "in_check": board.is_check()}
