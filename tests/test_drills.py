import chess
import chess.engine

from coach.analyze import ENGINE
from coach.drills import drill, why_wrong


def test_why_wrong_names_the_capture():
    board = chess.Board("4k3/8/3p4/8/3Q4/8/8/4K3 w - - 0 1")
    move, reply = chess.Move.from_uci("d4e5"), chess.Move.from_uci("d6e5")
    assert why_wrong(board, move, reply) == "Then their pawn takes your queen on e5 (dxe5)."


def test_drill_marks_hanging_the_queen_as_wrong_and_saving_it_as_right():
    # White queen d4, black pawn d6: Qe5 hangs the queen, Qd5 is safe.
    r = dict(fen="4k3/8/3p4/8/3Q4/8/8/4K3 w - - 0 1", move="Qe5", ply=1, url="g")
    with chess.engine.SimpleEngine.popen_uci(str(ENGINE)) as eng:
        d = drill(eng, "left a piece hanging", r)
    assert not d["moves"]["d4e5"]["good"]
    assert "takes your queen" in d["moves"]["d4e5"]["say"]
    assert d["moves"]["d4d5"]["good"]
