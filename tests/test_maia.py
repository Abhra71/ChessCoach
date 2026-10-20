"""The human-move model: Maia-3, run in numpy (needs engine/maia3/maia3-5m.npz: python -m coach.get_engine)."""
import json
import random

import chess
import pytest

from coach import maia
from coach.paths import PROJECT

pytestmark = pytest.mark.skipif(not maia.available(), reason="Maia-3 isn't downloaded")
TWO_KNIGHTS = "r1bqkb1r/pppp1ppp/2n2n2/4p1N1/2B1P3/8/PPPP1PPP/RNBQK2R b KQkq - 5 4"


def test_the_numpy_copy_predicts_strong_players_like_maia3_does():
    """The proof the copy of the model is faithful: on 6 games by 2,400+ players from Lichess Elite it matches about
    half their moves (51% on 24 games, 20 Oct 2026). A mistake anywhere in the copy drops it far below that."""
    elite = json.loads((PROJECT / "coach" / "library" / "elite.json").read_text())
    games = [g for s in elite["structures"].values() for g in s["games"]][:6]
    hit = n = 0
    for g in games:
        b = chess.Board()
        for ply, u in enumerate(g["moves"][:50]):
            m = chess.Move.from_uci(u)
            if ply >= 8:
                p = maia.policy(b, 2500)
                hit, n = hit + (max(p, key=p.get) == m), n + 1
            b.push(m)
    assert hit / n > 0.40, f"{hit}/{n}"


def test_stronger_players_find_the_main_move_more_often():
    board = chess.Board(TWO_KNIGHTS)
    low, high = maia.policy(board, 600), maia.policy(board, 1900)
    d5 = board.parse_san("d5")
    assert 99.9 <= sum(low.values()) <= 100.1
    assert high[d5] > low[d5]


def test_every_kind_of_move_has_its_place_including_promotions_and_black():
    for fen in ("8/P7/8/8/8/8/k7/4K3 w - - 0 1", "4k3/8/8/8/8/8/p7/K7 b - - 0 1", TWO_KNIGHTS, chess.STARTING_FEN):
        board = chess.Board(fen)
        p = maia.policy(board, 1500)
        assert set(p) == set(board.legal_moves) and abs(sum(p.values()) - 100) < 0.1
    promo = maia.policy(chess.Board("8/P7/8/8/8/8/k7/4K3 w - - 0 1"), 1500)
    assert max(promo, key=promo.get) == chess.Move.from_uci("a7a8q")  # a queen, as everyone would


def test_the_review_line_compares_your_level_with_the_next():
    line = maia.compare(TWO_KNIGHTS, "Qe7", "d5", 1100)
    assert line.startswith("At your level,") and "1,500" in line and "d5" in line


def test_a_human_move_is_a_legal_one_at_any_rating():
    board = chess.Board()
    for r in (100, 900, 2000):
        assert maia.pick(board, maia.lichess_rating(r), random.Random(1)) in board.legal_moves


def test_chess_com_ratings_become_lichess_ratings_going_up():
    rs = [maia.lichess_rating(r) for r in (0, 211, 800, 1500, 2600, 3000)]
    assert rs == sorted(rs) and rs[0] > 0


def test_how_hard_it_was_in_words():
    assert maia.hard_words(85).startswith("Most players")
    assert "normal at your level" in maia.hard_words(12)
    assert maia.hard_words(None) is None
