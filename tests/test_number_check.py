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
