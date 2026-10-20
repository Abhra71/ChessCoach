"""Guess the human move, the weekly challenge (1.0): five real positions a week, scored by what people play."""
import datetime

import pytest

from coach import guess, maia

pytestmark = pytest.mark.skipif(not maia.available(), reason="Maia-3 isn't downloaded")


@pytest.fixture(autouse=True)
def own_file(tmp_path, monkeypatch):
    monkeypatch.setattr(guess, "FILE", tmp_path / "guess.json")


def test_a_week_has_five_real_guesses_at_rising_ratings_and_keeps_them():
    day = datetime.date(2026, 10, 20)
    c = guess.challenge(day)
    assert len(c["positions"]) == guess.COUNT and [p["rating"] for p in c["positions"]] == list(guess.RATINGS)
    for p in c["positions"]:
        assert 35 <= p["top"][0]["pct"] <= 85 and p["top"][0]["uci"] in p["legal"]  # a real guess, never a giveaway
    assert guess.challenge(day + datetime.timedelta(days=2))["positions"] == c["positions"]  # the same all week
    assert guess.challenge(day + datetime.timedelta(days=7))["week"] != c["week"]  # new ones on Monday


def test_the_favourite_scores_100_and_a_rare_move_little():
    p = guess.challenge(datetime.date(2026, 10, 20))["positions"][0]
    assert guess.score(p, p["top"][0]["uci"]) == 100
    rare = next((u for u in p["legal"] if u not in p["chances"]), None)  # a move under 0.5% there
    assert rare is None or guess.score(p, rare) == 0


def test_the_weeks_best_is_kept():
    day = datetime.date(2026, 10, 20)
    guess.challenge(day)
    assert guess.done(300, day) == {"best": 300, "record": True}
    assert guess.done(200, day) == {"best": 300, "record": False}
