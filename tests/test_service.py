from coach.service import game_id, key_moments

HANG = dict(url="https://www.chess.com/game/live/42", color="white", stalemate=False, cp_before=0, cp_after=-800,
            best_mates=False, allows_mate=False, best_is_capture=False, mat_before=8, loss=45,
            fen="4k3/8/3p4/8/3Q4/8/8/4K3 w - - 0 1", move="Qe5", best="Qd5", reply_pv=["d6e5"], ply=31)


def test_game_id():
    assert game_id("https://www.chess.com/game/live/143843521880") == "143843521880"


def test_key_moment_has_arrows_and_words():
    [m] = key_moments([HANG, dict(HANG, loss=2, ply=33)])  # the small slip is not a key moment
    assert (m["move_uci"], m["best_uci"], m["reply_uci"]) == ("d4e5", "d4d5", "d6e5")
    assert m["placement"] == "4k3/8/3p4/8/3Q4/8/8/4K3"
    assert m["after_placement"] == "4k3/8/3p4/4Q3/8/8/8/4K3"
    assert m["say"] == "After Qe5, their pawn on d6 can take your queen on e5."
    assert m["move_number"] == 16


def test_at_most_three_moments_in_game_order():
    rows = [dict(HANG, ply=p, loss=30 + p) for p in (11, 21, 31, 41)]
    assert [m["ply"] for m in key_moments(rows)] == [21, 31, 41]


def test_only_one_copy_can_run():
    import pytest
    from coach.service import Handler, Server
    first = Server(("127.0.0.1", 0), Handler)
    try:
        with pytest.raises(OSError):
            Server(("127.0.0.1", first.server_address[1]), Handler)
    finally:
        first.server_close()
