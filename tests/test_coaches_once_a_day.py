"""A repeat visit says where things stand once a day, not every time (22 Oct test)."""
from coach import coaches


def test_same_stat_once_a_day(tmp_path, monkeypatch):
    monkeypatch.setattr(coaches, "SAID", tmp_path / "said.json")
    assert coaches.fresh_today("0.8 pieces a game", today="2026-10-22")
    assert not coaches.fresh_today("0.8 pieces a game", today="2026-10-22")
    assert coaches.fresh_today("something new", today="2026-10-22")
    assert coaches.fresh_today("0.8 pieces a game", today="2026-10-23")
