"""Blindfold by voice (1.0): the moves read out, a question with answers worked out from the real position."""
import chess
import pytest

from coach import blindfold

GAME = {"pgn": "1. e4 e5 2. Nf3 Nc6 3. Bc4 Nf6 4. Ng5 d5 5. exd5 Nxd5 6. Nxf7 *", "url": "u",
        "white": {"username": "gushynanda"}, "black": {"username": "them"}}


@pytest.fixture(autouse=True)
def own_file(tmp_path, monkeypatch):
    monkeypatch.setattr(blindfold, "FILE", tmp_path / "blindfold.json")
    monkeypatch.setattr(blindfold.insights, "home", lambda: {"player": "gushynanda"})


def test_moves_are_said_the_way_people_say_them():
    b = chess.Board("r1bqkb1r/pppp1ppp/2n2n2/4p1N1/2B1P3/8/PPPP1PPP/RNBQK2R w KQkq - 4 5")
    assert blindfold.spoken(b, b.parse_san("Bxf7+")) == "bishop takes f7, check"
    assert blindfold.spoken(b, b.parse_san("O-O")) == "castles short"
    assert blindfold.spoken(chess.Board(), chess.Move.from_uci("e2e4")) == "e4"
    assert blindfold._read_out([chess.Move.from_uci(u) for u in ("e2e4", "e7e5", "g1f3")]) == \
        "From the start. Move 1. White, e4. Black, e5. Move 2. White, knight f3."


def test_every_answer_is_right_in_the_real_position():
    import random
    for seed in range(8):
        it = blindfold.item(random.Random(seed), games=[GAME])
        board = chess.Board(it["fen"])
        assert it["plies"] == blindfold.START and it["kind"] == "where"  # short ones ask where a piece is
        for sq in it["answers"]:
            assert board.piece_at(chess.parse_square(sq)) is not None
        assert it["game"]["opponent"] == "them"


def test_right_makes_it_longer_wrong_shorter_and_a_peek_counts_for_nothing():
    assert blindfold.done(True) == {"plies": 6, "best": 4, "record": True}
    assert blindfold.done(True, peeked=True)["plies"] == 6
    assert blindfold.done(False)["plies"] == 4
    for _ in range(5):
        blindfold.done(False)
    assert blindfold.done(False)["plies"] == blindfold.LEAST


def test_a_spoken_square_is_worked_out_by_the_ai_and_checked():
    assert blindfold.heard_square("I think f three", ask_ai=lambda s, p, n: ("f3", "groq")) == "f3"
    assert blindfold.heard_square("no idea", ask_ai=lambda s, p, n: ("none", "groq")) is None
    assert blindfold.heard_square("x", ask_ai=lambda s, p, n: ("z9", "groq")) is None


def test_a_game_read_out_lately_waits_its_turn_and_the_next_badge_is_named():
    import random
    games = [dict(GAME, url=f"u{i}") for i in range(3)]
    seen = [blindfold.item(random.Random(s), games=games)["game"]["url"] for s in range(3)]
    assert sorted(seen) == ["u0", "u1", "u2"]  # three rounds, three different games
    assert blindfold.item(random.Random(9), games=games)["goal"] == {"moves": 3, "name": "Bronze"}
