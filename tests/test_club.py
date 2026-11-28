"""Storyline steps 3.3 to 3.6 (28 Nov): the coaches' memories (each once, one a week per coach, at the moment it fits),
the club's story moments, "on this day" (sourced, weekly at most, never twice) and the chess words."""
import datetime
import json
import time

from coach import memories, nudge, story, words
from tests.test_nudge import HOME, fresh

DAY = datetime.date(2026, 12, 2)
QUIET = {**HOME, "last_game": {}, "daily": {"done_today": True}}
ME = "me"


def game(i, result="loss", end=None):
    me = {"username": ME, "result": "win" if result == "win" else "resigned"}
    them = {"username": f"Opp{i}", "result": "resigned" if result == "win" else "win"}
    return {"url": f"https://www.chess.com/game/live/{i}", "end_time": end or time.time() - 3600 * (i + 1),
            "white": me, "black": them, "pgn": ""}


def said(day=DAY, home=QUIET, games=None, n=3, **kw):
    return [p for p in (nudge.pick("app", "home", home, day, games=games, player=ME, **kw) for _ in range(n)) if p]


def test_viktors_regret_is_told_once_when_in_your_head_first_opens(tmp_path, monkeypatch):
    first = memories.on_page("calc")
    assert first["coach"] == "viktor" and "a move I didn't check" in first["line"]
    assert memories.on_page("calc") == first  # left before it was shown: it waits for the next time
    assert memories.told_on_page(first["id"], DAY)
    assert memories.on_page("calc") is None  # shown: never again
    assert memories.on_page("repertoire")["coach"] == "maya"
    assert memories.on_page("games") is None and not memories.told_on_page("welcome")


def test_welcome_to_the_club_on_the_first_day_only(tmp_path, monkeypatch):
    fresh(tmp_path, monkeypatch, club=True)
    first = said(n=1)[0]
    assert first["kind"] == "story" and first["line"].startswith("Welcome to the club") and first["voice"] == "maya"
    assert not any(p["id"] == "welcome" for p in said(DAY + datetime.timedelta(days=1)))


def test_the_club_notices_a_streak_and_a_hundred_games(tmp_path, monkeypatch):
    fresh(tmp_path, monkeypatch, club=True)
    memories.told("welcome")
    home = {**QUIET, "games": 140, "daily": {"done_today": True, "streak": 7}}
    first = said(home=home, n=1)[0]
    assert first["kind"] == "story"  # one story moment a day, before everything else that day
    assert {first["id"]} <= {"streak-7", "hundred"}
    other = said(DAY + datetime.timedelta(days=1), home=home, n=1)[0]
    assert {first["id"], other["id"]} == {"streak-7", "hundred"} and other["voice"] in ("maya", "viktor")


def test_a_memory_at_most_once_a_week_per_coach(tmp_path, monkeypatch):
    fresh(tmp_path, monkeypatch, club=True)
    from coach import insights
    memories.told("welcome")
    games = [game(i) for i in range(35)]  # 35 games, the last 5 lost, the last one fresh
    monkeypatch.setattr(insights, "_moves", lambda: {g["url"]: [] for g in games})
    home = {**QUIET, "last_game": {"end_time": time.time() - 3600, "result": "loss"}}
    got = memories.candidates(home, games, ME, DAY, {})
    ids = {c[1] for c in got}
    assert {"maya-streak", "viktor-notebook"} <= ids
    memories.told("maya-streak", DAY)
    later = {c[1] for c in memories.candidates(home, games, ME, DAY + datetime.timedelta(days=3), {})}
    assert "maya-streak" not in later  # told
    assert memories.clock_memory({"clock": {"big": 10, "fast": 5}}, DAY + datetime.timedelta(days=3)) is None  # Maya: a week
    assert memories.clock_memory({"clock": {"big": 10, "fast": 5}}, DAY + datetime.timedelta(days=8))
    assert "viktor-notebook" in later  # Viktor hasn't said one this week


def test_maya_remembers_her_queen_when_you_leave_yours(tmp_path, monkeypatch):
    from coach import insights
    g = game(1)
    row = {"pattern": "left a piece hanging", "fen": "4k3/8/8/1b6/8/8/8/3QK3 w - - 0 1", "move": "Qa4",
           "reply_pv": ["e8d8"]}  # they didn't take it
    hung = {**row, "move": "Qb3", "reply_pv": ["b5c4"]}  # a queen attacked, not taken: not this memory
    real = {"pattern": "left a piece hanging", "fen": "4k3/8/8/1b6/8/8/8/3QK3 w - - 0 1", "move": "Qa4",
            "reply_pv": ["b5a4"]}  # the bishop takes the queen
    assert not memories._queen_hung(row) and not memories._queen_hung(hung) and memories._queen_hung(real)
    monkeypatch.setattr(insights, "_moves", lambda: {g["url"]: [real]})
    home = {**QUIET, "last_game": {"end_time": time.time() - 3600, "result": "loss"}}
    assert "maya-queen" in {c[1] for c in memories.candidates(home, [g], ME, DAY, {})}


def test_on_this_day_is_real_sourced_weekly_and_never_twice():
    for month, d, year, what, src in memories.HISTORY:
        datetime.date(year, month, d)  # a real date
        assert src.startswith("https://en.wikipedia.org/wiki/") and what.endswith(".")
    hid, line, src = memories.on_this_day(datetime.date(2026, 12, 12))
    assert line.startswith("On this day in 2024: Gukesh") and "World_Chess_Championship_2024" in src
    memories.told(hid, datetime.date(2026, 12, 12))
    assert memories.on_this_day(datetime.date(2026, 12, 13)) is None  # a week between
    late = memories.on_this_day(datetime.date(2027, 11, 24))  # Carlsen in Chennai, two days late
    assert late[1].startswith("On 22 November 2013: Magnus Carlsen")


def test_on_this_day_comes_from_viktor_with_its_source(tmp_path, monkeypatch):
    fresh(tmp_path, monkeypatch, club=True)
    memories.told("welcome")
    memories.told("hundred")
    p = said(datetime.date(2026, 12, 12), n=1)[0]
    assert p["kind"] == "history" and p["voice"] == "viktor" and p["action"]["url"].startswith("https://en.wikipedia.org")


def test_33_chess_words_each_with_a_meaning(tmp_path, monkeypatch):
    monkeypatch.setattr(words, "FILE", tmp_path / "words.json")
    p = words.page()
    assert len(p["words"]) == 33 and all(w["meaning"].endswith(".") for w in p["words"])
    forms = [f.lower() for w in p["words"] for f in w["forms"]]
    assert len(forms) == len(set(forms)), "one form, one word"
    assert words.looked_up("Fork") and not words.looked_up("not a word")
    assert words.page()["looked"] == ["Fork"]


def test_viktor_points_at_the_word_list_once_you_use_words(tmp_path, monkeypatch):
    fresh(tmp_path, monkeypatch)
    monkeypatch.setattr(words, "FILE", tmp_path / "words.json")
    for w in ("Fork", "Pin", "Skewer"):
        words.looked_up(w)
    c = {c["kind"]: c for c in nudge.candidates("app", QUIET, day=DAY)}["words"]
    assert c["route"] == "words" and c["line"].startswith("You've looked up 3 chess words. All 33")


def test_meet_your_coaches_after_two_days_in_the_club(tmp_path, monkeypatch):
    fresh(tmp_path, monkeypatch)
    memories.joined(DAY)
    assert "meet" not in {c["kind"] for c in nudge.candidates("app", QUIET, day=DAY)}
    later = {c["kind"]: c for c in nudge.candidates("app", QUIET, day=DAY + datetime.timedelta(days=2))}
    assert later["meet"]["route"] == "coaches"
    nudge.seen("coaches", day=DAY + datetime.timedelta(days=2))
    assert "meet" not in {c["kind"] for c in nudge.candidates("app", QUIET, day=DAY + datetime.timedelta(days=40))}


def test_a_broken_story_never_stops_the_suggestions(tmp_path, monkeypatch):
    fresh(tmp_path, monkeypatch, club=True)

    def boom(*a, **k):
        raise RuntimeError("no")
    monkeypatch.setattr(memories, "candidates", boom)
    assert said(n=1)  # the day's other things still come


def test_story_json_keeps_ranks_and_told_lines_together(tmp_path):
    story.note_level(1)
    memories.told("welcome", DAY)
    m = json.loads(story.FILE.read_text())
    assert m["reached"] == 1 and m["told_lines"] == {"welcome": DAY.isoformat()}


def test_every_line_fits_the_bubble():
    """The bubble shows two sentences (More shows the rest): a memory's point must be in them."""
    import re
    lines = [m[1] for m in memories.MEMORIES.values()] + [m[1] for m in memories.MOMENTS.values()] + \
        [h[3] for h in memories.HISTORY]
    for line in lines:
        assert len(re.split(r"(?<=[.!?])\s+", line)) <= 2, line


def test_the_page_memory_endpoints(tmp_path, monkeypatch):
    """Through the app's own server: asked, then marked told only when the page showed it."""
    import threading
    import urllib.request
    from http.server import ThreadingHTTPServer
    from coach import service
    srv = ThreadingHTTPServer(("127.0.0.1", 0), service.Handler)
    monkeypatch.setattr(service, "PORT", srv.server_port)  # the Host check uses the real port
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    get = lambda path: json.loads(urllib.request.urlopen(f"http://127.0.0.1:{srv.server_port}{path}", timeout=5).read())
    try:
        assert get("/api/memory?page=calc")["id"] == "viktor-regret"
        assert get("/api/memory?page=calc")["id"] == "viktor-regret"  # still there: not shown yet
        assert get("/api/memory/told?id=viktor-regret")["ok"]
        assert get("/api/memory?page=calc") == {}
        assert len(get("/api/words")["words"]) == 33
    finally:
        srv.shutdown()
