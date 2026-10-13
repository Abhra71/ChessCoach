"""The chess.com self-check (coach/health.py) and the API check in every download (coach/fetch.py)."""
import json
import urllib.error

import pytest

from coach import fetch, health


@pytest.fixture(autouse=True)
def tmp_files(tmp_path, monkeypatch):
    monkeypatch.setattr(health, "FILE", tmp_path / "health.json")
    monkeypatch.setattr(fetch, "DATA", tmp_path)


GAME = {"url": "https://www.chess.com/game/live/1", "pgn": "1. e4 *", "end_time": 1, "time_class": "rapid",
        "rules": "chess", "white": {"username": "a", "rating": 400, "result": "win"},
        "black": {"username": "b", "rating": 400, "result": "resigned"}}


def test_all_working_then_one_breaks_then_it_is_fixed():
    assert health.summary() == {"ok": True, "broken": [], "verified": None, "seen": []}
    health.record("board", True, now=100)
    health.record("game-address", True, now=110)
    assert health.summary()["ok"] and health.summary()["verified"] == 110
    health.record("game-address", False, "unknown: /newgame/<id>", now=200)
    s = health.summary()
    assert not s["ok"] and s["broken"][0]["check"] == "game-address" and s["broken"][0]["since"] == 200
    assert "Open them in Knightwise" in health.says("game-address")
    assert health.says("board") is None  # the rest keeps working
    health.record("game-address", True, now=300)
    assert health.summary()["ok"] and health.says("game-address") is None


def test_only_known_checks_are_kept():
    assert not health.record("anything-else", False, "x")
    assert health.summary()["seen"] == []


def test_api_shape_is_checked():
    assert health.missing_fields({"games": [GAME]}) == []
    assert health.missing_fields({"games": []}) == []
    broken = dict(GAME, white={"username": "a", "result": "win"})
    del broken["pgn"]
    assert health.missing_fields({"games": [broken]}) == ["pgn", "white.rating"]
    assert health.missing_fields({"items": []}) == ["games"]
    assert health.missing_fields(None) == ["games"]


def answers(monkeypatch, replies):
    def get_json(url):
        r = replies[url.rsplit("/", 1)[-1] if "archives" in url else "month"]
        if isinstance(r, Exception):
            raise r
        return r
    monkeypatch.setattr(fetch, "get_json", get_json)


def test_download_records_a_working_api(monkeypatch, tmp_path):
    answers(monkeypatch, {"archives": {"archives": ["https://api.chess.com/pub/player/x/games/2026/10"]},
                          "month": {"games": [GAME]}})
    assert fetch.fetch("x") == 1
    assert {c: e["ok"] for c, e in json.loads(health.FILE.read_text()).items()} == {"api-archives": True,
                                                                                   "api-games": True}


def test_changed_api_keeps_the_last_good_copy(monkeypatch, tmp_path):
    (tmp_path / "games-2026-10.json").write_text(json.dumps({"games": [GAME]}))
    answers(monkeypatch, {"archives": {"archives": ["https://api.chess.com/pub/player/x/games/2026/10"]},
                          "month": {"games": [{"id": 5}]}})
    fetch.fetch("x")
    assert json.loads((tmp_path / "games-2026-10.json").read_text()) == {"games": [GAME]}
    assert "api-games" in [b["check"] for b in health.summary()["broken"]]


def test_api_down_is_reported_but_no_internet_is_not(monkeypatch):
    answers(monkeypatch, {"archives": urllib.error.HTTPError("u", 503, "down", {}, None)})
    with pytest.raises(urllib.error.HTTPError):
        fetch.fetch("x")
    assert health.summary()["broken"][0]["detail"] == "HTTP 503"
    health.FILE.unlink()
    answers(monkeypatch, {"archives": urllib.error.URLError("no network")})
    with pytest.raises(urllib.error.URLError):
        fetch.fetch("x")
    assert health.summary()["seen"] == []  # the player's internet is off: not chess.com's fault
    answers(monkeypatch, {"archives": urllib.error.HTTPError("u", 404, "no such player", {}, None)})
    with pytest.raises(urllib.error.HTTPError):
        fetch.fetch("x")
    assert health.summary()["seen"] == []  # a mistyped username isn't a broken service
