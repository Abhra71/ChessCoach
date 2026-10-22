"""The whole-game review: one short line for every move, from the rules of chess and the engine's verdicts, no AI
(22 Oct hand test: "name positions, who moved which piece from where, what opportunities open up, small things,
not too elaborate, on each move"). Each line: who moved what from where, one thing it opens up or leaves loose,
and for the player's own moves how good it was (the engine's loss); for the opponent's, whether it was a slip."""
import chess

from coach.analyze import VALUE, win_chance

NAME = {chess.PAWN: "pawn", chess.KNIGHT: "knight", chess.BISHOP: "bishop", chess.ROOK: "rook", chess.QUEEN: "queen",
        chess.KING: "king"}
GOOD = ["Good.", "A good move.", "Solid.", "Fine."]
TOP = ["The engine's top choice.", "The best move.", "Exactly right."]
# win chance lost on one move (the same scale as the key moments)
SMALL, MISTAKE, BIG = 4, 10, 20
SLIP = 12  # the opponent handed this much win chance to the player


def _who(mine, opponent, first):
    return "You" if mine else (opponent if first else "They")


def _whose(color, me):
    return "your" if color == me else "their"


def _targets(board, sq, me):
    """Enemy pieces the piece on sq now hits that are worth hitting: undefended, or worth more than it."""
    piece = board.piece_at(sq)
    out = []
    for t in board.attacks(sq):
        victim = board.piece_at(t)
        if not victim or victim.color == piece.color:
            continue
        if victim.piece_type in (chess.KING, chess.PAWN):
            continue  # check is said on its own; pawns would be said on nearly every move
        loose = not board.attackers(victim.color, t)
        if loose or VALUE[victim.piece_type] > VALUE[piece.piece_type]:
            out.append((VALUE[victim.piece_type], t, victim, loose))
    return sorted(out, key=lambda x: -x[0])


def _loose(board, color):
    """color's pieces (not pawns or king) that are attacked and have no defender."""
    out = []
    for sq, p in board.piece_map().items():
        if p.color != color or p.piece_type in (chess.PAWN, chess.KING):
            continue
        if board.attackers(not color, sq) and not board.attackers(color, sq):
            out.append((VALUE[p.piece_type], sq, p))
    return sorted(out, key=lambda x: -x[0])


def line(board, move, me, opponent, first_theirs=False):
    """What happened on this move, in one sentence or two (board: the position before the move)."""
    piece, mover = board.piece_at(move.from_square), board.turn
    mine = mover == me
    who = _who(mine, opponent, first_theirs)
    pron = "your" if mine else "their"
    sq = chess.square_name
    if board.is_castling(move):
        text = f"{who} castled {'kingside' if chess.square_file(move.to_square) == 6 else 'queenside'}."
    elif board.is_capture(move):
        cap_sq = move.to_square if not board.is_en_passant(move) else chess.square(chess.square_file(move.to_square), chess.square_rank(move.from_square))
        victim = board.piece_at(cap_sq)
        text = (f"{who} took {_whose(victim.color, me)} {NAME[victim.piece_type]} on {sq(cap_sq)} "
                f"with {pron} {NAME[piece.piece_type]}.")
    else:
        text = f"{who} moved {pron} {NAME[piece.piece_type]} from {sq(move.from_square)} to {sq(move.to_square)}."
    if move.promotion:
        text = text[:-1] + f" and made a {NAME[move.promotion]}."
    after = board.copy()
    after.push(move)
    if after.is_checkmate():
        return text + " Checkmate."
    extra = ""
    hits = _targets(after, move.to_square, me)
    if after.is_check() and hits:
        extra = f"Check, and it also hits the {NAME[hits[0][2].piece_type]} on {sq(hits[0][1])}: a fork."
    elif after.is_check():
        extra = "Check."
    elif len(hits) >= 2:
        extra = (f"A fork: it hits the {NAME[hits[0][2].piece_type]} on {sq(hits[0][1])} "
                 f"and the {NAME[hits[1][2].piece_type]} on {sq(hits[1][1])}.")
    elif hits:
        _, t, victim, loose = hits[0]
        whose = "your" if not mine else "their"
        extra = f"Now it attacks {whose} {NAME[victim.piece_type]} on {sq(t)}" + (", which nobody defends." if loose else ".")
    else:  # nothing it attacks: does it leave something loose?
        was = {sq for _, sq, _ in _loose(board, me)}  # only what this move left loose, said once
        loose = [x for x in _loose(after, me) if x[1] not in was]
        if loose:
            _, t, p = loose[0]
            extra = (f"Careful: your {NAME[p.piece_type]} on {sq(t)} is attacked and undefended." if not mine else
                     f"Your {NAME[p.piece_type]} on {sq(t)} is loose now.")
    return f"{text} {extra}".strip()


def _uci(fen, san):
    try:
        return chess.Board(fen).parse_san(san).uci()
    except (ValueError, TypeError):
        return None


# chess.com-style labels (22 Oct: "names openings, calls book moves... blunder, good, brilliant"), from the win
# chance a move gave away (the engine on your moves; for theirs, what they handed you)
LABELS = [(2, "Excellent"), (5, "Good"), (10, "Inaccuracy"), (20, "Mistake"), (101, "Blunder")]
SIGN = {"Brilliant": "!!", "Best": "", "Book": "", "Excellent": "", "Good": "", "Inaccuracy": "?!", "Mistake": "?",
        "Blunder": "??"}
_BOOK = None


def book():
    """(every move sequence that is still in the opening catalogue, the name of each exact line)."""
    global _BOOK
    if _BOOK is None:
        from coach import openings
        prefixes, names = set(), {}
        for _eco, name, sans in openings.catalogue():
            names[tuple(sans)] = name
            for k in range(1, len(sans) + 1):
                prefixes.add(tuple(sans[:k]))
        _BOOK = (prefixes, names)
    return _BOOK


def _label(loss):
    return next(name for top, name in LABELS if loss < top)


def _sacrifice(after, sq):
    """The piece that just moved (a knight or more) can be taken for less: given away on purpose."""
    p = after.piece_at(sq)
    if not p or VALUE[p.piece_type] < 3:
        return False
    attackers = after.attackers(not p.color, sq)
    return bool(attackers) and (not after.attackers(p.color, sq) or
                                min(VALUE[after.piece_at(a).piece_type] for a in attackers) < VALUE[p.piece_type])


def game(positions, played, rows, me, opponent):
    """Every move of the game: [{ply, text, kind, label, arrows}], ply 1 = the first move. rows: the engine's
    verdicts on the player's moves (moves.jsonl, by ply). Labels like chess.com's: Book, Brilliant, Best,
    Excellent, Good, Inaccuracy, Mistake, Blunder; the opening is named when its line is reached."""
    by_ply = {r["ply"]: r for r in rows}
    prefixes, names = book()
    board = chess.Board(positions[0]["fen"])
    out, first_theirs, sans, in_book, named = [], True, [], True, None
    for i, move in enumerate(played, start=1):
        mine = board.turn == me
        san = board.san(move)
        sans.append(san)
        in_book = in_book and tuple(sans) in prefixes
        text = line(board, move, me, opponent, first_theirs and not mine)
        if not mine:
            first_theirs = False
        kind, arrows, label = ("mine" if mine else "real"), [[move.uci(), "mine" if mine else "real"]], None
        r = by_ply.get(i)
        after = board.copy()
        after.push(move)
        if mine and r:
            loss, best = r.get("loss") or 0, r.get("best")
            label = "Best" if best and san == best else _label(loss)
            if in_book and loss < 5:
                label = "Book"
            elif label == "Best" and _sacrifice(after, move.to_square) and win_chance(r.get("cp_after", 0)) >= 40:
                label = "Brilliant"
            if label in ("Inaccuracy", "Mistake", "Blunder") and best:
                text += {"Inaccuracy": f" An inaccuracy: {best} was better.", "Mistake": f" A mistake: {best} was better.",
                         "Blunder": f" A blunder: {best} was much better."}[label]
                kind = "bad" if label != "Inaccuracy" else "mine"
                u = _uci(r["fen"], best)
                if u:
                    arrows.append([u, "better"])
            else:
                text += {"Book": " A book move.", "Brilliant": " Brilliant: a sacrifice, and the best move.",
                         "Best": " " + TOP[i % len(TOP)], "Excellent": " Excellent.", "Good": " Good."}[label]
                kind = "good"
        elif not mine:  # their move: did it hand you a chance? (your chance after your last move -> before your next)
            prev, nxt = by_ply.get(i - 1), by_ply.get(i + 1)
            if in_book:
                label = "Book"
            if prev and nxt and "cp_after" in prev and "cp_before" in nxt:
                gain = win_chance(nxt["cp_before"]) - win_chance(prev["cp_after"])
                label = "Book" if in_book and gain < 5 else _label(max(0, gain))
                if gain >= SLIP and nxt.get("best"):
                    text += f" {'A blunder' if label == 'Blunder' else 'Their mistake'}: now {nxt['best']} is strong for you."
                    kind = "slip"
                    u = _uci(nxt["fen"], nxt["best"])
                    if u:
                        arrows.append([u, "better"])
                elif label == "Inaccuracy":
                    text += " An inaccuracy by them."
        if in_book and tuple(sans) in names and names[tuple(sans)] != named:  # the opening, by name, when it's reached
            named = names[tuple(sans)]
            text = (text[:-len(" Checkmate.")] + f" This is the {named}. Checkmate." if text.endswith(" Checkmate.")
                    else text + f" This is the {named}.")
        out.append({"ply": i, "text": text, "kind": kind, "label": label, "sign": SIGN.get(label, ""), "arrows": arrows})
        board.push(move)
    return out


def highlights(moves, n=3):
    """For a game with no big mistakes: its best moments to walk through (your top moves that kept the lead, their
    slips you could use, and the end)."""
    pick = [m for m in moves if m["kind"] == "slip"][:n]
    pick += [m for m in moves if m["kind"] == "good" and any(t in m["text"] for t in TOP)][: max(0, n - len(pick))]
    pick = sorted({m["ply"]: m for m in pick}.values(), key=lambda m: m["ply"])
    if moves and moves[-1] not in pick:
        pick.append(moves[-1])
    return [m["ply"] for m in pick]
