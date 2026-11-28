"""Step 2 of docs/CONNECTIONS.md (28 Nov, owner: "everything on the right time"): a suggestion from the player's own
data rests after it was opened or ignored, and comes back when the need is still there, instead of never again."""
import datetime
import json

from coach import nudge
from tests.test_nudge import HOME, fresh

DAY = datetime.date(2026, 12, 1)
CLOCK = {"clock": {"big": 40, "fast": 20}}  # half the big mistakes in a rush: the clock drill is needed
QUIET = {**HOME, "last_game": {}, "daily": {"done_today": True}}  # nothing else to say that day


def clock_today(day):
    """Is the clock drill among the day's suggestions (up to A_DAY; a kind shown yesterday goes to the back)?"""
    picks = [nudge.pick("app", "home", QUIET, day, prog=CLOCK) for _ in range(nudge.A_DAY)]
    return any(p and p["kind"] == "clock" for p in picks)


def test_opened_it_rests_then_comes_back_if_still_needed(tmp_path, monkeypatch):
    fresh(tmp_path, monkeypatch)
    assert clock_today(DAY)
    nudge.seen("clockdrill", day=DAY)  # the player opened the drill
    assert not clock_today(DAY + datetime.timedelta(days=10))  # resting
    assert not clock_today(DAY + datetime.timedelta(days=20))
    assert clock_today(DAY + datetime.timedelta(days=21))  # REST_DAYS later the habit is still there: Maya brings it back


def test_not_needed_any_more_it_stays_quiet(tmp_path, monkeypatch):
    fresh(tmp_path, monkeypatch)
    nudge.seen("clockdrill", day=DAY)
    later = DAY + datetime.timedelta(days=30)
    p = nudge.pick("app", "home", QUIET, later, prog={"clock": {"big": 40, "fast": 2}})  # the rush is gone
    assert not (p and p["kind"] == "clock")


def test_ignored_twice_it_rests_too(tmp_path, monkeypatch):
    fresh(tmp_path, monkeypatch)
    assert clock_today(DAY) and clock_today(DAY + datetime.timedelta(days=1))  # shown on two days, never opened
    assert not clock_today(DAY + datetime.timedelta(days=2))  # respect: it stops asking
    assert not clock_today(DAY + datetime.timedelta(days=20))
    assert clock_today(DAY + datetime.timedelta(days=23))  # after the rest, one more try


def test_updating_from_1_2_starts_gradually(tmp_path, monkeypatch):
    """Pages opened before dates were kept count as opened on the first day of the new version: nothing floods back."""
    fresh(tmp_path, monkeypatch)
    (tmp_path / "nudges.json").write_text(json.dumps({"seen": ["clockdrill"]}))
    assert not clock_today(DAY)
    assert not clock_today(DAY + datetime.timedelta(days=15))
    assert clock_today(DAY + datetime.timedelta(days=21))


def test_an_introduction_never_used_stops_nagging(tmp_path, monkeypatch):
    """28 Nov simulation on the owner's data: Punish, Spar, Explore, Ask and the film came back every other day,
    forever, because the player opened the page but never used the thing. Now: 2 days, a rest, 4 tries in all."""
    fresh(tmp_path, monkeypatch, tour=True)
    monkeypatch.setattr(nudge, "TOUR", nudge.TOUR[:1])  # one introduction, never used
    days = []
    for i in range(120):
        day = DAY + datetime.timedelta(days=i)
        p = nudge.pick("app", "home", {"games": 0}, day, now=1_800_000_000 + i * 86400)
        if p:
            days.append(i)
    assert len(days) == nudge.TOUR_TRIES  # 4 tries in all, then quiet for good
    # at most MAX_DAYS showings in any REST_DAYS window
    assert all(len([d for d in days if s <= d < s + nudge.REST_DAYS]) <= nudge.MAX_DAYS for s in range(120))


def test_the_use_record_counts_brought_and_opened(tmp_path, monkeypatch):
    fresh(tmp_path, monkeypatch)
    clock_today(DAY)
    nudge.seen("clockdrill", day=DAY)
    nudge.seen("clockdrill", day=DAY + datetime.timedelta(days=3))
    use = json.loads((tmp_path / "nudges.json").read_text())["use"]["clock"]
    assert use == {"brought": 1, "last_brought": "2026-12-01", "opened": 2, "last_opened": "2026-12-04"}
