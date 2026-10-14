from coach import clock

PGN = """[Event "Live Chess"]

1. e4 {[%clk 0:09:58]} 1... e5 {[%clk 0:09:50]} 2. Nf3 {[%clk 0:09:00]} 2... Nc6 {[%clk 0:09:48]} 3. Bc4 {[%clk 0:08:57]} 3... d6 {[%clk 0:09:20]} 1-0"""


def test_time_spent_on_each_move_from_the_recorded_clock():
    times = clock.spent(PGN, "600")
    assert [(p, side, s) for p, side, s, _ in times] == [
        (1, "white", 2.0), (2, "black", 10.0), (3, "white", 58.0), (4, "black", 2.0), (5, "white", 3.0), (6, "black", 28.0)]


def test_increment_is_added_back_and_daily_games_have_no_clock():
    assert clock.spent(PGN, "600+2")[2][2] == 60.0
    assert clock.base_and_increment("1/86400") is None and clock.spent(PGN, "-") == []


def test_a_rush_scales_with_the_time_control():
    assert clock.rushed_under(600) == 9.0 and clock.rushed_under(60) == 2.0


def test_say_time():
    assert clock.say_time(1) == "1 second" and clock.say_time(68) == "1 min 8 s" and clock.say_time(120) == "2 min"
