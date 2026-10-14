"""The endgame trainer (0.7): the endings every player must know, played out against Stockfish's best defence.

Each ending has a goal (checkmate, promote, or hold the draw) and a move limit. Positions are new every time:
random but checked by the engine to be what the ending is about (a win to convert, or a draw to hold). After each
of your moves the engine checks it: a stalemate, a piece given away or a win thrown away is said at once, with
the chance to take it back, so the habit forms on the board (the user's games: 4 won games stalemated).
"""
import json
import random

import chess
import chess.engine

from coach import live_engine
from coach.analyze import score_cp
from coach.paths import DATA

FILE = DATA / "endgames.json"
TABLEBASE = "https://tablebase.lichess.ovh/standard?fen="  # Lichess's free endgame tablebase: perfect play, 7 pieces
_TB = {}
DEFENCE = chess.engine.Limit(depth=14)  # the defender plays its best move
CHECK = chess.engine.Limit(depth=12)

# id, name, level (ladder), goal, move limit, pieces ("Q" = white queen ...), the one idea, the tip after a stalemate
ENDINGS = [
    ("queen", "Mate with king and queen", 1, "mate", 10, "KQ",
     "Use your queen to box their king in, a knight's jump away, until it's on the edge. Then bring your king close and mate.",
     "Their king had no move but wasn't in check: stalemate, a draw. Keep the queen a knight's jump away, never closer, until your king is near."),
    ("rook", "Mate with king and rook", 1, "mate", 16, "KR",
     "Cut their king off with your rook, bring your king up opposite theirs, and push it to the edge one row at a time.",
     "Stalemate. When their king has only a couple of squares, make a waiting move with the rook instead of taking the last square."),
    ("tworooks", "The ladder mate with two rooks", 1, "mate", 8, "KRR",
     "Your two rooks take turns: one holds a row, the other gives check on the next row, like climbing a ladder.",
     "Stalemate. Check their king each move; a quiet rook move can take its last square."),
    ("pawn", "Win with king and pawn", 2, "promote", 20, "KP",
     "Your king goes in front of your pawn, and takes the opposition: kings face to face with one square between, and they must move first.",
     "Stalemate: with king and pawn this happens when their king is stuck in the corner. Give it a square, or lead with your king."),
    ("holdpawn", "Hold the draw against king and pawn", 2, "draw", 15, "kP",
     "Stay in front of their pawn. When the kings face each other with one square between, it's their move that hurts them.",
     ""),
    ("queenpawn", "Queen against a pawn on the seventh", 3, "mate", 20, "KQp",
     "Check from the side and from the front until their king has to stand in front of its pawn; then bring your king one step closer.",
     "Stalemate. With a rook's or bishop's pawn this is their drawing trick: leave their king a square."),
]
ENDING = {e[0]: e for e in ENDINGS}


def tb(fen):
    """The tablebase's verdict for the side to move ("win", "draw", "loss"...) and its moves, best first; None when
    it can't be reached (no internet): the engine decides instead."""
    key = " ".join(fen.split()[:4])
    if key in _TB:
        return _TB[key]
    import urllib.request
    try:
        req = urllib.request.Request(TABLEBASE + fen.replace(" ", "_"), headers={"User-Agent": "Knightwise (github.com/Abhra71/ChessCoach)"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            out = json.load(resp)
    except (OSError, ValueError):
        return None
    _TB[key] = out
    return out


def _wins(board):
    """Is the side to move winning? The tablebase if it answers, else the engine (at least +6)."""
    t = tb(board.fen())
    if t:
        return t.get("category") in ("win", "maybe-win")
    with live_engine.LOCK:
        return score_cp(live_engine.get().analyse(board, CHECK)["score"].pov(board.turn)) >= 600


def _drawn(board):
    t = tb(board.fen())
    if t:
        return t.get("category") in ("draw", "cursed-win", "blessed-loss")
    with live_engine.LOCK:
        return abs(score_cp(live_engine.get().analyse(board, CHECK)["score"].white())) <= 60


def _memory():
    try:
        return json.loads(FILE.read_text())
    except (OSError, ValueError):
        return {}


def done(eid):
    mem = _memory()
    mem[eid] = mem.get(eid, 0) + 1
    FILE.parent.mkdir(parents=True, exist_ok=True)
    FILE.write_text(json.dumps(mem))
    return mem[eid]


def listing():
    mem = _memory()
    return [{"id": e[0], "name": e[1], "level": e[2], "goal": e[3], "limit": e[4], "idea": e[6], "solved": mem.get(e[0], 0)}
            for e in ENDINGS]


def _random_position(pieces, rng):
    """A legal position with these pieces: capitals are White (you), small letters Black. White to move."""
    board = chess.Board(None)
    squares = list(chess.SQUARES)
    rng.shuffle(squares)
    kinds = {"K": chess.KING, "Q": chess.QUEEN, "R": chess.ROOK, "P": chess.PAWN, "B": chess.BISHOP, "N": chess.KNIGHT}
    want = list(pieces) + (["k"] if "k" not in pieces else [])
    if "K" not in want:
        want.insert(0, "K")
    for p in want:
        for sq in squares:
            if board.piece_at(sq):
                continue
            rank = chess.square_rank(sq)
            if p in "Pp" and rank in (0, 7):
                continue
            board.set_piece_at(sq, chess.Piece(kinds[p.upper()], p.isupper()))
            break
    board.turn = chess.WHITE
    return board


def position(eid, rng=None):
    """A fresh position for this ending, checked by the engine. None if the ending is unknown."""
    e = ENDING.get(eid)
    if not e:
        return None
    rng = rng or random.Random()
    goal, pieces = e[3], e[5]
    for _ in range(400):
        board = _random_position(pieces, rng)
        if not board.is_valid() or board.is_game_over() or board.is_check():
            continue
        if eid == "queenpawn":  # their pawn one step from queening, its king near it
            pawn = next(sq for sq, p in board.piece_map().items() if p.symbol() == "p")
            if chess.square_rank(pawn) != 1:
                continue
        if eid == "pawn":  # the pawn starts back (rank 2 to 4) and their king is near it: it takes technique
            pawn = next(sq for sq, p in board.piece_map().items() if p.symbol() == "P")
            if chess.square_rank(pawn) not in (1, 2, 3) or chess.square_distance(pawn, board.king(chess.BLACK)) > 3:
                continue
        if eid in ("queen", "rook", "tworooks"):  # their king starts away from the edge, so there's work to do
            k = board.king(chess.BLACK)
            if chess.square_file(k) in (0, 7) or chess.square_rank(k) in (0, 7):
                continue
        if not _wins(board):
            continue  # it must be a win to convert
        return {"fen": board.fen(), "flip": False}
    return None


def defend_position(rng=None):
    """For "hold the draw": you have the lone king (Black), they have king and pawn, and it's a draw with best play."""
    rng = rng or random.Random()
    for _ in range(400):
        board = _random_position("KPk", rng)
        if not board.is_valid() or board.is_game_over() or board.is_check():
            continue
        pawn = next(sq for sq, p in board.piece_map().items() if p.symbol() == "P")
        if chess.square_rank(pawn) not in (2, 3, 4) or chess.square_file(pawn) in (0, 7):
            continue
        board.turn = chess.BLACK
        if not board.is_valid() or board.is_check():
            continue
        if _drawn(board):
            return {"fen": board.fen(), "flip": True}
    return None


def start(eid, rng=None):
    e = ENDING.get(eid)
    if not e:
        return None
    pos = defend_position(rng) if e[3] == "draw" else position(eid, rng)
    if not pos:
        return None
    you = chess.Board(pos["fen"]).turn
    limit = e[4]
    t = tb(pos["fen"]) if e[3] == "mate" else None
    if t and isinstance(t.get("dtm"), int):  # perfect play needs this many moves: give five more, never fewer than usual
        limit = max(limit, (abs(t["dtm"]) + 1) // 2 + 5)
    return {**pos, "id": eid, "name": e[1], "goal": e[3], "limit": limit, "idea": e[6], "white": you == chess.WHITE,
            "legal": [m.uci() for m in chess.Board(pos["fen"]).legal_moves]}


def _value(board, you):
    """The engine's view for you: centipawns, mate counts as 10,000."""
    with live_engine.LOCK:
        info = live_engine.get().analyse(board, CHECK)
    return score_cp(info["score"].pov(you))


def play(eid, fen, uci, made, limit=None):
    """Your move, the engine's check of it, and the defender's best answer. None for an illegal move."""
    e = ENDING.get(eid)
    if not e:
        return None
    board = chess.Board(fen)
    you = board.turn
    try:
        move = chess.Move.from_uci(uci)
    except ValueError:
        return None
    if move not in board.legal_moves:
        move = chess.Move(move.from_square, move.to_square, chess.QUEEN)
        if move not in board.legal_moves:
            return None
    goal, limit = e[3], max(e[4], min(int(limit or e[4]), 40))
    first = tb(board.fen())
    before = None if first else _value(board, you)
    before_ok = bool(first) and (first.get("category") in ("win", "maybe-win") if goal != "draw"
                                 else first.get("category") in ("draw", "cursed-win", "blessed-loss"))
    san = board.san(move)
    board.push(move)
    made += 1
    out = {"mine": {"uci": move.uci(), "san": san, "fen": board.fen()}, "made": made, "reply": None, "say": None,
           "over": False, "result": None, "warn": None}

    def end(result, say):
        out.update(over=True, result=result, say=say, fen=board.fen(), legal=[])
        if result == "win":
            out["solved"] = done(eid)
        return out
    if board.is_checkmate():
        return end("win", f"Checkmate in {made} moves. That's how it's done.")
    if board.is_stalemate():
        return end("stalemate", e[7] or "Stalemate.")
    if goal == "promote" and move.promotion:
        return end("win", f"{san}: a new queen, in {made} moves. From here it's the queen mate you know.")
    t = tb(board.fen())  # now from their side: "loss" means you're still winning
    if t:
        theirs = t.get("category")
        if goal in ("mate", "promote") and before_ok and theirs not in ("loss", "maybe-loss"):
            out["warn"] = "Careful: that move throws the win away. Take it back and look again."
        if goal == "draw" and before_ok and theirs in ("win", "maybe-win"):
            out["warn"] = "That move loses: their pawn gets through now. Take it back and look again."
    else:
        after = _value(board, you)
        if goal in ("mate", "promote") and before >= 600 and after < 300:
            out["warn"] = "Careful: that move throws the win away. Take it back and look again."
        if goal == "draw" and before > -200 and after < -500:
            out["warn"] = "That move loses: their pawn gets through now. Take it back and look again."
    best = t and t.get("moves")
    if best:  # the defender plays the tablebase's best move
        reply = chess.Move.from_uci(best[0]["uci"])
    else:
        with live_engine.LOCK:
            reply = live_engine.get().play(board, DEFENCE).move
    out["reply"] = {"uci": reply.uci(), "san": board.san(reply)}
    board.push(reply)
    if board.is_insufficient_material() and goal != "draw":
        return end("lost", "They took your last piece that could win. Try again: the idea is in the box.")
    if goal == "draw" and (board.is_insufficient_material() or made >= limit):
        return end("win", "Draw held. Exactly right: stay in front of the pawn.")
    if goal == "draw" and any(p.piece_type == chess.QUEEN for p in board.piece_map().values()):
        return end("lost", "Their pawn became a queen. Try again: stay in front of it.")
    if made >= limit:
        return end("limit", f"{limit} moves and no {'checkmate' if goal == 'mate' else 'queen'} yet. Try again with the idea in the box.")
    out.update(fen=board.fen(), legal=[m.uci() for m in board.legal_moves])
    return out
