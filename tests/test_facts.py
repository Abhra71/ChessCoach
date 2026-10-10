import chess

from coach.facts import describe_move, loose_pieces


def test_moving_a_defender_away_leaves_a_piece_loose():
    # White bishop d3 is guarded by the c2 pawn; their queen on d5 attacks it. c3 abandons the bishop.
    board = chess.Board("rnb1kbnr/ppp1ppp1/8/3q3p/8/3B4/PPPP1PPP/RNBQK1NR w KQkq - 0 4")
    assert "bishop on d3" not in loose_pieces(board, chess.WHITE)
    assert describe_move(board, chess.Move.from_uci("c2c3")) == "pawn c2 to c3 (leaves loose: bishop on d3)"


def test_king_cannot_take_a_protected_piece():
    # Rook on e7 gives check, protected by the bishop on h4: their king touches it but can't take it.
    board = chess.Board("r6r/pppkRp2/7n/2PP3p/7B/7P/PP4P1/nN1K4 b - - 2 24")
    assert "rook on e7" not in loose_pieces(board, chess.WHITE)


def test_capture_and_check_described():
    board = chess.Board("4k3/8/8/3q4/8/8/8/3QK3 w - - 0 1")
    assert describe_move(board, chess.Move.from_uci("d1d5")) == "queen d1 to d5 (takes the queen on d5)"
