"""Conversation without an AI key (24 Oct): tapped questions, answered from the player's numbers, never the same
wording twice in a row, never a number that isn't there."""
import random

from coach import answers

HOME = {"games": 140, "results": {"win": 60, "loss": 60, "draw": 20}, "rating_change": 25, "rating_class": "rapid",
        "you_vs_you": {"now": {"games": 20, "pieces": 0.7, "moments": 1.4, "wins": 45},
                       "then": {"games": 20, "pieces": 1.1, "moments": 1.6, "wins": 30}},
        "focus": {"pattern": "left a piece hanging", "habit": "Before every move, ask what they can take."},
        "patterns": [{"pattern": "left a piece hanging", "per_game": 0.86, "recent": 0.45}]}


def test_how_am_i_doing_uses_the_numbers_and_varies():
    seen = {answers.answer("how", {"section": "home"}, home=HOME, rng=random.Random(i))["text"] for i in range(6)}
    assert len(seen) >= 2  # different words
    assert all("0.7" in t and "1.1" in t and "45%" in t for t in seen)  # the same facts
    a, b = (answers.answer("how", {}, home=HOME)["text"] for _ in range(2))
    assert a != b  # never the same wording twice in a row


def test_follow_up_questions_leave_out_the_one_answered():
    r = answers.answer("how", {"section": "home"}, home=HOME)
    assert "how" not in [q["id"] for q in r["questions"]] and r["questions"] and r["ai"] is False


def test_no_numbers_no_made_up_answer():
    r = answers.answer("how", {"section": "home"}, home={})
    assert "numbers" in r["text"] or "Not enough" in r["text"]


def test_work_names_the_habit_in_words():
    t = answers.answer("work", {"section": "home"}, home={**HOME, "focus": {**HOME["focus"]}})["text"]
    assert "leaving pieces hanging" in t and "0.45" in t


def test_a_brand_new_account_is_told_where_to_start(monkeypatch):
    from coach import answers, insights
    monkeypatch.setattr(insights, "_games", lambda: [])
    home = {"player": "new", "games": 0}
    assert answers.answer("work", {"section": "home"}, home=home)["text"].startswith("Start with the Basics in Your course")
    assert "No games" in answers.answer("lose", {"section": "home"}, home=home)["text"]
