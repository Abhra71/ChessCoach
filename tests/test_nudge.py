"""The coach's one new thing per page: one list for both places, once a day each, at most A_DAY a day, a different
kind from yesterday's first, never what's already done, never in a game or a review."""
import datetime
import time

from coach import nudge

DAY = datetime.date(2026, 10, 23)
NEXT = DAY + datetime.timedelta(days=1)
HOME = {"games": 140, "daily": {"done_today": False, "streak": 3},
        "focus": {"pattern": "left a piece hanging"},
        "last_game": {"id": "111", "opponent": "RIP_Hansie", "moments": 2, "checked": True, "result": "loss",
                      "end_time": time.time() - 3600}}
REMATCH = {"ply": 32, "move_number": 16}


def fresh(tmp_path, monkeypatch):
    monkeypatch.setattr(nudge, "FILE", tmp_path / "nudges.json")


def ids(place, home, n=4, day=DAY, **kw):
    return [p["id"] if p else None for p in (nudge.pick(place, "home", home, day, **kw) for _ in range(n))]


def test_a_new_game_first_then_the_daily_then_a_rematch_then_quiet(tmp_path, monkeypatch):
    fresh(tmp_path, monkeypatch)
    assert ids("app", HOME, rematch=REMATCH) == ["game-111", "daily", "rematch-111", None]  # 3 a day


def test_a_kind_shown_yesterday_goes_to_the_back_but_a_new_game_never_does(tmp_path, monkeypatch):
    fresh(tmp_path, monkeypatch)
    ids("app", HOME, rematch=REMATCH)
    assert ids("app", HOME, n=3, day=NEXT, rematch=REMATCH)[:2] == ["game-111", "daily"]
    assert ids("app", HOME, n=1, day=NEXT, rematch=REMATCH) == [None]


def test_the_rematch_goes_back_a_day_after_it_was_shown(tmp_path, monkeypatch):
    fresh(tmp_path, monkeypatch)
    ids("app", HOME, rematch=REMATCH)
    nudge.seen("games/111")
    home = {**HOME, "daily": {"done_today": True}}
    assert ids("app", home, n=1, day=NEXT, rematch=REMATCH) == ["cc-puzzles"]  # not the rematch two days running


def test_already_done_or_opened_is_never_suggested_again(tmp_path, monkeypatch):
    fresh(tmp_path, monkeypatch)
    for route in ("games/111", "rematch/111/32", "course/safe-checks", "guess"):
        nudge.seen(route)
    home = {**HOME, "daily": {"done_today": True}}
    got = ids("app", home, n=3, lesson={"id": "safe-checks", "title": "Look at their checks"}, rematch=REMATCH)
    assert not {"game-111", "daily", "rematch-111", "lesson-Look at their checks", "try-guess"} & set(got)
    assert "try-blindfold" in got


def test_app_things_on_chess_com_get_a_button_and_chess_com_things_in_the_app_a_link(tmp_path, monkeypatch):
    fresh(tmp_path, monkeypatch)
    nudge.seen("games/111")
    cc = nudge.pick("chesscom", "home", HOME, DAY)
    assert cc["id"] == "daily" and cc["action"] == {"label": "Open Knightwise", "app": "daily"}
    home = {**HOME, "daily": {"done_today": True}}
    app = nudge.pick("app", "home", home, DAY)
    assert app["id"] == "cc-puzzles" and app["action"]["url"].startswith("https://www.chess.com/")


def test_on_chess_com_the_red_ring_and_never_in_play_or_review(tmp_path, monkeypatch):
    fresh(tmp_path, monkeypatch)
    nudge.seen("games/111")
    home = {**HOME, "daily": {"done_today": True}}
    p = nudge.pick("chesscom", "home", home, DAY)
    assert p["guide"] == "puzzles" and p["route_guide"]["to"] == "/puzzles/rated"
    assert nudge.pick("chesscom", "play", HOME, DAY) is None
    assert nudge.pick("chesscom", "review", HOME, DAY) is None
    assert nudge.pick("app", "review", HOME, DAY) is None


def test_not_the_way_to_puzzles_on_the_puzzles_page(tmp_path, monkeypatch):
    fresh(tmp_path, monkeypatch)
    nudge.seen("games/111")
    home = {**HOME, "daily": {"done_today": True}}
    assert nudge.pick("chesscom", "puzzles", home, DAY)["id"] == "bots"


def test_close_to_a_badge_rushed_mistakes_and_a_regular_opponent(tmp_path, monkeypatch):
    fresh(tmp_path, monkeypatch)
    nudge.seen("games/111")
    home = {**HOME, "daily": {"done_today": True}, "last_game": {}}
    prog = {"badges": [{"group": "Habits", "id": "safe", "name": "Safe pieces", "what": "games in a row without a "
                        "hanging piece", "current": 8, "next": 10}], "clock": {"big": 44, "fast": 16}}
    now = time.time()
    games = [{"end_time": now - i * 86400, "white": {"username": "gushynanda"}, "black": {"username": "Laro1966"}}
             for i in range(4)]
    got = ids("app", home, n=3, prog=prog, games=games, player="gushynanda")
    assert got == ["badge-safe-10", "clock", "prep-laro1966"]


def test_an_old_game_is_not_new(tmp_path, monkeypatch):
    fresh(tmp_path, monkeypatch)
    home = {**HOME, "last_game": {**HOME["last_game"], "end_time": time.time() - 5 * 86400}}
    assert nudge.pick("app", "home", home, DAY)["id"] == "daily"


def test_a_new_player_with_no_games_gets_nothing(tmp_path, monkeypatch):
    fresh(tmp_path, monkeypatch)
    assert nudge.pick("app", "home", {"games": 0}, DAY) is None
