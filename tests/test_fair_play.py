"""Fair play (docs/FAIR-PLAY-AUDIT.md, 27 Nov 2026): the extension can never show, draw or say anything during a game
against a real person, in its own tab or another one.

The extension's real page scripts run in a small stand-in for a chess.com tab (tests/fair_play_page.js, Node.js;
skipped without it). Each scenario is one of the ways the audit found a game could be running while Knightwise looked.
"""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
node = pytest.mark.skipif(not shutil.which("node"), reason="needs Node.js")


def run(scenario, timeout=90):
    out = subprocess.run(["node", str(ROOT / "tests" / "fair_play_page.js"), str(ROOT / "extension"), scenario],
                         capture_output=True, text=True, timeout=timeout)
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout.strip().splitlines()[-1])


@node
def test_a_finished_game_still_gets_its_review():
    r = run("finished")
    assert r["review"] is True
    assert r["live_here"] is False  # this tab now says: no live game here


@node
def test_a_new_game_on_the_same_page_takes_the_review_away():
    """chess.com can show a live game and the same game finished at one address; a rematch can start on the page."""
    r = run("rematch_same_page")
    assert r["before"] is True
    assert r["after"] is False and r["hushed"] is True
    assert r["live_here"] is True  # and the other tabs go quiet


@node
def test_nothing_without_the_finished_games_move_list():
    r = run("never_the_finished_list", timeout=120)
    assert r == {"review": False, "said": []}


@node
def test_no_review_while_a_game_is_on_in_another_tab():
    """The same opening in a live game in tab A, its 'Better' arrow in an old game's review in tab B."""
    assert run("review_with_live_game_elsewhere") == {"review": False, "said": []}


@node
def test_no_coach_while_a_game_is_on_in_another_tab():
    """Ask and Talk could otherwise answer questions about the game being played next door."""
    r = run("coach_with_live_game_elsewhere")
    assert r == {"coach": False, "said": [], "asked": False}


@node
def test_the_coach_goes_when_a_game_starts_in_another_tab():
    r = run("live_game_starts_elsewhere")
    assert r == {"before": True, "after": False}


@node
def test_a_late_answer_never_appears_on_a_game_page():
    """Ask on home, then straight into a game: the answer used to open the coach's box there, and speak."""
    assert run("late_answer_on_a_game_page") == {"coach": False, "said": []}


@node
def test_the_review_still_comes_when_the_app_missed_one_answer():
    """Bug hunt 27 Nov: one failed answer from the app ended the wait for good."""
    r = run("app_missed_once")
    assert r["review"] is True and r["asked"] == 2


@node
def test_every_game_address_counts_as_maybe_live():
    """The old check knew only /game/live and /play/online; chess.com's live games moved to /game/<id> on 13 Oct."""
    r = run("addresses")
    for live in ("/game/185261729330", "/live/game/185261729330", "/game/live/185261729330", "/game/daily/162529818",
                 "/play/online", "/play", "/puzzles/battle", "/newgame/185261729330"):
        assert r[live] is True, live
    for calm in ("/home", "/", "/puzzles/rated", "/member/demo_player", "/games/archive", "/stats/overview",
                 "/lessons/x", "/puzzles/problem/1234567"):
        assert r[calm] is False, calm


@node
def test_old_marks_are_ignored_and_unreadable_storage_stays_off():
    assert run("stale_marks") == {"stale": False, "fresh": True, "unreadable": True}


def test_the_app_tells_the_extension_how_long_the_finished_game_was(monkeypatch):
    """The extension compares it with chess.com's move list before it shows anything."""
    import threading
    import urllib.request

    import chess

    from coach import insights, nudge, service
    monkeypatch.setattr(service.MOMENT_CACHE, "get", lambda gid: [{"ply": 9}] if gid == "42" else None)
    monkeypatch.setattr(service, "key_moments", lambda rows, gid=None: [])
    monkeypatch.setattr(service, "played_moves", lambda gid: [chess.Move.null()] * 37 if gid == "42" else [])
    monkeypatch.setattr(service, "players_of", lambda gid: ["alice", "bob"])
    monkeypatch.setattr(insights, "extras_for", lambda gid: {})
    monkeypatch.setattr(insights, "game_detail", lambda gid: {})
    monkeypatch.setattr(nudge, "seen", lambda route: None)
    server = service.Server(("127.0.0.1", 0), service.Handler)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    old, service.PORT = service.PORT, port
    try:
        get = lambda gid: json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/api/game/{gid}").read())
        known = get("42")
        assert known["known"] is True and known["plies"] == 37
        unknown = get("999")  # a game being played: unknown, nothing about it
        assert unknown == {"known": False, "moments": [], "players": []}
    finally:
        service.PORT = old
        server.shutdown()
        server.server_close()
