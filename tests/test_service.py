from coach.service import game_id, key_moments

HANG = dict(url="https://www.chess.com/game/live/42", color="white", stalemate=False, cp_before=0, cp_after=-800,
            best_mates=False, allows_mate=False, best_is_capture=False, mat_before=8, loss=45,
            fen="4k3/8/3p4/8/3Q4/8/8/4K3 w - - 0 1", move="Qe5", best="Qd5", reply_pv=["d6e5"], ply=31)


def test_game_id():
    assert game_id("https://www.chess.com/game/live/143843521880") == "143843521880"


def test_key_moment_has_arrows_and_words():
    [m] = key_moments([HANG, dict(HANG, loss=2, ply=33)])  # the small slip is not a key moment
    assert (m["move_uci"], m["best_uci"], m["reply_uci"]) == ("d4e5", "d4d5", "d6e5")
    assert m["placement"] == "4k3/8/3p4/8/3Q4/8/8/4K3"
    assert m["after_placement"] == "4k3/8/3p4/4Q3/8/8/8/4K3"
    assert m["say"].startswith("You put your queen on e5, where nothing guards it: their pawn just takes it.")
    assert m["idea"] == "hanging" and m["lesson"]["id"] == "safe-hanging"  # the reason links to its course lesson
    assert m["move_number"] == 16


def test_review_tells_the_real_reply_from_the_engine_reply():
    """The 13 Oct test: the arrow said "Reply" for the engine's Bxa8 when the opponent really castled."""
    import chess
    from coach.service import moment
    board = chess.Board(HANG["fen"])
    filler = [chess.Move.null()] * HANG["ply"]  # the moves before; only the one after the player's move matters
    missed = moment(HANG, filler[:-1] + [board.parse_san("Qe5")] + [chess.Move.from_uci("e8e7")])
    assert (missed["reply_san"], missed["real_reply_san"], missed["reply_missed"]) == ("dxe5", "Ke7", True)
    assert missed["say"].endswith("In the game they missed it and played Ke7.")
    found = moment(HANG, filler[:-1] + [board.parse_san("Qe5")] + [chess.Move.from_uci("d6e5")])
    assert (found["real_reply_san"], found["reply_missed"]) == ("dxe5", False)
    assert "missed" not in found["say"]
    last = moment(HANG, filler)  # the game ended after the player's move
    assert (last["real_reply_uci"], last["reply_missed"]) == (None, False)
    assert moment(HANG)["grade"] == "Blunder"
    # one step at a time: You played, Better, They replied, and Their better only when they missed it
    assert [s["kind"] for s in missed["steps"]] == ["mine", "better", "real", "reply"]
    assert [s["kind"] for s in found["steps"]] == ["mine", "better", "real"]
    assert "their best answer" in found["steps"][2]["text"]
    assert [s["kind"] for s in last["steps"]] == ["mine", "better", "reply"]
    assert last["steps"][2]["text"].startswith("The game ended here.")
    assert [s["board"] for s in missed["steps"]] == ["before", "before", "after", "after"]


def test_at_most_three_moments_in_game_order():
    rows = [dict(HANG, ply=p, loss=30 + p) for p in (11, 21, 31, 41)]
    assert [m["ply"] for m in key_moments(rows)] == [21, 31, 41]


def test_only_one_copy_can_run():
    import pytest
    from coach.service import Handler, Server
    first = Server(("127.0.0.1", 0), Handler)
    try:
        with pytest.raises(OSError):
            Server(("127.0.0.1", first.server_address[1]), Handler)
    finally:
        first.server_close()


def test_bad_usernames_are_refused_without_asking_chess_com():
    from coach.service import set_player
    for name in ("", "has space", "semi;colon", "x" * 31):
        ok, message = set_player(name)
        assert not ok and "doesn't look like" in message


def test_status_has_what_the_welcome_page_needs():
    from coach.service import status
    s = status()
    for key in ("player", "phase", "done", "total", "review_ready", "extension_seen", "extension_path", "browsers"):
        assert key in s


def test_coach_says_nothing_about_a_game_it_does_not_know(monkeypatch):
    from coach import service
    monkeypatch.setattr(service.MOMENT_CACHE, "get", lambda gid: [HANG] if gid == "42" else None)
    from coach import coaches  # a player with games, not this PC's data (GitHub's computer has none)
    monkeypatch.setattr(coaches.insights, "home", lambda: {"player": "gushynanda", "games": 140, "pieces_last20": 0.7,
                                                           "pieces_per_game": 1.2})
    unknown = service.coach_says("/api/coach?section=review&hour=20&game=999")
    assert unknown["coach"] == "maya" and unknown["mood"] == "thinking" and not unknown["actions"]
    known = service.coach_says("/api/coach?section=review&hour=20&game=42")
    assert "1 key moment" in known["lines"][0] and "moments" not in known["lines"][0]


def test_only_knightwise_and_its_extension_may_talk_to_it():
    import threading
    import urllib.error
    import urllib.request
    from coach.service import Handler, Server
    server = Server(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()

    def status(origin=None, host=None):
        req = urllib.request.Request(f"http://127.0.0.1:{port}/api/hello")
        if origin:
            req.add_header("Origin", origin)
        if host:
            req.add_header("Host", host)
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, r.headers.get("Access-Control-Allow-Origin")
        except urllib.error.HTTPError as e:
            return e.code, None
    import coach.service as service
    old = service.PORT
    service.PORT = port  # the Host check uses the real port
    try:
        assert status()[0] != 403 and status()[1] is None  # no "any website may read this" header
        assert status("chrome-extension://abc")[0] != 403
        assert status("https://evil.example")[0] == 403
        assert status(host=f"evil.example:{port}")[0] == 403  # a site pointing its own name at this computer
    finally:
        service.PORT = old
        server.shutdown()
        server.server_close()


def test_sign_in_time_is_read_from_windows_not_from_the_boot_time():
    import sys
    import pytest
    if sys.platform != "win32":
        pytest.skip("Windows only")
    from coach import app
    minutes = app.minutes_since_sign_in()
    assert minutes is not None and 0 <= minutes < 60 * 24 * 60


def test_settings_say_which_browser_the_extension_is_in():
    """13 Oct test: the Edge tab said Connected though the extension was only in Chrome."""
    from coach.service import browser_of
    chrome = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0 Safari/537.36"
    edge = chrome + " Edg/141.0"
    assert (browser_of(chrome), browser_of(edge), browser_of(None)) == ("chrome", "edge", "other")


def test_ai_nudge_follows_the_real_key(monkeypatch):
    """The 'Want real replies?' line shows only while no key is set, and comes back when it's removed."""
    from coach import service, settings
    monkeypatch.setattr(service, "player", lambda: None)
    keys = {}
    monkeypatch.setattr(settings, "get_key", lambda slot: keys.get(slot))
    assert "ai_hint" in service.coach_says("/api/coach?section=puzzles&hour=10")
    keys["slot1"] = "gsk_test"
    assert "ai_hint" not in service.coach_says("/api/coach?section=puzzles&hour=10")
    keys.clear()
    assert "ai_hint" in service.coach_says("/api/coach?section=puzzles&hour=10")


def test_archive_tag_says_what_the_review_shows():
    """chess.com's archive gets one short, true line per checked game: the same moments as the review."""
    from coach.service import game_tag
    assert game_tag(None) is None  # not checked (or not finished): no tag
    assert game_tag([dict(HANG, loss=2)]) == {"text": "clean game", "tone": "good"}  # a small slip isn't a mistake
    assert game_tag([HANG, dict(HANG, ply=21)]) == {"text": "2 pieces left hanging", "tone": "bad"}


def test_a_key_moment_says_how_hard_the_better_move_was():
    """1.0: "How hard was it?" from the human-move model, kind and in words; nothing without the model."""
    from coach import maia
    [m] = key_moments([HANG])
    if maia.enabled():
        assert m["hard"] and "at your level" in m["hard"]
    else:
        assert m["hard"] is None


def test_app_files_only_from_inside_the_app():
    """/ui/ serves the app's own files; ".." can't reach anything outside (20 Oct: linked folders are still served)."""
    from coach.service import Handler
    h = Handler.__new__(Handler)
    assert h.static_file("app.js") is not None
    assert h.static_file("../service.py") is None and h.static_file(r"..\service.py") is None
    assert h.static_file("../../tests/conftest.py") is None and h.static_file("nope.js") is None


def test_feedback_by_email_is_a_ready_email_to_the_right_address():
    from urllib.parse import parse_qs, unquote, urlsplit
    from coach.service import FEEDBACK_TO, feedback_mail
    url = feedback_mail("What went wrong: the arrow & the ring\n" + "x" * 5000)
    parts = urlsplit(url)
    assert parts.scheme == "mailto" and unquote(parts.path) == FEEDBACK_TO == "nanotech.mark.robots@gmail.com"
    q = parse_qs(parts.query)
    assert q["subject"][0].startswith("Knightwise feedback") and q["body"][0].startswith("What went wrong: the arrow & the ring")
    assert len(url) < 6000  # Windows mail apps cut longer addresses


def test_start_over_clears_the_player_but_keeps_the_app(tmp_path, monkeypatch):
    from coach import service
    monkeypatch.setattr(service, "DATA", tmp_path)
    for name in ("player.txt", "moves.jsonl", "games-2026-10.json", "practice.jsonl", "novelty.json", "course.json",
                 "settings.json", "puzzles.json", "ai-usage.json"):
        (tmp_path / name).write_text("x")
    (tmp_path / "voice-cache").mkdir()
    service.start_over()
    assert sorted(p.name for p in tmp_path.iterdir()) == ["ai-usage.json", "puzzles.json", "settings.json", "voice-cache"]
