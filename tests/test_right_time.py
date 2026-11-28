"""Step 3.2 (28 Nov, owner: "nothing unused"): the seven features only the tour used to bring up now each have a
moment from the player's own data, brought by their own coach, and stay quiet when the data isn't there."""
import datetime
import json
import time

from coach import features, nudge
from tests.test_nudge import HOME, fresh

SUNDAY = datetime.date(2026, 11, 29)
QUIET = {**HOME, "last_game": {}, "daily": {"done_today": True}}
ME = "me"


def game(i, end=None, opp="Someone"):
    return {"url": f"https://www.chess.com/game/live/{i}", "end_time": end or time.time() - 3600 * (i + 1),
            "white": {"username": ME, "result": "win"}, "black": {"username": opp, "result": "resigned"}, "pgn": ""}


def kinds(day, home=QUIET, games=None, player=None):
    return {c["kind"]: c for c in nudge.candidates("app", home, games=games, player=player, day=day)}


def test_no_feature_is_left_to_the_tour_alone():
    assert features.GAPS == [] and features.gaps() == []


def test_practice_due_again_today(tmp_path, monkeypatch):
    fresh(tmp_path, monkeypatch)
    from coach import memory
    for i in range(4):
        memory.record_practice(f"d{i}", "drill", True, day=SUNDAY - datetime.timedelta(days=1))  # box 1: back tomorrow
    c = kinds(SUNDAY)["practice"]
    assert c["line"].startswith("4 positions from your own mistakes are due again today") and c["route"] == "practice"
    memory.record_practice("d0", "drill", True, day=SUNDAY)  # practised today: nothing to say
    assert "practice" not in kinds(SUNDAY)


def test_weekly_letter_only_on_sunday_after_a_week_with_games(tmp_path, monkeypatch):
    fresh(tmp_path, monkeypatch)
    home = {**QUIET, "week": {"this": {"games": 5, "pieces": 3}, "last": {}}}
    assert kinds(SUNDAY, home)["report"]["route"] == "report/week"
    assert "report" not in kinds(SUNDAY - datetime.timedelta(days=1), home)  # Saturday
    assert "report" not in kinds(SUNDAY, {**home, "week": {"this": {"games": 1}}})  # a quiet week
    nudge.seen("report/week", day=SUNDAY - datetime.timedelta(days=2))
    assert "report" not in kinds(SUNDAY, home)  # read it already this week


def test_the_month_as_wrapped_and_its_film_on_the_first_days(tmp_path, monkeypatch):
    fresh(tmp_path, monkeypatch)
    from coach import film, insights
    games = [game(i) for i in range(6)]
    monkeypatch.setattr(film, "month_game", lambda: insights.game_id(games[2]["url"]))
    first = datetime.date(2026, 12, 1)
    got = kinds(first, games=games, player=ME)
    assert got["wrapped"]["route"] == "report/month" and "6 games" in got["wrapped"]["line"]
    assert got["film"]["route"] == "film/month" and "against Someone" in got["film"]["line"]
    later = kinds(first + datetime.timedelta(days=5), games=games, player=ME)
    assert "wrapped" not in later and "film" not in later


def test_blindfold_once_you_are_a_club_player(tmp_path, monkeypatch):
    fresh(tmp_path, monkeypatch)
    from coach import story
    games = [game(i) for i in range(3)]
    story.note_level(0)
    assert "blindfold" not in kinds(SUNDAY, games=games, player=ME)  # a new member: not yet
    story.note_level(1)
    story.told_rank()
    c = kinds(SUNDAY, games=games, player=ME)["blindfold"]
    assert "Club player" in c["line"] and "Berlin" in c["line"]
    nudge.seen("blindfold", day=SUNDAY)
    assert "blindfold" not in kinds(SUNDAY + datetime.timedelta(days=3), games=games, player=ME)


def test_guess_when_you_keep_walking_into_their_plans(tmp_path, monkeypatch):
    fresh(tmp_path, monkeypatch)
    from coach import guess, insights, maia
    monkeypatch.setattr(maia, "enabled", lambda: True)
    games = [game(i) for i in range(6)]
    rows = {g["url"]: [{"pattern": "walked into a fork or trick"}] for g in games}
    monkeypatch.setattr(insights, "_moves", lambda: rows)
    c = kinds(SUNDAY, games=games, player=ME)["guess"]
    assert c["line"].startswith("6 times in your last 6 games") and c["route"] == "guess"
    guess.FILE.write_text(json.dumps({"week": guess.week(SUNDAY), "tries": 1}))  # tried this week
    assert "guess" not in kinds(SUNDAY, games=games, player=ME)
    rows = {g["url"]: [] for g in games}  # careful games: nothing to say
    monkeypatch.setattr(insights, "_moves", lambda: rows)
    assert "guess" not in kinds(SUNDAY + datetime.timedelta(days=7), games=games, player=ME)


def test_your_plan_is_brought_up_on_home_when_a_new_card_is_picked():
    """It already was (coach/coaches.py): the map had missed it."""
    from coach import coaches, insights
    said = coaches.speak("home", insights.home() or {}, extra={"novelty": {"title": "Forks", "kind": "tactic",
                                                                          "why": "Forks are new for you."}}, in_app=True)
    assert any(line.startswith("Something new for you: forks. Forks are new for you.") for line in said["lines"])
    assert said["actions"][0]["app"] == "plan"


def test_a_broken_moment_never_stops_the_others(tmp_path, monkeypatch):
    fresh(tmp_path, monkeypatch)
    from coach import film

    def boom(*a, **k):
        raise RuntimeError("no")
    monkeypatch.setattr(film, "month_game", boom)
    home = {**QUIET, "week": {"this": {"games": 5, "pieces": 3}, "last": {}}}
    assert "report" in kinds(datetime.date(2026, 11, 1), home, games=[game(0)], player=ME)  # a Sunday and a 1st


def test_each_new_kind_has_a_button():
    import inspect
    from coach import service
    src = inspect.getsource(service)
    for k in ("practice", "report", "film", "wrapped", "blindfold", "guess"):
        assert f'"{k}": "' in src


def test_viktors_own_words_are_said_by_viktor_even_on_mayas_page(tmp_path, monkeypatch):
    fresh(tmp_path, monkeypatch)
    from coach import insights, service, story
    story.note_level(0)
    story.note_level(1)
    story.told_rank()
    p = nudge.pick("app", "home", QUIET, SUNDAY, games=[game(0)], player=ME)
    assert p["kind"] == "blindfold" and p["voice"] == "viktor"
    monkeypatch.setattr(nudge, "pick", lambda *a, **k: p)
    monkeypatch.setattr(insights, "home", lambda: QUIET)
    said = service.with_point({"coach": "maya", "lines": ["Good evening."], "actions": []},
                              {"in": "app", "section": "home", "tab": "home"})
    assert said["coach"] == "viktor" and said["lines"][-1].startswith("You're a Club player now. As a boy in Berlin")
    assert said["lines"][0] != "Good evening."  # Maya's greeting isn't put in Viktor's mouth
