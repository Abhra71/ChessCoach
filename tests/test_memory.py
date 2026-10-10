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
    assert memory.choose(["a", "b"], 5, today=D) == ["b"]          # not again today
    assert memory.choose(["a", "b"], 5, today=day(1)) == ["a", "b"]  # tomorrow, first


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
    assert memory.practice_stats() == {"answers": 4, "right": 3, "positions": 2, "learned": 1}
    assert memory._read(memory.VERDICTS) == [{"answer": "yes", "day": "2026-10-10"}]
