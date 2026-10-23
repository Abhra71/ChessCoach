"""How to beat them (coach/scout.py): the parts that don't need Stockfish or chess.com."""
from coach import scout


def _g(user, side, result, eco="Italian-Game", end=0, tc="600", kind="rapid"):
    other = "x" if side == "black" else "y"
    return {"white": {"username": user if side == "white" else other, "result": result if side == "white" else "win"},
            "black": {"username": user if side == "black" else other, "result": result if side == "black" else "win"},
            "eco": f"https://www.chess.com/openings/{eco}", "end_time": end, "time_control": tc, "time_class": kind,
            "pgn": "1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. c3 Nf6 5. d4 exd4 6. cxd4 Bb4+ 7. Bd2 Bxd2+ 8. Nbxd2 d5 "
                   "9. exd5 Nxd5 10. Qb3 Na5 *", "url": f"u{end}"}


def test_worst_opening_needs_three_games_and_a_low_score():
    games = [_g("me", "white", "resigned", "Italian-Game", i) for i in range(3)] + \
            [_g("me", "white", "win", "Ruy-Lopez", 10 + i) for i in range(3)]
    w = scout.worst_opening(games, "me")
    assert w == {"name": "Italian Game", "score": 0, "games": 3}
    assert scout.worst_opening(games[:2], "me") is None  # two games: too few to say


def test_latest_keeps_their_main_time_class_newest_first():
    games = [_g("me", "white", "win", end=i, kind="rapid") for i in range(15)] + [_g("me", "white", "win", end=99, kind="blitz")]
    got = scout.latest(games, "me", n=12)
    assert len(got) == 12 and all(g["time_class"] == "rapid" for g in got) and got[0]["end_time"] == 14


def test_tips_come_from_the_numbers():
    s = {"habits": [{"pattern": "left a piece hanging"}], "phases": {"opening": 0, "middlegame": 1, "endgame": 4},
         "clock": {"low": 3, "of": 5}, "slipped": {"lost": 0, "of": 0}, "worst_opening": None}
    t = scout.tips(s)
    assert len(t) == 3 and "undefended" in t[0] and "endgame" in t[1] and "clock" in t[2]
    quiet = {"habits": [], "phases": {"opening": 0, "middlegame": 0, "endgame": 0}, "clock": {"low": 0, "of": 0},
             "slipped": {"lost": 0, "of": 0}, "worst_opening": None}
    assert scout.tips(quiet) == ["No clear weakness: play solid, safe moves and check what they can take."]


def test_phase():
    assert scout.phase({"ply": 10, "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"}) == "opening"
    assert scout.phase({"ply": 60, "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"}) == "middlegame"
    assert scout.phase({"ply": 60, "fen": "4k3/pp3r2/8/8/8/8/PP2R3/4K3 w - - 0 1"}) == "endgame"
