"""Sparring: the opponent plays the moves this player really chose, while their games last."""
import random

import chess

from coach import spar

PGN = "1. e4 c5 2. Nf3 d6 3. d4 cxd4 *"


def game(white, black):
    return {"white": {"username": white}, "black": {"username": black}, "pgn": PGN}


def test_their_book_is_only_their_own_moves():
    b = spar.book("x", [game("x", "me"), game("x", "me"), game("me", "x")])
    start = spar._key(chess.Board())
    assert b["white"][start] == {"e2e4": 2}  # as White they open 1.e4
    after_e4 = chess.Board()
    after_e4.push_san("e4")
    assert b["black"][spar._key(after_e4)] == {"c7c5": 1}  # as Black, their Sicilian (once)
    assert spar._key(chess.Board()) not in b["black"]


def test_their_usual_move_while_their_games_last(monkeypatch):
    games = [game("x", "me")] * 3
    monkeypatch.setattr(spar.prep, "games_of", lambda user: games)
    move, source, n = spar._their_move("x", chess.Board(), "white", 1200, random.Random(0))
    assert (move.uci(), source, n) == ("e2e4", "book", 3)
    off = chess.Board("4k3/8/8/8/8/8/8/4K2R w K - 0 1")  # a position they never reached
    monkeypatch.setattr(spar.rematch, "pick", lambda board, rating, rng: next(iter(board.legal_moves)))
    move, source, n = spar._their_move("x", off, "white", 1200, random.Random(0))
    assert source in ("human", "engine") and n is None
