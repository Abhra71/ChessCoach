from coach.patterns import classify


def rec(**kw):
    base = dict(stalemate=False, cp_before=0, loss=40, best_mates=False, allows_mate=False,
                reply_pv=[], mat_before=0, best_is_capture=False)
    return {**base, **kw}


def test_small_loss_is_not_a_mistake():
    assert classify(rec(loss=5, fen="4k3/8/8/8/8/8/8/4K3 w - - 0 1", move="Kd1")) is None


def test_hung_queen():
    # White queen goes to e5, where the d6 pawn takes it.
    r = rec(fen="4k3/8/3p4/8/3Q4/8/8/4K3 w - - 0 1", move="Qe5", reply_pv=["d6e5"], mat_before=8)
    assert classify(r) == "left a piece hanging"


def test_stalemate_when_winning():
    assert classify(rec(stalemate=True, cp_before=900, loss=50)) == "stalemated a won game"


def test_walked_into_mate():
    r = rec(allows_mate=True, cp_before=50, fen="4k3/8/8/8/8/8/8/4K3 w - - 0 1", move="Kd1")
    assert classify(r) == "walked into checkmate"
