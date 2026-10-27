"""The first start on a new PC (27 Oct 2026): 148 games took 25 minutes before Home opened, a helper process's broken
pipe said "Can't reach chess.com", and a slow chess.com wasn't tried again."""
import json
import urllib.error

import pytest

from coach import analyze, fetch


def _games(tmp_path, monkeypatch, n):
    monkeypatch.setattr(analyze, "DATA", tmp_path)
    monkeypatch.setattr(analyze, "MOVES", tmp_path / "moves.jsonl")
    monkeypatch.setattr(analyze, "CHECKED", tmp_path / "checked.txt")
    (tmp_path / "player.txt").write_text("me")
    games = [{"url": f"https://www.chess.com/game/live/{i}", "end_time": 1000 + i, "rules": "chess",
              "pgn": "", "white": {"username": "me"}, "time_class": "rapid"} for i in range(n)]
    (tmp_path / "games-2026-10.json").write_text(json.dumps({"games": games}))


class _Pool:  # the checker's process pool, in this process
    def __init__(self, **k):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def map(self, f, games, players):
        return [[{"url": g["url"]}] for g in games]


def test_the_newest_games_are_checked_first_and_the_rest_wait(tmp_path, monkeypatch):
    _games(tmp_path, monkeypatch, 30)
    monkeypatch.setattr(analyze, "ProcessPoolExecutor", _Pool)
    assert [g["end_time"] for g in analyze.unchecked()][:3] == [1029, 1028, 1027]
    assert analyze.main(argv=[], limit=analyze.FIRST_LOOK) == analyze.FIRST_LOOK
    left = analyze.unchecked()
    assert len(left) == 10 and max(g["end_time"] for g in left) == 1009  # the oldest ten are still waiting
    assert analyze.main(argv=[]) == 10 and analyze.unchecked() == []


def test_progress_is_saved_after_every_game(tmp_path, monkeypatch):
    """A hiccup halfway keeps the games already checked: they are never checked (and counted) twice."""
    _games(tmp_path, monkeypatch, 5)

    class Broken(_Pool):
        def map(self, f, games, players):
            def rows():
                for i, g in enumerate(games):
                    if i == 3:
                        raise BrokenPipeError("a helper process went away")
                    yield [{"url": g["url"]}]
            return rows()

    monkeypatch.setattr(analyze, "ProcessPoolExecutor", Broken)
    with pytest.raises(BrokenPipeError):
        analyze.main(argv=[])
    assert len(analyze.checked_games()) == 3 and len(analyze.unchecked()) == 2


def test_a_busy_chess_com_is_tried_again_and_an_unknown_player_is_not(monkeypatch):
    calls = []

    class Answer:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return b'{"ok": 1}'

    def urlopen(req, timeout):
        calls.append(req.full_url)
        if len(calls) < 3:
            raise urllib.error.HTTPError(req.full_url, 429, "Too Many Requests", {}, None)
        return Answer()

    monkeypatch.setattr(fetch.urllib.request, "urlopen", urlopen)
    monkeypatch.setattr(fetch.time, "sleep", lambda s: None)
    assert fetch.get_json("https://api.chess.com/x") == {"ok": 1} and len(calls) == 3

    calls.clear()

    def unknown(req, timeout):
        calls.append(1)
        raise urllib.error.HTTPError(req.full_url, 404, "Not Found", {}, None)

    monkeypatch.setattr(fetch.urllib.request, "urlopen", unknown)
    with pytest.raises(urllib.error.HTTPError):
        fetch.get_json("https://api.chess.com/nobody")
    assert len(calls) == 1
