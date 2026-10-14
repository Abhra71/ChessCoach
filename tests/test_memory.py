from datetime import date

import pytest

from coach import memory


@pytest.fixture(autouse=True)
def tmp_files(tmp_path, monkeypatch):
    monkeypatch.setattr(memory, "PRACTICE", tmp_path / "practice.jsonl")
    monkeypatch.setattr(memory, "VERDICTS", tmp_path / "verdicts.jsonl")


D = date(2026, 10, 10)


def day(n):
    return date.fromordinal(D.toordinal() + n)


def test_new_positions_come_first_in_given_order():
    assert memory.choose(["a", "b", "c"], 2, today=D) == ["a", "b"]


def test_wrong_answer_comes_back_tomorrow_before_new_ones():
    memory.record_practice("a", "game", False, day=D)
    assert memory.choose(["a", "b"], 5, today=D) == ["a", "b"]     # today's set stays the same after a rebuild
    assert memory.choose(["a", "b"], 5, today=day(1)) == ["a", "b"]  # tomorrow, first


def test_answered_today_stay_in_todays_set_before_new_ones():
    memory.record_practice("c", "game", True, day=D)
    assert memory.choose(["a", "b", "c"], 2, today=D) == ["c", "a"]
    assert memory.choose(["a", "b", "c"], 2, today=day(1)) == ["a", "b"]  # a new day: new positions first


def test_right_answers_space_out():
    memory.record_practice("a", "game", True, day=D)       # box 1: back after 1 day
    assert memory.choose(["a"], 5, today=day(1)) == ["a"]
    memory.record_practice("a", "game", True, day=day(1))  # box 2: back after 3 days
    assert memory.choose(["a"], 5, today=day(3)) == []
    assert memory.choose(["a"], 5, today=day(4)) == ["a"]


def test_stats_and_verdict():
    for n in range(3):
        memory.record_practice("a", "game", True, day=day(n))
    memory.record_practice("b", "puzzle", False, day=D)
    memory.record_verdict("yes", day=D)
    assert memory.practice_stats() == {"answers": 4, "right": 3, "positions": 2, "right_first": 1, "learned": 1}
    assert memory._read(memory.VERDICTS) == [{"answer": "yes", "day": "2026-10-10"}]


def test_only_the_first_answer_of_the_day_counts():
    """13 Oct test: solving the same puzzle again raised "right first time" from 4 to 6."""
    assert memory.record_practice("a", "puzzle", False, day=D)
    assert not memory.record_practice("a", "puzzle", True, day=D)  # back to it, solved: changes nothing
    assert not memory.record_practice("a", "puzzle", True, day=D)
    assert memory.practice_stats()["right_first"] == 0
    assert memory.today(day=D) == {"a": "missed"}
    memory.record_practice("b", "opening", True, day=D, shown=True)  # Show answer is never "right"
    assert memory.today(["b"], day=D) == {"b": "shown"}
    assert memory.practice_stats()["right"] == 0
