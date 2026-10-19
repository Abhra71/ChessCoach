import chess

from coach import endgames


def no_tablebase(monkeypatch):
    monkeypatch.setattr(endgames, "tb", lambda fen: None)  # offline: the engine decides


def test_a_stalemate_is_caught_with_the_tip(monkeypatch):
    no_tablebase(monkeypatch)
    r = endgames.play("queen", "k7/8/1K6/8/8/8/8/2Q5 w - - 0 1", "c1c7", 3)
    assert r["over"] and r["result"] == "stalemate" and "still have a square" in r["say"]


def test_checkmate_wins_and_counts(monkeypatch, tmp_path):
    no_tablebase(monkeypatch)
    monkeypatch.setattr(endgames, "FILE", tmp_path / "e.json")
    r = endgames.play("queen", "k7/8/1K6/8/8/8/8/2Q5 w - - 0 1", "c1c8", 3)
    assert r["result"] == "win" and r["solved"] == 1 and "4 moves" in r["say"]


def test_giving_the_queen_away_is_said_at_once(monkeypatch):
    no_tablebase(monkeypatch)
    r = endgames.play("queen", "8/8/8/8/4k3/8/4K3/3Q4 w - - 0 1", "d1d4", 0)
    assert r["warn"] and r["result"] == "lost"


def test_an_illegal_move_is_refused():
    assert endgames.play("queen", "8/8/8/8/4k3/8/4K3/3Q4 w - - 0 1", "d1h8", 0) is None
    assert endgames.start("nope") is None
