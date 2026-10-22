"""One-click feedback: at most four sends a day from one PC."""
from coach import service


def test_four_a_day(tmp_path, monkeypatch):
    monkeypatch.setattr(service, "DATA", tmp_path)
    assert [service.feedback_send_allowed("2026-10-22") for _ in range(5)] == [True] * 4 + [False]
    assert service.feedback_send_allowed("2026-10-23")  # a new day
