"""What turns over when (25 Oct): daily sets at the player's own midnight, a lesson's positions kept until it's
finished, and Practice made new the moment it's asked for on a new day."""
import json
from datetime import date

from coach import daylock


def test_a_days_set_stays_all_day_and_is_new_the_next(tmp_path, monkeypatch):
    monkeypatch.setattr(daylock, "FILE", tmp_path / "today-sets.json")
    first = daylock.keep("practice", [{"id": "a"}], today=date(2026, 10, 25))
    assert daylock.keep("practice", [{"id": "b"}], today=date(2026, 10, 25)) == first  # same day: unchanged
    assert daylock.keep("practice", [{"id": "c"}], today=date(2026, 10, 26)) == [{"id": "c"}]  # after midnight: new


def test_a_lesson_keeps_its_positions_until_it_is_finished(tmp_path, monkeypatch):
    monkeypatch.setattr(daylock, "KEPT", tmp_path / "kept-sets.json")
    first = daylock.keep_until_done("course:x", [{"id": "a"}])
    assert daylock.keep_until_done("course:x", [{"id": "b"}]) == first  # another day, another ask: the same
    daylock.release("course:x")
    assert daylock.keep_until_done("course:x", [{"id": "c"}]) == [{"id": "c"}]  # finished: new ones next time
    daylock.release("never-kept")  # nothing to release: no error
    assert json.loads((tmp_path / "kept-sets.json").read_text()) == {"course:x": [{"id": "c"}]}
