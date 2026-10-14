"""The human-move model: Maia's chances for each move, by rating (needs engine/lc0 and engine/maia)."""
import random

import chess
import pytest

from coach import maia

pytestmark = pytest.mark.skipif(not maia.available(), reason="Leela and Maia aren't downloaded")
TWO_KNIGHTS = "r1bqkb1r/pppp1ppp/2n2n2/4p1N1/2B1P3/8/PPPP1PPP/RNBQK2R b KQkq - 5 4"


@pytest.fixture(autouse=True)
def _close():
    yield
    maia.close()


def test_stronger_players_find_the_main_move_more_often():
    board = chess.Board(TWO_KNIGHTS)
    low, high = maia.policy(board, 1100), maia.policy(board, 1900)
    d5 = board.parse_san("d5")
    assert 90 <= sum(low.values()) <= 101
    assert high[d5] > low[d5]  # 14 Oct: 34% at 1,100, 57% at 1,900


def test_the_review_line_compares_your_level_with_the_next():
    line = maia.compare(TWO_KNIGHTS, "Qe7", "d5", 1100)
    assert line.startswith("At about 1,100,") and "at 1,500" in line and "d5" in line
    assert maia.compare(TWO_KNIGHTS, "Qe7", "d5", 211).startswith("At 1,100, a level ahead of you,")


def test_a_human_move_is_a_legal_one():
    board = chess.Board()
    assert maia.pick(board, 1300, random.Random(1)) in board.legal_moves


def test_nearest_level():
    assert (maia.nearest(211), maia.nearest(1449), maia.nearest(2400)) == (1100, 1400, 1900)
