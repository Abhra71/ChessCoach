"""The reasons the coach gives for a mistake: each one checked on a real position, never guessed."""
import chess

from coach import why


def rec(fen, move, best, reply_pv=(), loss=30, ply=30, **kw):
    r = dict(fen=fen, move=move, best=best, reply_pv=list(reply_pv), loss=loss, ply=ply, cp_before=0,
             stalemate=False, best_mates=False, allows_mate=False)
    return {**r, **kw}


def test_a_piece_put_where_it_can_be_taken():
    e = why.explain(rec("rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2", "Ba6", "Nf3", ["b7a6"], ply=3))
    assert e["idea"] == "hanging"
    assert e["say"].startswith("You put your bishop on a6, where nothing guards it: their pawn just takes it.")


def test_a_fork_after_your_move():
    e = why.explain(rec("4k3/8/8/8/3n4/8/8/R3K2R w - - 0 1", "Rh3", "Kd2", ["d4c2", "e1d2", "c2a1"]))
    assert e["idea"] == "fork"
    assert "their knight comes to c2 and attacks your king and rook at once" in e["say"]


def test_moving_the_guard():
    e = why.explain(rec("4r1k1/8/8/4B3/8/5N2/8/4K3 w - - 0 1", "Ng5", "Kd2", ["e8e5", "e1d2"]))
    assert e["idea"] == "defender"
    assert e["say"] == ("Your knight on f3 was guarding your bishop on e5. When it moved, their rook could take it.")


def test_a_threat_not_answered():
    e = why.explain(rec("4r1k1/8/8/4B3/8/8/8/3K4 w - - 0 1", "Kc2", "Bd4", ["e8e5"]))
    assert e["idea"] == "threats"
    assert e["say"].startswith("Your bishop on e5 was already under attack, and Kc2 did nothing about it")


def test_a_free_piece_not_taken():
    e = why.explain(rec("4k3/8/8/3n4/8/8/8/3QK3 w - - 0 1", "Ke2", "Qxd5"))
    assert e["idea"] == "free"
    assert e["say"] == "Their knight on d5 was there to take: Qxd5 wins it."


def test_back_rank_mate_only_when_the_pawns_shut_the_king_in():
    e = why.explain(rec("3r2k1/5ppp/8/8/8/P7/5PPP/6K1 w - - 0 1", "a4", "h3", ["d8d1"], allows_mate=True))
    assert e["idea"] == "back_rank"
    # 13 Oct, a real game: the uncastled king mated by Qd8 with open squares in front is not a back-rank lesson
    e = why.explain(rec("r1b1kbnr/pp2pppp/8/1qpQ2B1/N3P2P/1P4PB/P1P2P2/R3K1NR b KQkq - 0 12", "e6", "Nf6", ["d5d8"],
                        allows_mate=True))
    assert e["idea"] == "king_danger" and "checkmate in one: Qd8#" in e["say"]


def test_stalemate_in_a_won_game():
    e = why.explain(rec("k7/8/1K6/8/8/8/8/2Q5 w - - 0 1", "Qc7", "Qc8#", stalemate=True, cp_before=2000, loss=50))
    assert e["idea"] == "stalemate"


def test_queen_out_early():
    e = why.explain(rec("rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2", "Qf6", "Nc6", ["b1c3"],
                        loss=10, ply=4))
    assert e["idea"] == "development"
    assert "4 of your knights and bishops are still at home" in e["say"]


def test_centre_before_edge_pawns():
    e = why.explain(rec(chess.STARTING_FEN, "a3", "e4", ["e7e5"], loss=8, ply=1))
    assert e["idea"] == "centre"


def test_skewer_looks_behind_the_piece_not_beside_it():
    b = chess.Board("4k3/8/8/8/1b6/8/3K4/4R3 w - - 0 1")  # bishop b4, king d2, rook e1 behind it
    assert why._skewer(b, chess.B4) == (chess.D2, chess.E1)
    b = chess.Board("4k3/8/8/R7/1b6/8/3K4/8 w - - 0 1")  # the rook is on the other side of the bishop
    assert why._skewer(b, chess.B4) is None


def test_no_simple_reason_is_said_honestly():
    e = why.explain(rec("4k3/8/8/8/8/8/4P3/4K3 w - - 0 1", "Kd1", "Kd2", loss=8))
    assert e["idea"] == "deeper"
    assert "a few moves deep" in e["say"]
