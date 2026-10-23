"""The coach's one new thing per page: once a day each, at most A_DAY a day, never in a game or a review."""
import datetime
import time

from coach import nudge

DAY = datetime.date(2026, 10, 23)
HOME = {"games": 140, "daily": {"done_today": False, "streak": 3},
        "focus": {"pattern": "left a piece hanging"},
        "last_game": {"id": "111", "opponent": "RIP_Hansie", "moments": 2, "checked": True, "result": "loss",
                      "end_time": time.time() - 3600}}


def fresh(tmp_path, monkeypatch):
    monkeypatch.setattr(nudge, "FILE", tmp_path / "nudges.json")


def test_a_new_game_comes_first_then_the_daily_then_a_rematch(tmp_path, monkeypatch):
    fresh(tmp_path, monkeypatch)
    picks = [nudge.pick("app", "home", HOME, DAY, rematch={"ply": 32, "move_number": 16}) for _ in range(4)]
    assert [p["route"] if p else None for p in picks] == ["games/111", "daily", "rematch/111/32", None]  # 3 a day
    assert "2 key moments" in picks[0]["line"] and "3-day streak" in picks[1]["line"]


def test_each_suggestion_once_a_day_and_back_tomorrow(tmp_path, monkeypatch):
    fresh(tmp_path, monkeypatch)
    assert nudge.pick("app", "home", HOME, DAY)["id"] == "game-111"
    assert nudge.pick("app", "home", HOME, DAY)["id"] == "daily"
    assert nudge.pick("app", "home", HOME, DAY + datetime.timedelta(days=1))["id"] == "game-111"


def test_a_game_already_opened_is_not_new(tmp_path, monkeypatch):
    fresh(tmp_path, monkeypatch)
    nudge.seen("games/111")
    assert nudge.pick("app", "home", HOME, DAY)["id"] == "daily"


def test_something_untried_is_offered_one_at_a_time(tmp_path, monkeypatch):
    fresh(tmp_path, monkeypatch)
    home = {**HOME, "daily": {"done_today": True}, "last_game": {}}
    assert nudge.pick("app", "home", home, DAY)["route"] == "guess"
    nudge.seen("guess")
    assert nudge.pick("app", "home", home, DAY + datetime.timedelta(days=1))["route"] == "blindfold"


def test_on_chess_com_the_red_ring_for_the_habit_and_never_in_play_or_review(tmp_path, monkeypatch):
    fresh(tmp_path, monkeypatch)
    nudge.seen("games/111")
    p = nudge.pick("chesscom", "home", HOME, DAY)
    assert p["guide"] == "puzzles" and p["route_guide"]["to"] == "/puzzles/rated"
    assert nudge.pick("chesscom", "play", HOME, DAY) is None
    assert nudge.pick("chesscom", "review", HOME, DAY) is None
    assert nudge.pick("app", "review", HOME, DAY) is None


def test_not_the_way_to_puzzles_on_the_puzzles_page(tmp_path, monkeypatch):
    fresh(tmp_path, monkeypatch)
    nudge.seen("games/111")
    assert nudge.pick("chesscom", "puzzles", HOME, DAY) is None


def test_a_new_player_with_no_games_gets_nothing(tmp_path, monkeypatch):
    fresh(tmp_path, monkeypatch)
    assert nudge.pick("app", "home", {"games": 0}, DAY) is None


def test_an_old_game_is_not_new(tmp_path, monkeypatch):
    fresh(tmp_path, monkeypatch)
    home = {**HOME, "last_game": {**HOME["last_game"], "end_time": time.time() - 5 * 86400}}
    assert nudge.pick("app", "home", home, DAY)["id"] == "daily"
