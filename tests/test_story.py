"""Step 3.1 (28 Nov 2026): the club's ranks and Viktor's notebook (coach/story.py, docs/STORYLINE.md)."""
import json
import time

import pytest

from coach import nudge, story


@pytest.fixture(autouse=True)
def _own_file(tmp_path, monkeypatch):
    monkeypatch.setattr(story, "FILE", tmp_path / "story.json")
    monkeypatch.setattr(nudge, "FILE", tmp_path / "nudges.json")


def test_five_ranks_each_with_a_sourced_page():
    assert list(story.RANKS.values()) == ["New member", "Club player", "Team player", "First board", "Club master"]
    assert set(story.NOTEBOOK) == set(story.RANKS)
    for page in story.NOTEBOOK.values():  # every story is real and shows where it comes from
        assert page["title"] and len(page["text"]) > 80 and page["source"].startswith("https://en.wikipedia.org/")


def test_where_you_already_stand_is_no_fanfare_but_a_new_rank_is():
    story.note_level(1)  # first time: remembered quietly
    assert story.pending_rank() is None
    story.note_level(1)
    assert story.pending_rank() is None
    story.note_level(2)  # moved up
    up = story.pending_rank()
    assert {k: up[k] for k in ("id", "rank", "page")} == {"id": "club", "rank": "Team player", "page": "The magician from Riga"}
    assert up["story"].startswith("Mikhail Tal became world champion in 1960")
    story.note_level(1)  # a bad week never takes a rank away
    assert story.pending_rank()["rank"] == "Team player"
    story.told_rank()  # the player opened Your level
    assert story.pending_rank() is None


def test_the_notebook_restores_pages_up_to_your_rank():
    pages = story.notebook(1)
    assert [p["open"] for p in pages] == [True, True, False, False, False]
    assert pages[1]["title"] == "The Opera Game" and pages[2]["title"] is None and pages[2]["text"] is None


def test_viktor_brings_up_a_new_rank():
    story.note_level(0)
    story.note_level(1)
    home = {"games": 50, "daily": {"done_today": True}, "last_game": {"end_time": time.time() - 9 * 86400}}
    c = [x for x in nudge.candidates("app", home) if x["kind"] == "rank"]
    assert c and c[0]["line"].startswith("A new rank: Club player, and a story from my notebook. Paris, 1858.")
    assert c[0]["route"] == "level"


def test_the_level_page_carries_ranks_and_the_notebook(monkeypatch):
    import threading
    import urllib.request

    from coach import course, ladder, service
    levels = [{"id": lid, "name": lid, "band": "x", "skills": [], "done": False} for lid in story.ORDER]
    monkeypatch.setattr(ladder, "page", lambda: {"player": "me", "games": 20, "levels": levels, "current": 2})
    monkeypatch.setattr(course, "course", lambda current=None: {"lessons": []})
    server = service.Server(("127.0.0.1", 0), service.Handler)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    old, service.PORT = service.PORT, port
    try:
        out = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/api/ladder").read())
    finally:
        service.PORT = old
        server.shutdown()
        server.server_close()
    assert [lv["rank"] for lv in out["levels"]][:3] == ["New member", "Club player", "Team player"]
    assert [p["open"] for p in out["notebook"]] == [True, True, True, False, False]
