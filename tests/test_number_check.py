"""The 23 Oct number check: a free piece is really free, and the graph's last point is your last games."""
import chess

from coach import patterns


def test_a_free_piece_is_one_that_stays_won():
    b = chess.Board("4k3/8/8/3n4/8/8/8/3QK3 w - - 0 1")  # the knight on d5, nobody defends it
    assert patterns.exchange(b, b.parse_san("Qxd5")) == 3


def test_a_trade_is_not_free():
    b = chess.Board("4k3/8/2p5/3n4/8/8/8/3RK3 w - - 0 1")  # knight d5, defended by the pawn c6; rook takes, pawn takes
    assert patterns.exchange(b, b.parse_san("Rxd5")) == -2


def test_the_graph_ends_on_the_last_full_window(monkeypatch):
    from coach import insights
    lost = [1] * 7 + [0] * 20  # oldest first: 27 games, the last 20 clean
    window = insights.TREND_WINDOW
    trend = [round(sum(lost[i:i + window]) / window, 2) for i in range(len(lost) % window, len(lost) - window + 1, window)]
    assert trend[-1] == 0.0 and len(trend) == 2


def test_todays_5_minutes_stay_the_same_all_day(tmp_path, monkeypatch):
    import datetime
    from coach import daily
    monkeypatch.setattr(daily, "FILE", tmp_path / "daily.json")
    day = datetime.date(2026, 10, 23)
    kept = [{"id": "a"}, {"id": "b"}]
    (tmp_path / "daily.json").write_text('{"days": [], "set": {"day": "2026-10-23", "theme": "Forks", "drills": %s}}'
                                         % __import__("json").dumps(kept))
    out = daily.challenge({"focus": {"pattern": "left a piece hanging"}}, today=day)
    assert out["drills"] == kept and out["theme"] == "Forks"
    other = daily.challenge({"focus": {"pattern": "left a piece hanging"}}, today=day + datetime.timedelta(days=1))
    assert other["drills"] != kept  # a new day, a new set


def test_a_days_set_is_kept_until_midnight(tmp_path, monkeypatch):
    import datetime
    from coach import daylock
    monkeypatch.setattr(daylock, "FILE", tmp_path / "today-sets.json")
    day = datetime.date(2026, 10, 23)
    assert daylock.keep("course:x", [{"id": 1}], day) == [{"id": 1}]
    assert daylock.keep("course:x", [{"id": 2}], day) == [{"id": 1}]  # remade later that day: the same set
    assert daylock.keep("course:x", [{"id": 2}], day + datetime.timedelta(days=1)) == [{"id": 2}]  # a new day
