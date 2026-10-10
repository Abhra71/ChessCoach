import random

import chess
import pytest

from coach import play
from coach.analyze import open_engine


@pytest.fixture(scope="module")
def engine():
    eng = open_engine()
    yield eng
    eng.quit()


def test_hanging_the_queen_pauses_for_the_player_then_takeback(engine):
    game = play.Game("white", 3)
    game.board = chess.Board("4k3/8/3p4/8/3Q4/8/8/4K3 w - - 0 1")  # Qe5?? walks into the d6 pawn
    out = game.player_move(engine, "d4e5")
    assert out["waiting"] and out["verdict"]["mistake"]
    assert "takes" not in out["verdict"]["played_does"]  # Qe5 itself takes nothing
    assert out["turn"] == "black"  # the opponent has not moved yet
    back = game.takeback()
    assert back["fen"].startswith("4k3/8/3p4/8/3Q4/8/8/4K3 w") and back["takebacks"] == 1


def test_good_move_gets_a_reply(engine):
    game = play.Game("white", 1)
    out = game.player_move(engine, "e2e4")
    assert "waiting" not in out and out["turn"] == "white" and out["their_move"]
    assert len(out["moves"]) == 2


def test_illegal_move_refused(engine):
    game = play.Game("white", 1)
    with pytest.raises(ValueError):
        game.player_move(engine, "e2e5")


def test_engine_opens_when_player_is_black(engine):
    game = play.Game("black", 2)
    out = game.reply(engine, random.Random(3))
    assert out["turn"] == "black" and len(out["moves"]) == 1
