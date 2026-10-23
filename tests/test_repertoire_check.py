"""The repertoire re-check (24 Oct): after 50 new games and a month, a line you stopped playing or that goes badly."""
import json

from coach import repertoire

DAY = 86400
LINE = {"name": "Caro-Kann Defense: Main Line", "side": "black", "steps": [{"san": "e4"}, {"san": "c6"}, {"san": "d4"}]}


def game(t, my_answer, result="win"):
    return {"white": {"username": "x", "result": "win"}, "black": {"username": "me", "result": result},
            "end_time": t, "pgn": f"1. e4 {my_answer} 2. d4 *", "url": f"u{t}"}


def setup(tmp_path, monkeypatch, start):
    monkeypatch.setattr(repertoire, "FILE", tmp_path / "rep.json")
    monkeypatch.setattr(repertoire, "CHECK", tmp_path / "check.json")
    repertoire.FILE.write_text(json.dumps([LINE]))
    repertoire.CHECK.write_text(json.dumps({"at": start, "games": 0, "stale": []}))


def test_not_checked_before_50_games_and_a_month(tmp_path, monkeypatch):
    setup(tmp_path, monkeypatch, 0)
    games = [game(10 + i, "e5") for i in range(60)]
    assert repertoire.stale(games, "me", now=10 * DAY) == []  # 60 games but only 10 days


def test_a_line_you_stopped_playing_is_out_of_date(tmp_path, monkeypatch):
    setup(tmp_path, monkeypatch, 0)
    games = [game(10 + i, "e5") for i in range(55)] + [game(100 + i, "c6") for i in range(5)]
    out = repertoire.stale(games, "me", now=40 * DAY)
    assert [x["name"] for x in out] == ["Caro-Kann Defense: Main Line"] and "only 5 of your last 60" in out[0]["why"]
    assert repertoire.stale(games, "me", now=41 * DAY) == out  # kept until the next check


def test_a_line_you_still_play_and_win_with_stays(tmp_path, monkeypatch):
    setup(tmp_path, monkeypatch, 0)
    assert repertoire.stale([game(10 + i, "c6") for i in range(55)], "me", now=40 * DAY) == []
