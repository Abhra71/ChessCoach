from coach.review import explain, move_number, pick_examples


def rec(**kw):
    base = dict(url="g1", ply=1, loss=40, cp_before=0, cp_after=-500, time_class="rapid", reply_pv=[])
    return {**base, **kw}


def test_move_number():
    assert move_number(rec(ply=1)) == 1   # white's first move
    assert move_number(rec(ply=2)) == 1   # black's first move
    assert move_number(rec(ply=31)) == 16


def test_hanging_sentence_names_the_pieces():
    # White queen to e5, the d6 pawn takes it.
    r = rec(fen="4k3/8/3p4/8/3Q4/8/8/4K3 w - - 0 1", move="Qe5", best="Qd5", reply_pv=["d6e5"])
    assert explain("left a piece hanging", r) == "After Qe5, their pawn on d6 can take your queen on e5."


def test_missed_capture_sentence():
    r = rec(fen="4k3/8/8/3q4/4P3/8/8/4K3 w - - 0 1", move="Kf2", best="exd5")
    assert explain("missed a free capture", r) == "Their queen on d5 was there to take: your pawn takes it with exd5."


def test_examples_one_per_game_turning_points_first():
    rows = [rec(url="a", loss=90, cp_before=-500), rec(url="b", loss=40), rec(url="b", loss=60),
            rec(url="c", loss=30, time_class="bullet"), rec(url="d", loss=30)]
    assert [r["url"] for r in pick_examples(rows)] == ["b", "d", "c"]
