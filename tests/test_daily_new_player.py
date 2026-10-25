"""Today's 5 minutes for a brand-new chess.com account (26 Oct): three puzzles on the basics, not one; players with
games keep exactly the set they had."""
import random
from datetime import date

from coach import daily, memory, plan


def setup(tmp_path, monkeypatch):
    monkeypatch.setattr(daily, "FILE", tmp_path / "daily.json")
    monkeypatch.setattr(daily, "_own", lambda focus, rng, today=None: None)
    monkeypatch.setattr(memory, "seen_before", lambda today=None: set())
    monkeypatch.setattr(plan, "_puzzles", lambda theme, rating, rng, avoid=None:
                        [{"id": f"p-{theme}", "intro": f"A {theme} puzzle.", "kind": "puzzle"}])


def test_a_new_player_gets_three_different_puzzles(tmp_path, monkeypatch):
    setup(tmp_path, monkeypatch)
    out = daily.challenge({"player": "new", "games": 0}, games=[], today=date(2026, 10, 26))
    ids = [d["id"] for d in out["drills"]]
    assert len(ids) == 3 and len(set(ids)) == 3
    assert out["drills"][1]["intro"].startswith("Also today: ")


def test_a_player_with_games_keeps_the_set_as_it_was(tmp_path, monkeypatch):
    setup(tmp_path, monkeypatch)
    out = daily.challenge({"player": "me", "games": 120}, games=[], today=date(2026, 10, 26))
    assert len(out["drills"]) == 1  # their own position and opening come from their games: nothing added
