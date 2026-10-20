"""Spar against a player you'll meet (0.11, with prep): their own openings, then human moves at their rating.

The opponent plays the moves this player really chose in their public games (chess.com, the last three months), as
long as the game follows a position they've reached at least twice; after that, Maia plays on at their rating
(coach/maia.py, Maia-3: on unless switched off in Settings), or else Stockfish weakened to about their level (coach/rematch.py).
It's someone who opens like them and plays like players of their rating: not the person, and the page says so.
Fair play: for before a game only.
"""
import collections
import io
import random

import chess
import chess.pgn

from coach import prep, rematch

BOOK_PLIES = 16  # their first 8 moves each
BOOK_MIN = 2  # a position they've reached at least twice


def _key(board):
    return " ".join(board.fen().split()[:4])


_BOOK = {}  # (user, id of their games list) -> book, so it's read once per hour, not once per move


def book(user, games):
    """{"white"|"black": {position: Counter(move)}}: what this player played, by the side they had."""
    key = (user, id(games))
    if key in _BOOK:
        return _BOOK[key]
    _BOOK.clear()
    _BOOK[key] = out = _book(user, games)
    return out


def _book(user, games):
    out = {"white": collections.defaultdict(collections.Counter), "black": collections.defaultdict(collections.Counter)}
    for g in games:
        side = "white" if g["white"]["username"].lower() == user else "black"
        game = chess.pgn.read_game(io.StringIO(g.get("pgn") or ""))
        if not game:
            continue
        board = game.board()
        for move in list(game.mainline_moves())[:BOOK_PLIES]:
            if (board.turn == chess.WHITE) == (side == "white"):
                out[side][_key(board)][move.uci()] += 1
            board.push(move)
    return out


def _their_move(user, board, their_side, rating, rng):
    """(move, where it came from, how many games) for the opponent."""
    seen = book(user, prep.games_of(user))[their_side].get(_key(board))
    if seen and sum(seen.values()) >= BOOK_MIN:
        moves = list(seen)
        move = chess.Move.from_uci(rng.choices(moves, weights=[seen[m] for m in moves])[0])
        if move in board.legal_moves:
            return move, "book", seen[move.uci()]
    move = rematch.pick(board, rating, rng)
    return move, "human" if rematch._human(rating) else "engine", None


def _reply(user, board, their_side, rating, rng):
    if board.is_game_over(claim_draw=True):
        return None
    move, source, n = _their_move(user, board, their_side, rating, rng)
    out = {"uci": move.uci(), "san": board.san(move), "from": source, "games": n}
    board.push(move)
    return out


def start(user, my_side, rng=random):
    """A fresh game against them; when they're White, their first move is already played."""
    s = prep.cached(user)
    if not s:
        return None
    board, their = chess.Board(), "black" if my_side == "white" else "white"
    reply = _reply(user, board, their, s["rating"], rng) if their == "white" else None
    return {**rematch.state(board, my_side == "white"), "user": user, "rating": s["rating"], "color": my_side,
            "flip": my_side == "black", "reply": reply, "human": rematch._human(s["rating"])}


def play(user, fen, uci, my_side, rating, rng=random):
    """Your move, then theirs (from their games while they last). None when the move isn't legal."""
    board = chess.Board(fen)
    white = my_side == "white"
    if board.turn != white:
        return None
    try:
        move = chess.Move.from_uci(uci)
    except ValueError:
        return None
    if move not in board.legal_moves:
        move = chess.Move(move.from_square, move.to_square, chess.QUEEN)
        if move not in board.legal_moves:
            return None
    mine = board.san(move)
    board.push(move)
    mid = board.fen()
    reply = _reply(user, board, "black" if white else "white", rating, rng)
    return {**rematch.state(board, white), "mine": {"uci": move.uci(), "san": mine, "fen": mid}, "reply": reply}
