"""Findings from the review of 0.6 to 0.9 (26 Oct), kept fixed."""
from coach import fixes


def test_a_bad_edit_of_the_fix_file_is_ignored_not_a_crash(tmp_path, monkeypatch):
    monkeypatch.setattr(fixes, "FILE", tmp_path / "fixes.json")
    assert fixes.clean({"boards": 5, "off": 1, "nav": {"a": 3}})["boards"] == []
    out = fixes.refresh(force=True, fetch=lambda: {"boards": 5, "off": "talk", "game_addresses": ["x"]})
    assert out["boards"] == [] and out["off"] == [] and out["game_addresses"] == ["x"]


def test_a_week_that_came_out_short_keeps_its_best(tmp_path, monkeypatch):
    from coach import guess
    monkeypatch.setattr(guess, "FILE", tmp_path / "guess.json")
    wk = guess.week()
    guess._save({"week": wk, "positions": [{"fen": "x"}] * 4, "best": 320, "tries": 2})
    monkeypatch.setattr(guess, "build", lambda w: (_ for _ in ()).throw(AssertionError("rebuilt")))
    assert guess.challenge()["best"] == 320
