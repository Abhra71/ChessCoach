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


def fresh(tmp_path, monkeypatch, tour=False):
    """A clean memory. These tests are about the day's suggestions: no tour and no gap between picks, unless asked."""
    from coach import plan
    monkeypatch.setattr(nudge, "FILE", tmp_path / "nudges.json")
    monkeypatch.setattr(plan, "MEMORY", tmp_path / "novelty.json")
    if not tour:
        monkeypatch.setattr(nudge, "TOUR", [])
        monkeypatch.setattr(nudge, "GAP", 0)


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
    assert not {"game-111", "daily", "rematch-111", "lesson-Look at their checks"} & set(got)


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
    assert got == ["clock", "badge-safe-10", "prep-laro1966"]  # their own mistake first (25 Oct)


def test_an_old_game_is_not_new(tmp_path, monkeypatch):
    fresh(tmp_path, monkeypatch)
    home = {**HOME, "last_game": {**HOME["last_game"], "end_time": time.time() - 5 * 86400}}
    assert nudge.pick("app", "home", home, DAY)["id"] == "daily"


def test_a_new_player_with_no_games_gets_nothing(tmp_path, monkeypatch):
    fresh(tmp_path, monkeypatch)
    assert nudge.pick("app", "home", {"games": 0}, DAY) is None


# ---------- the tour: everything in Knightwise, a few new things a day, with space between them ----------
T0 = 1_800_000_000.0
QUIET = {**HOME, "daily": {"done_today": True, "streak": 3}, "last_game": {}, "focus": {}}  # nothing else to say today


def test_the_tour_brings_a_new_thing_spaced_and_at_most_three_a_day(tmp_path, monkeypatch):
    fresh(tmp_path, monkeypatch, tour=True)
    nudge.seen("extension")  # the extension has said hello: no "set it up"
    first = nudge.pick("app", "home", QUIET, DAY, now=T0)
    assert first["kind"] == "tour" and first["route"] == "level"
    assert nudge.pick("app", "home", QUIET, DAY, now=T0 + 60) is None  # not together
    second = nudge.pick("app", "home", QUIET, DAY, now=T0 + nudge.TOUR_GAP)
    third = nudge.pick("app", "home", QUIET, DAY, now=T0 + 2 * nudge.TOUR_GAP)
    assert second["kind"] == third["kind"] == "tour" and len({first["id"], second["id"], third["id"]}) == 3
    assert nudge.pick("app", "home", QUIET, DAY, now=T0 + 3 * nudge.TOUR_GAP) is None  # three a day


def test_the_tour_skips_what_was_opened_and_comes_back_to_what_was_not(tmp_path, monkeypatch):
    fresh(tmp_path, monkeypatch, tour=True)
    nudge.seen("extension")  # the extension has said hello: no "set it up"
    assert nudge.pick("app", "home", QUIET, DAY, now=T0)["id"] == "tour-level"
    nudge.seen("practice")  # found on their own: never suggested
    nxt = nudge.pick("app", "home", QUIET, DAY, now=T0 + nudge.TOUR_GAP)
    assert nxt["id"] == "tour-plan"
    tomorrow = nudge.pick("app", "home", QUIET, NEXT, now=T0 + 86400)
    assert tomorrow["id"] not in ("tour-level", "tour-plan", "tour-practice")  # never shown ones before repeats


def test_the_tour_points_on_into_the_page_and_waits_for_what_it_needs(tmp_path, monkeypatch):
    fresh(tmp_path, monkeypatch, tour=True)
    nudge.seen("extension")  # the extension has said hello: no "set it up"
    ids_ = [x[0] for x in nudge.TOUR]
    nudge.seen("plan")
    explore = next(x for x in nudge.TOUR if x[0] == "explore")
    assert explore[2] == "plan@.explore-box"
    left = nudge.tour_next(today=DAY, now=T0)
    assert left["id"] == "tour-level"
    for x in ids_:  # everything opened except Explore and Done
        if x not in ("explore", "done"):
            nudge.seen(next(t for t in nudge.TOUR if t[0] == x)[3])
    assert nudge.tour_next(today=DAY, now=T0)["id"] == "tour-explore"
    nudge.seen("plan/explore")
    assert nudge.tour_next(today=DAY, now=T0) is None  # Done waits until something is done


def test_setting_up_chess_com_comes_first_until_the_extension_says_hello(tmp_path, monkeypatch):
    """30 Oct test: "it never nudges for setting the extension up" (it was last of 20 in the tour)."""
    fresh(tmp_path, monkeypatch, tour=True)
    assert nudge.pick("app", "home", QUIET, DAY, now=T0)["id"] == "tour-extension"
    fresh(tmp_path / "b", monkeypatch, tour=True)
    nudge.seen("extension")  # what /api/hello records
    assert nudge.tour_next(today=DAY, now=T0)["id"] != "tour-extension"


def test_the_speaking_coach_brings_her_own_first(tmp_path, monkeypatch):
    fresh(tmp_path, monkeypatch, tour=True)
    assert nudge.tour_next(coach="maya", today=DAY, now=T0)["coach"] == "maya"
    assert nudge.tour_next(coach="viktor", today=DAY, now=T0)["coach"] == "viktor"


def test_the_days_own_things_come_before_the_tour(tmp_path, monkeypatch):
    fresh(tmp_path, monkeypatch, tour=True)
    assert nudge.pick("app", "home", HOME, DAY, now=T0)["id"] == "game-111"
    assert nudge.pick("app", "home", HOME, DAY, now=T0 + nudge.GAP)["id"] == "daily"
    assert nudge.pick("app", "home", HOME, DAY, now=T0 + 2 * nudge.GAP)["kind"] == "tour"


def test_a_suggestion_not_opened_stops_after_two_days(tmp_path, monkeypatch):
    fresh(tmp_path, monkeypatch)
    seen = []
    for d in range(5):
        day = DAY + datetime.timedelta(days=d)
        seen += [x for x in ids("app", HOME, n=4, day=day, rematch=REMATCH) if x == "rematch-111"]
    assert len(seen) == 2  # 24 Oct: the same rematch before and after midnight, again and again
