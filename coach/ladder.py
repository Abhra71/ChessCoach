"""The level ladder (0.6): from beginner to 2,000+, one level at a time, measured on your own games.

Five levels, each with a few skills. Every skill is a number from your last 20 checked games (Stockfish's check of
every move you played, the game record and its clock), a target, and the training for it in Knightwise. A level is
done when all its skills meet their targets; the coach works on the first level that isn't done yet.

The targets are our first estimate of what each level looks like, to be tuned on real players' games; the page
says so. Nothing here promises a rating.
"""
import io

import chess
import chess.pgn

from coach import clock, insights
from coach.review import biggest

WINDOW = 20  # the last 20 checked games
WINNING = 300  # "you were winning": a position at least 3 pawns up, by the engine's count
HANG, FORK, MATED = "left a piece hanging", "walked into a fork or trick", "walked into checkmate"
FREE, MISSED_MATE, STALEMATE = "missed a free capture", "missed a checkmate", "stalemated a won game"


def _per_game(games, moves, test):
    return sum(1 for g in games for r in moves[g["url"]] if test(r)) / len(games)


def _pattern(p):
    return lambda games, moves, ctx: _per_game(games, moves, lambda r: r["pattern"] == p)


def _losses(low, high=101):  # moves that cost between low and high points of your chance to win
    return lambda games, moves, ctx: _per_game(games, moves, lambda r: low <= r["loss"] < high)


def _average_loss(games, moves, ctx):
    rows = [max(0.0, r["loss"]) for g in games for r in moves[g["url"]]]
    return sum(rows) / len(rows) if rows else 0.0


def _conversion(games, moves, ctx):
    """Of the games where you were winning (3 pawns up or more), the share you won. None if there were none."""
    won = [g for g in games if any(r["cp_before"] >= WINNING for r in moves[g["url"]])]
    if not won:
        return None
    return 100 * sum(insights._result(g, insights._side(g, ctx["player"])[0]) == "win" for g in won) / len(won)


def _development(games, moves, ctx):
    """The share of games where you had 3 of your 4 knights and bishops out and had castled by move 12."""
    good = 0
    for g in games:
        me = chess.WHITE if insights._side(g, ctx["player"])[0] == "white" else chess.BLACK
        game = chess.pgn.read_game(io.StringIO(g.get("pgn", "")))
        if not game:
            continue
        board, castled = game.board(), False
        home = {sq for sq in (chess.B1, chess.C1, chess.F1, chess.G1)} if me == chess.WHITE else \
               {chess.B8, chess.C8, chess.F8, chess.G8}
        for move in list(game.mainline_moves())[:24]:  # 12 moves each
            if board.turn == me and board.is_castling(move):
                castled = True
            board.push(move)
        out = sum(1 for sq in home if not (board.piece_at(sq) and board.piece_at(sq).color == me
                                           and board.piece_at(sq).piece_type in (chess.KNIGHT, chess.BISHOP)))
        good += out >= 3 and castled
    return 100 * good / len(games)


def _rushed(games, moves, ctx):
    """The share of your biggest mistakes played in a rush (under 9 seconds in a 10-minute game). None without clocks."""
    fast = big = 0
    for g in games:
        tc = clock.base_and_increment(g.get("time_control"))
        me = insights._side(g, ctx["player"])[0]
        times = {ply: s for ply, side, s, _ in clock.spent(g.get("pgn"), g.get("time_control")) if side == me}
        if not tc or not times:
            continue
        for r in biggest(moves[g["url"]]):
            if r["ply"] in times:
                big += 1
                fast += times[r["ply"]] < clock.rushed_under(tc[0])
    return 100 * fast / big if big else None


def _stalemates(games, moves, ctx):
    return sum(1 for g in games for r in moves[g["url"]] if r["pattern"] == STALEMATE)


# (id, name, what it means, measure, target, "at most" or "at least", unit, training: (label, app route))
LEVELS = [
    ("safe", "Safe pieces", "up to about 800", [
        ("hang", "Keep every piece safe", "pieces left hanging a game", _pattern(HANG), 0.3, "max", "a game",
         ("Practise it", "practice/" + HANG)),
        ("free", "Take what they leave you", "free pieces missed a game", _pattern(FREE), 0.3, "max", "a game",
         ("Practise it", "practice/" + FREE)),
        ("mated", "Watch for their checks", "games where you walked into checkmate", _pattern(MATED), 0.05, "max", "a game",
         ("Learn it", "lesson/backRankMate")),
        ("finish", "Finish with checkmate", "checkmates missed a game", _pattern(MISSED_MATE), 0.1, "max", "a game",
         ("Learn it", "lesson/mateIn1")),
        ("stalemate", "Win won games", "won games you stalemated, in 20 games", _stalemates, 0, "max", "",
         ("Train it", "endgame/queen")),
    ]),
    ("tactics", "Tactics and good starts", "about 800 to 1,200", [
        ("forks", "See their forks and tricks", "forks and tricks walked into a game", _pattern(FORK), 0.2, "max", "a game",
         ("Practise it", "practice/" + FORK)),
        ("blunders1", "Fewer big mistakes", "big mistakes a game", _losses(20), 1.0, "max", "a game",
         ("Learn pins", "lesson/pin")),
        ("convert1", "Turn winning games into wins", "winning games you won", _conversion, 70, "min", "%",
         ("Train it", "endgame/pawn")),
        ("develop", "Start well", "games with 3 pieces out and castled by move 12", _development, 60, "min", "%",
         ("Your opening tree", "openings")),
    ]),
    ("club", "Fewer mistakes", "about 1,200 to 1,600", [
        ("blunders2", "Rarely a big mistake", "big mistakes a game", _losses(20), 0.6, "max", "a game",
         ("Learn skewers", "lesson/skewer")),
        ("mistakes2", "Fewer medium mistakes", "medium mistakes a game", _losses(10, 20), 1.5, "max", "a game",
         ("Learn discovered attacks", "lesson/discoveredAttack")),
        ("convert2", "Win won games, nearly always", "winning games you won", _conversion, 80, "min", "%",
         ("Train it", "endgame/queenpawn")),
        ("clock", "Slow down when it matters", "biggest mistakes played in a rush", _rushed, 25, "max", "%",
         ("Slow-down drill", "clockdrill")),
    ]),
    ("precise", "Precision", "about 1,600 to 2,000", [
        ("blunders3", "Almost no big mistakes", "big mistakes a game", _losses(20), 0.3, "max", "a game",
         ("See it in your head", "calc")),
        ("mistakes3", "Few medium mistakes", "medium mistakes a game", _losses(10, 20), 1.0, "max", "a game",
         ("Learn it", "lesson/capturingDefender")),
        ("small3", "Few small slips", "small slips a game", _losses(5, 10), 2.5, "max", "a game",
         ("Learn the quiet move", "lesson/quietMove")),
        ("average3", "Steady play", "of your chance to win lost per move, on average", _average_loss, 2.0, "max", "points",
         ("Learn zugzwang", "lesson/zugzwang")),
    ]),
    ("expert", "Expert", "2,000 and above", [
        ("blunders4", "Big mistakes are rare", "big mistakes a game", _losses(20), 0.15, "max", "a game",
         ("See it in your head", "calc")),
        ("mistakes4", "Medium mistakes are rare", "medium mistakes a game", _losses(10, 20), 0.6, "max", "a game",
         ("Learn it", "lesson/promotion")),
        ("average4", "Very steady play", "of your chance to win lost per move, on average", _average_loss, 1.3, "max", "points",
         ("Learn the in-between move", "lesson/intermezzo")),
        ("convert4", "Win every won game", "winning games you won", _conversion, 90, "min", "%",
         ("Learn it", "lesson/rookEndgame")),
    ]),
]


def ladder(games, moves, player, window=WINDOW):
    """Every level and skill against your last `window` checked games, and the level to work on now."""
    checked = [g for g in games if g["url"] in moves][:window]
    if not checked:
        return None
    ctx = {"player": player}
    levels, current = [], None
    for lid, name, band, skills in LEVELS:
        out = []
        for sid, sname, what, measure, target, way, unit, (label, route) in skills:
            value = measure(checked, moves, ctx)
            met = None if value is None else (value <= target if way == "max" else value >= target)
            out.append({"id": sid, "name": sname, "what": what, "value": None if value is None else round(value, 2),
                        "target": target, "way": way, "unit": unit, "met": met, "train": {"label": label, "route": route}})
        done = all(s["met"] is not False for s in out)
        if not done and current is None:
            current = len(levels)
        levels.append({"id": lid, "name": name, "band": band, "skills": out, "done": done})
    return {"games": len(checked), "levels": levels, "current": len(levels) - 1 if current is None else current}


def page():
    player = insights._player()
    if not player:
        return {"player": None}
    return {"player": player, **(ladder(insights._games(), insights._moves(), player) or {"levels": []})}


def focus(page_data):
    """The one skill to work on now: the first one not met at the current level (for the coaches and Talk)."""
    if not page_data.get("levels"):
        return None
    level = page_data["levels"][page_data["current"]]
    skill = next((s for s in level["skills"] if s["met"] is False), None)
    return {"level": level["name"], "band": level["band"], **skill} if skill else None


