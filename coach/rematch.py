"""Rematch your loss (flagship 4): play a game you didn't win again from the moment it went wrong.

The board starts just before the move that cost the most, exactly as it stood in the real game. You play something
better; from there Stockfish plays on for your opponent, weakened to about their level: it picks among its best few
moves with a spread that grows as the rating falls, and now and then plays a loose move, the way club players do.
That's an approximation of a level, not a copy of the person, and the app says so.
With the human-move model (coach/maia.py, Maia-3 since 20 Oct 2026; on unless switched off in Settings), the
opponent plays like real players of their rating instead, at any rating.
"""
import math
import random

import chess
import chess.engine

from coach import live_engine
from coach.analyze import score_cp

DEPTH = 8
CHOICES = 6


def spread(rating):
    """How far (in centipawns) from the best move the engine wanders: 300 at 400 and below, 20 at 2000+."""
    return max(20.0, min(300.0, (2000 - (rating or 800)) / 5))


def loose(rating):
    """The chance of a loose move, any legal one: 20% at 400 and below, 2% at 1800+."""
    return max(0.02, min(0.20, (1800 - (rating or 800)) / 7000))


def pick(board, rating, rng=random):
    """The opponent's move at about this (chess.com) rating: the human-move model's moves when it's on, otherwise
    Stockfish weakened as below."""
    legal = list(board.legal_moves)
    if len(legal) == 1:
        return legal[0]
    from coach import maia
    if _human(rating):
        try:
            move = maia.pick(board, maia.lichess_rating(rating), rng)
            if move:
                return move
        except Exception:  # the model failed: fall back to the weakened Stockfish
            pass
    if rng.random() < loose(rating):
        return rng.choice(legal)
    with live_engine.LOCK:
        infos = live_engine.get().analyse(board, chess.engine.Limit(depth=DEPTH), multipv=min(CHOICES, len(legal)))
    scored = [(info["pv"][0], score_cp(info["score"].pov(board.turn))) for info in infos if info.get("pv")]
    best = max(cp for _, cp in scored)
    weights = [math.exp((cp - best) / spread(rating)) for _, cp in scored]
    return rng.choices([m for m, _ in scored], weights=weights)[0]


def state(board, player_white):
    """What the page needs: the position, your legal moves, and how the game stands."""
    over, result = board.is_game_over(claim_draw=True), None
    if over:
        outcome = board.outcome(claim_draw=True)
        if outcome.winner is None:
            result = "stalemate" if outcome.termination == chess.Termination.STALEMATE else "draw"
        else:
            result = "win" if outcome.winner == player_white else "loss"
    return {"fen": board.fen(), "over": over, "result": result, "check": board.is_check(),
            "legal": [m.uci() for m in board.legal_moves] if not over and board.turn == player_white else []}


def play(fen, uci, rating, player_white):
    """Your move, then theirs. Returns the new state and their reply, or None when the move isn't legal."""
    board = chess.Board(fen)
    if board.turn != player_white:
        return None
    try:
        move = chess.Move.from_uci(uci)
    except ValueError:
        return None
    if move not in board.legal_moves:
        promo = chess.Move(move.from_square, move.to_square, chess.QUEEN)  # a pawn reaching the end: a queen
        if promo not in board.legal_moves:
            return None
        move = promo
    mine = board.san(move)
    board.push(move)
    mid = board.fen()  # after your move, before theirs: the page shows it first
    reply = None
    if not board.is_game_over(claim_draw=True):
        r = pick(board, rating)
        reply = {"uci": r.uci(), "san": board.san(r)}
        board.push(r)
    return {**state(board, player_white), "mine": {"uci": move.uci(), "san": mine, "fen": mid}, "reply": reply}


def end_say(result, real):
    """Maya's line when the rematch ends, against how the real game went ("loss" or "draw")."""
    if result == "win":
        return f"Checkmate! In the real game you {'lost' if real == 'loss' else 'drew'}. This time you won."
    if result == "draw":
        return ("A draw: half a point more than the real game." if real == "loss"
                else "A draw again. Try once more and look for the win.")
    if result == "stalemate":
        return "Stalemate, so it's a draw. When you're winning, leave their king a square before you close in."
    return "They won again. Try once more from the same moment: it gets easier."


def _human(rating):
    """Is the opponent played by the human-move model? At every rating since Maia-3 (20 Oct 2026)."""
    from coach import maia
    return maia.enabled()


def setup(gid, ply):
    """Where a rematch starts: the board just before your move at this ply, in a game you didn't win."""
    from coach import insights
    g = insights.game_detail(gid)
    if not g or g["result"] == "win" or not 1 <= ply < len(g["positions"]):
        return None
    board = chess.Board(g["positions"][ply - 1]["fen"])
    white = g["color"] == "white"
    if board.turn != white:
        return None
    return {**state(board, white), "game": g["id"], "ply": ply, "color": g["color"], "flip": not white,
            "opponent": g["opponent"], "rating": g["opponent_rating"], "real": g["result"], "human": _human(g["opponent_rating"]),
            "real_move": g["positions"][ply]["san"], "move_number": (ply + 1) // 2,
            "lead_in": [p["fen"] for p in g["positions"][max(0, ply - 6):ply]]}
