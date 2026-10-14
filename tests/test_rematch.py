import random

import chess

from coach import rematch


def test_weaker_opponents_wander_further_and_play_loose_moves_more_often():
    assert rematch.spread(254) > rematch.spread(1200) > rematch.spread(2200)
    assert rematch.loose(254) > rematch.loose(1200) >= rematch.loose(2200)


def test_state_says_who_won_and_offers_only_your_legal_moves():
    mate = chess.Board("6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1")
    mate.push_san("Ra8#")
    assert rematch.state(mate, True)["result"] == "win" and rematch.state(mate, True)["legal"] == []
    stale = chess.Board("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")
    assert rematch.state(stale, True)["result"] == "stalemate"
    start = chess.Board()
    assert len(rematch.state(start, True)["legal"]) == 20 and rematch.state(start, False)["legal"] == []


def test_an_illegal_move_is_refused():
    assert rematch.play(chess.STARTING_FEN, "e2e5", 800, True) is None
    assert rematch.play(chess.STARTING_FEN, "e7e5", 800, True) is None  # not your piece


def test_the_end_line_compares_with_the_real_game():
    assert "This time you won" in rematch.end_say("win", "loss")
    assert "half a point more" in rematch.end_say("draw", "loss")
    assert "look for the win" in rematch.end_say("draw", "draw")
