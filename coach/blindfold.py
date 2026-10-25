"""Blindfold by voice (1.0): follow a game in your head, then answer on an empty board.

The coach reads out the first moves of one of your own games, from the start. The board stays empty. Then one
question, answered by clicking a square (or saying it, with an AI key): where a piece is now, which piece can be
taken, or which piece can give check. Every answer is worked out by python-chess from the real position, so it's
never wrong. Right: the next one is a move longer; wrong: a move shorter. Your record is kept.
Trains what "see it in your head" needs: holding a position without seeing it.
"""
import io
import json
import random

import chess
import chess.pgn

from coach import insights
from coach.paths import DATA

FILE = DATA / "blindfold.json"
RECENT = 10  # games read out lately: not again until 10 others have been (25 Oct, owner: "is it really fresh?")
BADGE = [(3, "Bronze"), (5, "Silver"), (8, "Gold")]  # the Blindfold badge, in moves each (progress.py)
START, LEAST, MOST, STEP = 4, 2, 30, 2  # half-moves read out: 2 each to begin with, one more each when right
NAME = {chess.PAWN: "pawn", chess.KNIGHT: "knight", chess.BISHOP: "bishop", chess.ROOK: "rook", chess.QUEEN: "queen",
        chess.KING: "king"}
SIDE = {chess.WHITE: "White", chess.BLACK: "Black"}


def _load():
    try:
        return json.loads(FILE.read_text())
    except (OSError, ValueError):
        return {}


def _save(d):
    FILE.parent.mkdir(parents=True, exist_ok=True)
    FILE.write_text(json.dumps(d))


def spoken(board, move):
    """A move as the coach says it: "knight f3", "e4", "bishop takes c6, check", "castles short"."""
    if board.is_castling(move):
        words = "castles short" if chess.square_file(move.to_square) == 6 else "castles long"
    else:
        piece = board.piece_at(move.from_square).piece_type
        to = chess.square_name(move.to_square)
        takes = board.is_capture(move)
        if piece == chess.PAWN:
            words = f"{chess.FILE_NAMES[chess.square_file(move.from_square)]} takes {to}" if takes else to
        else:
            words = f"{NAME[piece]} {'takes ' if takes else ''}{to}"
        if move.promotion:
            words += f", becomes a {NAME[move.promotion]}"
    board.push(move)
    if board.is_checkmate():
        words += ", checkmate"
    elif board.is_check():
        words += ", check"
    board.pop()
    return words


def _read_out(moves):
    """The whole sequence to speak, one move per sentence so each gets a pause (25 Oct, owner: "too quick"):
    "From the start. Move 1. White, e4. Black, e5. Move 2. White, knight f3."."""
    b, parts = chess.Board(), ["From the start."]
    for i, m in enumerate(moves):
        if i % 2 == 0:
            parts.append(f"Move {i // 2 + 1}.")
        parts.append(f"{'White' if i % 2 == 0 else 'Black'}, {spoken(b, m)}.")
        b.push(m)
    return " ".join(parts)


def questions(board, moved):
    """Every question this position can ask, each with its right answers (squares). moved: {square: piece type}
    of the pieces that moved in the sequence, where they stand now."""
    out = []
    for color in (chess.WHITE, chess.BLACK):
        kinds = {}  # the pieces of this side that moved (not pawns), by kind, where they stand now
        for sq, kind in moved.items():
            p = board.piece_at(sq)
            if p and p.color == color and p.piece_type == kind and kind != chess.PAWN:
                kinds.setdefault(kind, []).append(sq)
        for kind, squares in kinds.items():
            if len(squares) == 1:  # one of its kind moved: the question names it without doubt
                same = len(board.pieces(kind, color)) > 1
                out.append({"kind": "where", "answers": [chess.square_name(squares[0])],
                            "ask": f"Where is {SIDE[color]}'s {NAME[kind]} now{', the one that moved' if same else ''}? Click its square."})
    me, them = board.turn, not board.turn
    takes = sorted({chess.square_name(m.to_square) for m in board.legal_moves if board.is_capture(m) and not board.is_en_passant(m)})
    if 1 <= len(takes) <= 3:
        out.append({"kind": "capture", "ask": f"It's {SIDE[me]}'s move. Click a {SIDE[them].lower()} piece that {SIDE[me]} can take.",
                    "answers": takes})
    checks = sorted({chess.square_name(m.from_square) for m in board.legal_moves if board.gives_check(m)})
    if 1 <= len(checks) <= 2:
        out.append({"kind": "check", "ask": f"It's {SIDE[me]}'s move. Click a {SIDE[me].lower()} piece that can give check.",
                    "answers": checks})
    return out


def item(rng=None, games=None):
    """The next blindfold exercise at your length: {plies, say, moves, question, answers, fen, game}."""
    rng = rng or random.Random()
    state = _load()
    plies = state.get("plies", START)
    games = games if games is not None else insights._games()
    pool = []
    for g in games[:80]:
        game = chess.pgn.read_game(io.StringIO(g.get("pgn") or ""))
        if game is None:
            continue
        moves = list(game.mainline_moves())
        if len(moves) >= plies + 1:
            pool.append((g, moves[:plies]))
    if not pool:
        return None
    rng.shuffle(pool)
    recent = state.get("recent", [])
    pool.sort(key=lambda gm: gm[0].get("url") in recent)  # games not read out lately first (stable: still shuffled)
    for g, moves in pool:
        board = chess.Board()
        moved = {}
        for m in moves:
            p = board.piece_at(m.from_square).piece_type
            moved.pop(m.from_square, None)
            moved.pop(m.to_square, None)
            board.push(m)
            moved[m.to_square] = p
        qs = questions(board, moved)
        if plies < 8:
            qs = [q for q in qs if q["kind"] == "where"] or qs  # the first lengths: where a piece is
        if not qs:
            continue
        q = rng.choice(qs)
        b = chess.Board()
        sans = []
        for m in moves:
            sans.append(b.san(m))
            b.push(m)
        state["recent"] = ([g.get("url")] + [u for u in recent if u != g.get("url")])[:RECENT]
        _save(state)
        best_each = (state.get("best", 0) + 1) // 2
        goal = next(((n, name) for n, name in BADGE if best_each < n), None)
        mine = (g.get("white") or {}).get("username", "").lower() == (insights.home().get("player") or "").lower()
        other = (g.get("black") if mine else g.get("white")) or {}
        return {"plies": plies, "best": state.get("best", 0), "say": _read_out(moves), "moves": sans,
                "goal": {"moves": goal[0], "name": goal[1]} if goal else None, "question": q["ask"], "kind": q["kind"], "answers": q["answers"], "fen": board.fen(),
                "game": {"opponent": other.get("username"), "url": g.get("url")}}
    return None


def done(right, peeked=False):
    """Your answer: one move longer when right without peeking, one shorter when wrong. {plies, best, record}."""
    d = _load()
    plies = d.get("plies", START)
    record = False
    if right and not peeked:
        if plies > d.get("best", 0):
            d["best"], record = plies, True
        plies = min(MOST, plies + STEP)
    elif not right:
        plies = max(LEAST, plies - STEP)
    d["plies"] = plies
    _save(d)
    return {"plies": plies, "best": d.get("best", 0), "record": record}


def heard_square(text, ask_ai=None):
    """The square the player named out loud ("I think it's on f three"), worked out by the AI (no word patterns for
    understanding speech: CLAUDE.md), or None. Only a real square name comes back."""
    from coach import ai
    system = ("A chess player answered a question by naming one square of the board, out loud; speech-to-text wrote "
              "down what they said, sometimes misheard. Reply with only that square in lower case, like f3, or the "
              "word none if they named no square.")
    try:
        reply, _ = (ask_ai or ai.complete)(system, f"They said: {str(text)[:200]}", 10)
    except Exception:  # no key, or the AI is busy: they click instead
        return None
    word = (reply or "").strip().lower().strip(".\"' ")
    return word if word in chess.SQUARE_NAMES else None
