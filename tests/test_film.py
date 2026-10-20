"""Your game as a 3D film (1.0): the script follows the real game, and slows down only for the moves that won it."""
import chess

from coach import film

PGN = ('[Termination "gushynanda won by checkmate"]\n\n1. e4 e5 2. Qh5 Nc6 3. Bc4 Nf6 4. Qxf7# 1-0')
GAME = {"url": "https://www.chess.com/game/live/42", "pgn": PGN, "end_time": 1792000000, "rules": "chess",
        "white": {"username": "gushynanda", "result": "win"}, "black": {"username": "them", "result": "checkmated"}}


def test_the_film_follows_the_real_game_and_ends_on_the_win(monkeypatch):
    monkeypatch.setattr(film.insights, "_games", lambda: [GAME])
    monkeypatch.setattr(film.insights, "_player", lambda: "gushynanda")
    monkeypatch.setattr(film.insights, "_moves", lambda: {})
    s = film.script("42")
    assert [m["san"] for m in s["moves"]] == ["e4", "e5", "Qh5", "Nc6", "Bc4", "Nf6", "Qxf7#"]
    last = s["moves"][-1]
    assert last["slow"] and last["capture"] == "f7" and last["caption"] == "Move 4. Your queen takes their pawn on f7: checkmate!"
    assert not any(m.get("slow") for m in s["moves"][:-1])  # no turning points known: only the last move slows down
    assert s["end"] == "Checkmate. You won." and s["you"] == "white" and 0.55 <= s["quiet"] <= 1.0


def test_castling_moves_the_rook_and_a_promotion_says_so():
    b = chess.Board("4k3/P7/8/8/8/8/8/R3K2R w KQ - 0 1")
    assert film._caption(b, b.parse_san("O-O"), 40) == "Move 21. You castle short."
    assert film._caption(b, b.parse_san("a8=Q+"), 40) == "Move 21. Your pawn goes to a8 and becomes a queen: check!"
