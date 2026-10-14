"""Why a move was a mistake, in plain words, worked out from the board and the engine's line (0.10: the teacher).

Stockfish says *what* was better. A teacher says *why*: "your knight was guarding that pawn", "their bishop pins your
knight to your king", "three of your pieces are still at home". Every reason here is a fact checked on the board or
in the engine's line, never guessed, and each one is an *idea* that a lesson in the course teaches (coach/course.py).
When no simple idea explains the move, the coach says so honestly instead of making one up.

    explain(r) -> {"idea": "fork", "say": "...", "better": "..." or None}
"""
import chess

from coach.facts import VALUE, loose_pieces
from coach.review import NAME

# idea -> its name, as the course and the review show it
IDEAS = {
    "hanging": "a piece left hanging", "threats": "a threat not answered", "free": "a free piece not taken",
    "defender": "a guard moved away", "king_danger": "their checks and checkmates", "back_rank": "the back rank",
    "mate_finish": "a checkmate missed", "stalemate": "stalemate", "fork": "a fork", "pin": "a pin",
    "skewer": "a skewer", "discovered": "a discovered attack", "tactics": "a trick a few moves deep",
    "development": "getting your pieces out", "centre": "the centre", "king_safety": "king safety",
    "pawns": "pawn structure", "passed": "passed pawns", "active_king": "the king in the endgame",
    "activity": "active pieces", "deeper": "a deeper idea",
}
# idea -> what the course counts, said plainly ("0.55 a game: pieces moved to where they're taken")
COUNTED = {
    "hanging": "pieces moved to where they're taken", "threats": "attacked pieces not saved",
    "free": "free pieces not taken", "defender": "guards moved away", "king_danger": "checkmates walked into",
    "back_rank": "back-rank mates", "mate_finish": "checkmates missed", "stalemate": "stalemates in won games",
    "fork": "forks walked into or missed", "pin": "pins", "skewer": "skewers", "discovered": "discovered attacks",
    "tactics": "tricks a few moves deep", "development": "moves that left pieces at home",
    "centre": "edge moves instead of the centre", "king_safety": "king safety mistakes", "pawns": "pawn weaknesses made",
    "passed": "passed pawns not pushed or not stopped", "active_king": "endgames with the king left behind",
    "activity": "pieces left passive",
}
MINOR_HOME = {chess.WHITE: (chess.B1, chess.C1, chess.F1, chess.G1), chess.BLACK: (chess.B8, chess.C8, chess.F8, chess.G8)}
LOST = -2  # material points lost in the engine's line that make it a material mistake


def _name(board, sq):
    p = board.piece_at(sq)
    return f"{NAME[p.piece_type]} on {chess.square_name(sq)}"


def _balance(board, me):
    return sum((1 if p.color == me else -1) * VALUE[p.piece_type] for p in board.piece_map().values())


def _line(board, ucis, limit=4):
    """[(board before the move, move)] along the engine's line, stopping at anything illegal."""
    b, out = board.copy(), []
    for u in ucis[:limit]:
        m = chess.Move.from_uci(u)
        if m not in b.legal_moves:
            break
        out.append((b.copy(), m))
        b.push(m)
    return out, b


def _worst(after, line, me):
    """The lowest material balance along the line, counted after our answers (a piece we take back isn't lost)."""
    start = _balance(after, me)
    worst = 0
    for i, (b, m) in enumerate(line):
        nb = b.copy()
        nb.push(m)
        if nb.turn != me or i == len(line) - 1:  # after our answer, or the line's end
            worst = min(worst, _balance(nb, me) - start)
    return worst


def targets(board, sq):
    """What the piece on `sq` really threatens: the king (check), anything worth more than it, or anything loose."""
    piece = board.piece_at(sq)
    out = []
    for t in board.attacks(sq):
        v = board.piece_at(t)
        if not v or v.color == piece.color:
            continue
        if v.piece_type == chess.KING or (VALUE[v.piece_type] > VALUE[piece.piece_type] and v.piece_type != chess.PAWN) \
                or (VALUE[v.piece_type] >= 3 and not board.attackers(v.color, t)):
            out.append(t)
    return out


def _safe_square(board, sq):
    """The piece on `sq` can't simply be taken for free (or by something cheaper) right now."""
    p = board.piece_at(sq)
    takers = board.attackers(not p.color, sq)
    if not takers:
        return True
    if not board.attackers(p.color, sq):
        return False
    return min(VALUE[board.piece_at(a).piece_type] or 99 for a in takers) >= VALUE[p.piece_type]


def _fork(board, sq):
    """The piece on `sq` attacks two or more real targets (and isn't just lost itself): the targets, else []."""
    t = targets(board, sq)
    if len(t) < 2:
        return []
    checking = any(board.piece_at(x).piece_type == chess.KING for x in t)
    return t if checking or _safe_square(board, sq) else []


def _list(board, squares):
    names = [f"{'king' if board.piece_at(s).piece_type == chess.KING else NAME[board.piece_at(s).piece_type]}" for s in squares]
    names = sorted(names, key=lambda n: ["king", "queen", "rook", "bishop", "knight", "pawn"].index(n))
    return " and ".join([", ".join(names[:-1]), names[-1]] if len(names) > 2 else names)


def _pin(board, sq):
    """A piece of the other side that the slider on `sq` pins to its king (it can't legally move off the line)."""
    p = board.piece_at(sq)
    if p.piece_type not in (chess.BISHOP, chess.ROOK, chess.QUEEN):
        return None
    for t in board.attacks(sq):
        v = board.piece_at(t)
        if v and v.color != p.color and v.piece_type not in (chess.KING, chess.PAWN) and board.is_pinned(v.color, t):
            if board.pin(v.color, t) & chess.BB_SQUARES[sq]:
                return t
    return None


def _skewer(board, sq):
    """The slider on `sq` hits a king or queen, with another piece behind it on the same line: (front, behind)."""
    p = board.piece_at(sq)
    if p.piece_type not in (chess.BISHOP, chess.ROOK, chess.QUEEN):
        return None
    for t in board.attacks(sq):
        v = board.piece_at(t)
        if not v or v.color == p.color or v.piece_type not in (chess.KING, chess.QUEEN):
            continue
        ray = chess.SquareSet(chess.ray(sq, t))
        behind = [s for s in ray if t in chess.SquareSet(chess.between(sq, s)) and board.piece_at(s)
                  and (chess.SquareSet(chess.between(sq, s)) - {t}).isdisjoint(chess.SquareSet(board.occupied))]
        behind = sorted(behind, key=lambda s: chess.square_distance(s, sq))[:1]
        if behind and board.piece_at(behind[0]).color == v.color and board.piece_at(behind[0]).piece_type != chess.PAWN \
                and VALUE[board.piece_at(behind[0]).piece_type] < (99 if v.piece_type == chess.KING else 9):
            return t, behind[0]
    return None


def _discovered(before, move):
    """After `move`, another piece of the mover now attacks a king or a valuable piece through the square it left."""
    if before.piece_at(move.from_square).piece_type == chess.KING:
        return None
    after = before.copy()
    after.push(move)
    me = before.turn
    for sq in after.pieces(chess.BISHOP, me) | after.pieces(chess.ROOK, me) | after.pieces(chess.QUEEN, me):
        if sq == move.to_square:
            continue
        new = after.attacks(sq) - before.attacks(sq)
        for t in new:
            v = after.piece_at(t)
            if v and v.color != me and (v.piece_type == chess.KING or VALUE[v.piece_type] >= 5 or
                                        (VALUE[v.piece_type] >= 3 and not after.attackers(v.color, t))):
                if move.from_square in chess.SquareSet(chess.between(sq, t)):
                    return sq, t
    return None


def _passed(board, sq):
    p = board.piece_at(sq)
    if not p or p.piece_type != chess.PAWN:
        return False
    f, r = chess.square_file(sq), chess.square_rank(sq)
    ahead = range(r + 1, 8) if p.color == chess.WHITE else range(0, r)
    for s in board.pieces(chess.PAWN, not p.color):
        if abs(chess.square_file(s) - f) <= 1 and chess.square_rank(s) in ahead:
            return False
    return True


def _pawn_faults(board, me):
    """(doubled, isolated) pawn counts for one side."""
    files = [chess.square_file(s) for s in board.pieces(chess.PAWN, me)]
    doubled = sum(files.count(f) - 1 for f in set(files))
    isolated = sum(1 for f in files if (f - 1) not in files and (f + 1) not in files)
    return doubled, isolated


def _endgame(board):
    heavy = lambda c: sum(VALUE[p.piece_type] for p in board.piece_map().values()
                          if p.color == c and p.piece_type not in (chess.PAWN, chess.KING))
    return not board.pieces(chess.QUEEN, chess.WHITE) and not board.pieces(chess.QUEEN, chess.BLACK) \
        and heavy(chess.WHITE) <= 8 and heavy(chess.BLACK) <= 8


def _centre_distance(sq):
    f, r = chess.square_file(sq), chess.square_rank(sq)
    return max(abs(2 * f - 7), abs(2 * r - 7))


def _undeveloped(board, me):
    return [s for s in MINOR_HOME[me] if board.piece_at(s) and board.piece_at(s).color == me
            and board.piece_at(s).piece_type in (chess.KNIGHT, chess.BISHOP)]


def _back_rank_mate(final, mater):
    """The checkmate in `final` is on the back rank: the king on its first rank, mated by a rook or queen on it."""
    loser = not mater
    k = final.king(loser)
    rank = 0 if loser == chess.WHITE else 7
    if k is None or chess.square_rank(k) != rank:
        return False
    front = [s for s in chess.SquareSet(chess.BB_KING_ATTACKS[k]) if chess.square_rank(s) != rank]
    blocked = [s for s in front if final.piece_at(s) and final.piece_at(s).color == loser]
    pawns = [s for s in blocked if final.piece_at(s).piece_type == chess.PAWN]
    return len(blocked) == len(front) and len(pawns) >= 2 and \
        any(final.piece_at(a).piece_type in (chess.ROOK, chess.QUEEN) and chess.square_rank(a) == rank for a in final.checkers())


def explain(r, engine=None):
    """The main reason a move was weaker than the engine's best, and what the better move does.
    engine: when given (the review of one game), a reason a few moves deep is looked for in the engine's longer lines
    before the coach admits there's no simple one."""
    e = _explain(r)
    if e["idea"] == "deeper" and engine is not None:
        return _deeper(r, engine) or e
    return e


DEEP = 14
DEEP_PLIES = 8


def _deeper(r, engine):
    """The reason a few moves deep: what the better move's line wins, or what your move's line loses (engine facts)."""
    import chess.engine
    before = chess.Board(r["fen"])
    me = before.turn
    best, mine = before.parse_san(r["best"]), before.parse_san(r["move"])
    for first, gain in ((best, True), (mine, False)):
        b = before.copy()
        b.push(first)
        if b.is_game_over():
            continue
        info = engine.analyse(b, chess.engine.Limit(depth=DEEP))
        pv = [first.uci()] + [m.uci() for m in info.get("pv", [])[:DEEP_PLIES - 1]]
        line, end = _line(before, pv, DEEP_PLIES)
        shown = ", ".join(lb.san(m) for lb, m in (line[:5] if gain else line[1:6]))
        if gain:
            won = max(0, _gain(before, line, me))
            if won >= 2:
                return {"idea": "tactics", "better": None,
                        "say": f"Better was {r['best']}. Stockfish's line: {shown}, and you win about {won} points of "
                               f"material. It's a few moves deep: see the end before you move."}
        else:
            lost = _worst(b, line[1:], me) if len(line) > 1 else 0
            if lost <= LOST:
                return {"idea": "tactics", "better": None,
                        "say": f"After {r['move']}, Stockfish's line goes {shown}, and you lose about {-lost} points of "
                               f"material. The trouble is a few moves deep: look at their checks and captures after "
                               f"each move of the line."}
    return None


def _gain(start, line, me):
    """The material you're up at the end of the line, counted after their last answer (so a piece they take back
    straight away isn't counted as won)."""
    base, settled = _balance(start, me), 0
    for b, m in line:
        nb = b.copy()
        nb.push(m)
        if nb.turn == me:
            settled = _balance(nb, me) - base
    return settled


def _explain(r):
    before = chess.Board(r["fen"])
    me = before.turn
    mine, best = before.parse_san(r["move"]), before.parse_san(r["best"])
    after = before.copy()
    after.push(mine)
    line, end = _line(after, r.get("reply_pv") or [])
    reply = line[0][1] if line else None
    lost = _worst(after, line, me) if line else 0
    better = _better(before, best, mine, r)
    # "better": what the better move does, when it's a different idea from the reason itself
    out = lambda idea, say: {"idea": idea, "say": say,
                             "better": better[1] if better and better[0] != idea and idea != "mate_finish" else None}

    # --- the game result itself ---
    if r.get("stalemate") and r.get("cp_before", 0) > 300:
        return out("stalemate", f"{r['move']} leaves their king no legal move while it isn't in check: stalemate, a draw "
                                f"in a won game. Always leave the lone king a square.")
    if r.get("best_mates") and mine != best:
        b = before.copy()
        b.push(best)
        if b.is_checkmate():
            return out("mate_finish", f"{r['best']} was checkmate, right there. Look at every check first: one may end the game.")
        return out("mate_finish", f"{r['best']} starts a forced checkmate. When their king is short of squares, look at "
                                  f"every check before anything else.")
    if r.get("allows_mate") and reply:
        if end.is_checkmate() and _back_rank_mate(end, not me):
            return out("back_rank", f"After {r['move']}, they mate you on your back rank: your king is shut in by its own "
                                    f"pawns. A pawn move in front of it, in time, gives it a square to escape to.")
        if len(line) == 1 and end.is_checkmate():
            return out("king_danger", f"After {r['move']}, they have checkmate in one: {line[0][0].san(reply)}. "
                                      f"Before every move, look at every check they could give.")
        if not line[0][0].gives_check(reply):  # a quiet move that sets up the mate: checks alone wouldn't show it
            return out("king_danger", f"After {r['move']}, {line[0][0].san(reply)} sets up a checkmate you can't stop. "
                                      f"When their pieces gather near your king, ask what they threaten next, not only "
                                      f"which checks they have.")
        return out("king_danger", f"After {r['move']}, they can start a checkmate with {line[0][0].san(reply)}. "
                                  f"Before every move, look at every check they could give next.")

    # --- you lose material: how ---
    if reply and lost <= LOST:
        nb = after.copy()
        nb.push(reply)
        rsan = after.san(reply)
        if after.is_capture(reply):
            taken_sq = reply.to_square
            taken = after.piece_at(taken_sq)
            what = NAME[taken.piece_type] if taken else "pawn"
            taker = NAME[after.piece_at(reply.from_square).piece_type]
            if taken_sq == mine.to_square:
                if after.attackers(me, taken_sq) and taken and VALUE[after.piece_at(reply.from_square).piece_type] < VALUE[taken.piece_type]:
                    return out("hanging", f"You put your {what} on {chess.square_name(taken_sq)}, where their {taker} takes "
                                          f"it: a {taker} is worth less than a {what}, so defending it isn't enough.")
                return out("hanging", f"You put your {what} on {chess.square_name(taken_sq)}, where nothing guards it: "
                                      f"their {taker} just takes it. Before every move, ask what they can take after it.")
            was_loose = _name(before, taken_sq) in loose_pieces(before, me) if before.piece_at(taken_sq) else False
            guard = before.piece_at(mine.from_square)
            if was_loose:
                return out("threats", f"Your {what} on {chess.square_name(taken_sq)} was already under attack, and "
                                      f"{r['move']} did nothing about it: their {taker} takes it. After every move they make, "
                                      f"ask: what does it attack?")
            if before.piece_at(taken_sq) and mine.from_square in before.attackers(me, taken_sq) \
                    and mine.from_square not in after.attackers(me, taken_sq):
                return out("defender", f"Your {NAME[guard.piece_type]} on {chess.square_name(mine.from_square)} was guarding "
                                       f"your {what} on {chess.square_name(taken_sq)}. When it moved, their {taker} could take it.")
        fork = _fork(nb, reply.to_square)
        if fork:
            return out("fork", f"After {r['move']}, their {NAME[nb.piece_at(reply.to_square).piece_type]} comes to "
                               f"{chess.square_name(reply.to_square)} and attacks your {_list(nb, fork)} at once: you can "
                               f"save only one.")
        pinned = _pin(nb, reply.to_square)
        if pinned:
            return out("pin", f"After {r['move']}, their {NAME[nb.piece_at(reply.to_square).piece_type]} on "
                              f"{chess.square_name(reply.to_square)} pins your {_name(nb, pinned)} to your king: it can't "
                              f"move, and they win it.")
        sk = _skewer(nb, reply.to_square)
        if sk:
            return out("skewer", f"After {r['move']}, their {NAME[nb.piece_at(reply.to_square).piece_type]} hits your "
                                 f"{NAME[nb.piece_at(sk[0]).piece_type]}, and when it moves away, your {_name(nb, sk[1])} "
                                 f"behind it falls: a skewer.")
        disc = _discovered(after, reply)
        if disc:
            return out("discovered", f"After {r['move']}, {rsan} moves out of the way and uncovers their "
                                     f"{NAME[nb.piece_at(disc[0]).piece_type]} on {chess.square_name(disc[0])}: two attacks "
                                     f"at once, and you lose material.")
        if after.is_capture(reply):
            taken = after.piece_at(reply.to_square)
            return out("hanging", f"After {r['move']}, their {NAME[after.piece_at(reply.from_square).piece_type]} takes your "
                                  f"{NAME[taken.piece_type] if taken else 'pawn'} on {chess.square_name(reply.to_square)}, "
                                  f"and you can't win it back.")
        promo = _promotes(line, me)
        if promo:
            return out("passed", promo.format(move=r["move"]))
        later = _later_fork(line, me)
        if later:
            return out("fork", later.format(move=r["move"]))
        return out("tactics", f"After {r['move']}, they have {rsan}, and you lose about {-lost} points of material a move or "
                              f"two later, whatever you do. Look at their checks, captures and threats before you move.")

    # a fork or a new queen a move later costs you even when the engine's short line hasn't taken the material yet
    if reply and r["loss"] >= 10:
        promo = _promotes(line, me)
        if promo:
            return out("passed", promo.format(move=r["move"]))
        later = _later_fork(line, me, royal=True)
        if later:
            return out("fork", later.format(move=r["move"]))

    # --- you missed something the better move does ---
    if better and better[0] in ("free", "fork", "pin", "skewer", "discovered", "passed"):
        return out(better[0], better[1])

    # --- how you play, not a trick ---
    ply = r["ply"]
    if ply <= 24:
        home = _undeveloped(before, me)
        piece = before.piece_at(mine.from_square).piece_type
        best_piece = before.piece_at(best.from_square).piece_type
        if before.is_castling(best) and not before.is_castling(mine):
            return out("king_safety", f"Better was {r['best']}: castle now, your king is safe and your rook joins the game. "
                                      f"Kings left in the middle get attacked once the centre opens.")
        if (before.has_kingside_castling_rights(me) or before.has_queenside_castling_rights(me)) and \
                piece in (chess.KING, chess.ROOK) and not before.is_castling(mine) and \
                not (after.has_kingside_castling_rights(me) or after.has_queenside_castling_rights(me)):
            return out("king_safety", f"{r['move']} gives up castling for the rest of the game, so your king stays in the "
                                      f"middle. Castle first, then move the king or rook.")
        if piece == chess.QUEEN and len(home) >= 2 and ply <= 16:
            return out("development", f"Your queen goes out while {len(home)} of your knights and bishops are still at home. "
                                      f"They can chase her and bring out pieces at the same time. Pieces first, queen later.")
        if best.from_square in home and best_piece in (chess.KNIGHT, chess.BISHOP) and                 not any(after.piece_at(t) and after.piece_at(t).piece_type == chess.QUEEN for t in after.attacks(mine.to_square)):
            bb = before.copy()
            bb.push(best)
            hit = [t for t in bb.attacks(best.to_square) if bb.piece_at(t) and bb.piece_at(t).color != me
                   and bb.piece_at(t).piece_type == chess.QUEEN]
            if hit and _safe_square(bb, best.to_square):
                return out("development", f"Better was {r['best']}: it brings out a new piece and attacks their queen, so "
                                          f"they lose a move running away while you get ahead in development.")
        if len(home) >= 2 and best.from_square in home and best_piece in (chess.KNIGHT, chess.BISHOP) \
                and mine.from_square not in home:
            return out("development", f"Better was {r['best']}: bring out a new piece. {len(home)} of your knights and "
                                      f"bishops are still at home, and pieces at home don't play.")
        central = {chess.D4, chess.E4} if me == chess.WHITE else {chess.D5, chess.E5}
        if ply <= 12 and best_piece == chess.PAWN and best.to_square in central and \
                piece == chess.PAWN and chess.square_file(mine.from_square) in (0, 1, 6, 7):
            return out("centre", f"Better was {r['best']}: a pawn in the centre gives your pieces room and takes squares from "
                                 f"theirs. Edge pawn moves early do little.")
    k = before.king(me)
    if k is not None and before.piece_at(mine.from_square).piece_type == chess.PAWN and not _endgame(before):
        f = chess.square_file(mine.from_square)
        castled_k = chess.square_file(k) >= 6 and f >= 5
        castled_q = chess.square_file(k) <= 2 and f <= 2
        if (castled_k or castled_q) and abs(chess.square_file(k) - f) <= 1 and before.pieces(chess.QUEEN, not me):
            return out("king_safety", f"{r['move']} moves a pawn from in front of your castled king. Those pawns are its "
                                      f"shelter: every step forward opens a way in for their pieces.")
    if _endgame(before):
        bk = before.piece_at(best.from_square)
        if bk.piece_type == chess.KING and _centre_distance(best.to_square) < _centre_distance(best.from_square) \
                and before.piece_at(mine.from_square).piece_type != chess.KING:
            return out("active_king", f"Better was {r['best']}: in the endgame the king is a fighting piece. Bring it towards "
                                      f"the middle, where it helps your pawns and stops theirs.")
    if reply and after.piece_at(reply.from_square) and after.piece_at(reply.from_square).piece_type == chess.PAWN \
            and _passed(after, reply.from_square):
        return out("passed", f"After {r['move']}, their passed pawn on {chess.square_name(reply.from_square)} runs forward. "
                             f"Nothing stands in its way: stop it early, with a piece in front of it.")
    d_mine, i_mine = _pawn_faults(after, me)
    bb = before.copy()
    bb.push(best)
    d_best, i_best = _pawn_faults(bb, me)
    if d_mine + i_mine > d_best + i_best and before.piece_at(mine.from_square).piece_type != chess.KING \
            and r["loss"] < 20 and not before.is_capture(best) and not before.gives_check(best):
        kind = "a doubled pawn" if d_mine > d_best else "an isolated pawn"
        return out("pawns", f"{r['move']} leaves you with {kind}, a lasting weakness: it can't be guarded by another pawn. "
                            f"{r['best']} kept your pawns together.")
    if better:
        return out(better[0], better[1])
    mover = before.piece_at(mine.from_square)
    if mover.piece_type == chess.KNIGHT and chess.square_file(mine.to_square) in (0, 7) and \
            chess.square_file(best.to_square) not in (0, 7):
        return out("activity", f"{r['move']} puts your knight on the edge, where it reaches only a few squares. "
                               f"A knight in the middle does far more.")
    return {"idea": "deeper", "better": None,
            "say": f"Better was {r['best']}. The reason is a few moves deep, not one simple idea: it kept about "
                   f"{round(r['loss'])}% more of your chance to win. Play both moves on the board and compare."}


def _promotes(line, me):
    """Their pawn makes a new queen in the engine's line: the sentence (with {move} to fill), else None."""
    for b, m in line:
        if b.turn != me and m.promotion:
            return (f"After {{move}}, their pawn reaches the end: {b.san(m)} makes a new queen. A passed pawn that close "
                    f"must be stopped first, before anything else.")
    return None


def _later_fork(line, me, royal=False):
    """One of their moves in the engine's line forks two of your pieces (royal: only forks with the king or queen)."""
    for i, (b, m) in enumerate(line):
        if b.turn == me:
            continue
        nb = b.copy()
        nb.push(m)
        fork = _fork(nb, m.to_square)
        if fork and (not royal or any(nb.piece_at(s).piece_type in (chess.KING, chess.QUEEN) for s in fork)):
            piece = NAME[nb.piece_at(m.to_square).piece_type]
            return (f"After {{move}}, their {piece} reaches {chess.square_name(m.to_square)} with {b.san(m)} and "
                    f"attacks your {_list(nb, fork)}: you can save only one. Before you move, look at the squares their "
                    f"knights and queen can reach.")
    return None


def _better(before, best, mine, r):
    """What the better move does, as (idea, sentence), or None when it does nothing simple to name."""
    me = before.turn
    bsan = r["best"]
    b = before.copy()
    b.push(best)
    if before.is_capture(best) and not before.is_en_passant(best) and mine.to_square != best.to_square:
        sq = best.to_square
        v = before.piece_at(sq)
        if v and _name(before, sq) in loose_pieces(before, not me) and (v.piece_type != chess.PAWN or r.get("loss", 0) >= 10):
            return "free", f"Their {NAME[v.piece_type]} on {chess.square_name(sq)} was there to take: {bsan} wins it."
    fork = _fork(b, best.to_square)
    if fork and len([s for s in fork if b.piece_at(s).piece_type != chess.PAWN]) >= 2:
        return "fork", f"{bsan} forks their {_list(b, fork)}: one piece attacks them all, and they can save only one."
    pinned = _pin(b, best.to_square)
    if pinned and VALUE[b.piece_at(pinned).piece_type] >= 3:
        return "pin", f"{bsan} pins their {_name(b, pinned)} to its king: it can't move, so you can attack it again."
    sk = _skewer(b, best.to_square)
    if sk:
        return "skewer", (f"{bsan} hits their {NAME[b.piece_at(sk[0]).piece_type]}, and when it moves away, the "
                          f"{_name(b, sk[1])} behind it falls: a skewer.")
    disc = _discovered(before, best)
    if disc and disc != _discovered(before, mine):
        return "discovered", (f"{bsan} moves out of the way and uncovers your {NAME[b.piece_at(disc[0]).piece_type]} on "
                              f"{chess.square_name(disc[0])}: two attacks at once.")
    p = before.piece_at(best.from_square)
    if p.piece_type == chess.PAWN and _passed(before, best.from_square) and r.get("loss", 0) >= 7:
        return "passed", f"{bsan} pushes your passed pawn: nothing of theirs can block it with a pawn, so it runs to queen."
    if p.piece_type == chess.ROOK and not before.is_capture(best):
        f = chess.square_file(best.to_square)
        if chess.square_file(best.from_square) != f and not any(chess.square_file(s) == f for s in before.pieces(chess.PAWN, me)):
            open_ = not any(chess.square_file(s) == f for s in before.pieces(chess.PAWN, not me))
            return "activity", f"{bsan} puts your rook on the {'open' if open_ else 'half-open'} {'abcdefgh'[f]}-file, where it has room to work."
    return None
