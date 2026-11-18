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


def test_the_first_look_is_two_rounds_on_any_pc(monkeypatch):
    """18 Nov self-test: 20 games were 3 rounds of checks here and 7 on a 4-core laptop. Two rounds, 6 to 20 games."""
    for cores, want in ((2, 6), (4, 6), (8, 14), (12, 16), (32, 16)):
        monkeypatch.setattr(analyze.os, "cpu_count", lambda c=cores: c)
        assert analyze.first_look() == want, cores


def test_practice_positions_are_worked_out_side_by_side_and_kept(tmp_path, monkeypatch):
    """18 Nov self-test: 12 positions took 40 s one after another. Several engines at once; the cache still answers."""
    import threading
    from coach import drills
    monkeypatch.setattr(drills, "CACHE", tmp_path / "drill-cache.json")
    monkeypatch.setattr(drills, "_cache", None)
    engines, seen = [], set()

    class Eng:
        def __enter__(self):
            engines.append(self)
            return self

        def __exit__(self, *a):
            return False

        def configure(self, opts):
            pass

    def fake(eng, pattern, r):
        seen.add(threading.get_ident())
        return {"id": drills.drill_id(r), "pattern": pattern}
    monkeypatch.setattr(drills, "open_engine", Eng)
    monkeypatch.setattr(drills, "_drill", fake)
    monkeypatch.setattr(drills.os, "cpu_count", lambda: 12)
    chosen = [("hang", {"url": "u", "ply": i, "fen": "f"}) for i in range(12)]
    got = drills.many(chosen)
    assert [d["id"] for d in got] == [f"u#{i}" for i in range(12)]  # in order
    assert len(engines) == 5  # (12 - 1) // 2 engines
    engines.clear()
    assert drills.many(chosen) == got and engines == []  # all kept: no engine opened
