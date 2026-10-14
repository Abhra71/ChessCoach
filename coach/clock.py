"""Clock coach (flagship 5): where your time went, from the clock chess.com records on every move.

chess.com's game records keep each player's clock after every move ({[%clk 0:08:06.9]}). Knightwise used to throw
that away; here it shows where the time went and whether the moves that cost the most were played in a rush.
Every number comes from the game record; nothing is estimated.
"""
import io

import chess.pgn

from coach.review import biggest, move_number

FIRST_MOVES = 10  # "the opening part": your first ten moves


def base_and_increment(time_control):
    """'600' -> (600, 0), '180+2' -> (180, 2); daily games ('1/86400') and unknown ones -> None."""
    try:
        base, _, inc = str(time_control).partition("+")
        return int(base), int(inc or 0)
    except ValueError:
        return None


def rushed_under(base):
    """A move "in a rush": under 1.5% of the starting time, at least 2 seconds (9 s in a 10-minute game)."""
    return max(2.0, base * 0.015)


def spent(pgn, time_control):
    """[(ply, "white" | "black", seconds spent, clock after)] for every move with a clock, in order."""
    tc = base_and_increment(time_control)
    game = chess.pgn.read_game(io.StringIO(pgn or ""))
    if not tc or not game:
        return []
    base, inc = tc
    left = {"white": float(base), "black": float(base)}
    out = []
    for ply, node in enumerate(game.mainline(), start=1):
        clock = node.clock()
        if clock is None:
            return []  # no clock in this record
        side = "white" if ply % 2 else "black"
        out.append((ply, side, max(0.0, round(left[side] - clock + inc, 1)), clock))
        left[side] = clock
    return out


def say_time(seconds):
    s = int(round(seconds))
    if s < 60:
        return f"{s} second{'s' if s != 1 else ''}"
    m, s = divmod(s, 60)
    return f"{m} min {s} s" if s else f"{m} min"


def game_clock(g, me, rows):
    """The clock story of one game: up to three plain lines, plus the numbers behind them. None without a clock."""
    tc = base_and_increment(g.get("time_control"))
    times = spent(g.get("pgn"), g.get("time_control"))
    mine = [(ply, s, left) for ply, side, s, left in times if side == me]
    if not tc or len(mine) < 3:
        return None
    base, _ = tc
    lines = []
    first = sum(s for ply, s, _ in mine[:FIRST_MOVES])
    slow = max(mine, key=lambda x: x[1])
    by_ply = {ply: s for ply, s, _ in mine}
    on_time = g[me]["result"] == "timeout"
    if on_time:
        lines.append(f"You lost on time. Your first {min(FIRST_MOVES, len(mine))} moves took {say_time(first)} "
                     f"of your {say_time(base)}.")
    worst = max(biggest(rows), key=lambda r: r["loss"], default=None)
    rush = rushed_under(base)
    if worst and worst["ply"] in by_ply:
        t = by_ply[worst["ply"]]
        n = move_number(worst)
        if t < rush:
            lines.append(f"Move {n} cost you the most, and you played it in {say_time(t)}. "
                         "A few more seconds to check could have saved it.")
        else:
            lines.append(f"Move {n} cost you the most. You took {say_time(t)} on it: the time was there, "
                         "so the habit is what to work on.")
    if slow[1] >= max(20, base * 0.05):
        lines.append(f"Your longest think: {say_time(slow[1])} on move {(slow[0] + 1) // 2}.")
    return {"base": base, "lines": lines[:3], "on_time": on_time, "first_moves": round(first),
            "longest": {"move": (slow[0] + 1) // 2, "seconds": round(slow[1])},
            "left": round(mine[-1][2]), "average": round(sum(s for _, s, _ in mine) / len(mine), 1)}


def summary(games, moves, player, n=30):
    """Across your last n timed games: losses on time, and how fast the moves that cost the most were played."""
    from coach import insights
    timed, on_time, losses, fast, big = 0, 0, 0, 0, 0
    for g in games:
        if timed >= n or g["url"] not in moves:
            continue
        me = insights._side(g, player)[0]
        times = {ply: s for ply, side, s, _ in spent(g.get("pgn"), g.get("time_control")) if side == me}
        if not times:
            continue
        timed += 1
        result = insights._result(g, me)
        losses += result == "loss"
        on_time += g[me]["result"] == "timeout"
        rush = rushed_under(base_and_increment(g["time_control"])[0])
        for r in biggest(moves[g["url"]]):
            if r["ply"] in times:
                big += 1
                fast += times[r["ply"]] < rush
    if not timed:
        return None
    lines = []
    if big:
        lines.append(f"Of your {big} biggest mistakes in these games, {fast} were played in a rush: "
                     f"in a 10-minute game, that's under 9 seconds.")
    if on_time:
        lines.append(f"{on_time} of your {losses} losses were on time.")
    return {"games": timed, "on_time": on_time, "losses": losses, "big": big, "fast": fast, "lines": lines}


def rushed(games, moves, player, n=5):
    """The positions where your biggest mistakes were played in a rush, newest first: for the slow-down drill."""
    from coach import insights
    out = []
    for g in games:
        if len(out) >= n or g["url"] not in moves:
            continue
        me = insights._side(g, player)[0]
        tc = base_and_increment(g.get("time_control"))
        times = {ply: s for ply, side, s, _ in spent(g.get("pgn"), g.get("time_control")) if side == me}
        if not tc or not times:
            continue
        for r in biggest(moves[g["url"]]):
            if r["ply"] in times and times[r["ply"]] < rushed_under(tc[0]) and r.get("pattern"):
                out.append({**r, "seconds": times[r["ply"]]})
    return out[:n]
