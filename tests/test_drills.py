import chess
import chess.engine

from coach.analyze import open_engine
from coach.drills import drill, why_wrong


def test_why_wrong_names_the_capture():
    board = chess.Board("4k3/8/3p4/8/3Q4/8/8/4K3 w - - 0 1")
    move, reply = chess.Move.from_uci("d4e5"), chess.Move.from_uci("d6e5")
    assert why_wrong(board, move, reply) == "Then their pawn takes your queen on e5."


def test_drill_marks_hanging_the_queen_as_wrong_and_saving_it_as_right():
    # White queen d4, black pawn d6: Qe5 hangs the queen, Qd5 is safe.
    r = dict(fen="4k3/8/3p4/8/3Q4/8/8/4K3 w - - 0 1", move="Qe5", ply=1, url="g")
    with open_engine() as eng:
        d = drill(eng, "left a piece hanging", r)
    moves = d["steps"][0]["moves"]
    assert not moves["d4e5"]["good"]
    assert "takes your queen" in moves["d4e5"]["say"]
    assert moves["d4d5"]["good"] or moves["d4d5"].get("close")  # safe: right, or at least "playable"


def test_one_right_move_two_at_most():
    """13 Oct test: queen on b7, 8 moves were accepted, d3 among them, which lets ...Rb8 trap the queen."""
    r = dict(fen="r2qkb1r/pQ1p1ppp/2n5/8/4n3/8/PPPP1PPP/RNB1KBNR w KQkq - 0 7", move="Qb4", ply=13, url="g")
    with open_engine() as eng:
        d = drill(eng, "left a piece hanging", r)
    moves = d["steps"][0]["moves"]
    right = [m["san"] for m in moves.values() if m["good"]]
    assert 1 <= len(right) <= 2 and "Qb5" in right
    assert not moves["d2d3"]["good"] and not moves["d2d3"].get("close")
    assert "Qb4" not in right


def test_puzzle_shows_their_move_then_accepts_the_mate():
    from coach.drills import puzzle
    # Black blunders Nf6?? and White mates with Qxf7#.
    p = {"id": "abc", "rating": 600, "moves": ["g8f6", "h5f7"],
         "fen": "r1bqkbnr/pppp1ppp/2n5/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR b KQkq - 3 3"}
    d = puzzle(p, "missed a checkmate")
    assert d["intro"] == "They just played Nf6. You are White: find the best move."
    assert d["last"] == ["g8", "f6"]
    [s] = d["steps"]
    assert s["moves"]["h5f7"]["good"] and s["moves"]["h5f7"]["san"] == "Qxf7#"
    assert not s["moves"]["h5h6"]["good"]
    assert s["reply"] is None
    assert d["url"] == "https://lichess.org/training/abc"


def test_two_move_puzzle_has_their_answer_between():
    from coach.drills import puzzle
    # After 1.d4 f5: Black plays e5, White takes, Black plays d6, White takes again.
    p = {"id": "x", "rating": 500, "moves": ["e7e5", "d4e5", "d7d6", "e5d6"],
         "fen": "rnbqkbnr/ppppp1pp/8/5p2/3P4/8/PPP1PPPP/RNBQKBNR b KQkq - 0 2"}
    d = puzzle(p, "missed a free capture")
    assert len(d["steps"]) == 2
    assert d["steps"][0]["reply"]["san"] == "d6"
    assert d["steps"][1]["moves"]["e5d6"]["good"]


def test_a_puzzle_says_why_it_ends():
    """13 Oct test: a queen ending stopped with the player's queen taken and "correct", with no reason given."""
    from coach.drills import why_it_ends
    from coach.drills import squares
    start = chess.Board("4k3/8/8/8/8/8/3q4/3QK3 w - - 0 1")  # queens on the board, level
    traded = chess.Board("4k3/8/8/8/8/8/8/4K3 w - - 0 1")
    assert "queens are off" in why_it_ends(squares(start), traded, True, [])
    up = chess.Board("4k3/8/8/8/8/8/8/3QK3 w - - 0 1")
    assert why_it_ends(squares(start), up, True, ["crushing"]).startswith("You've won a queen")
    mate = chess.Board("R5k1/5ppp/8/8/8/8/8/6K1 b - - 0 1")
    assert why_it_ends(squares(start), mate, True, ["mate"]).startswith("Checkmate")


def test_lesson_puzzles_match_the_lesson_and_the_level():
    """The stalemate lesson ("winning with the queen") takes only queen endings that end in mate; puzzles are the
    easiest of the theme when there are too few at the player's level, never a random 1428 for a 254 player."""
    import random
    from coach import plan
    if not plan.PUZZLES.exists():
        return
    queen = plan._puzzles("queenEndgame", 254, random.Random(1))
    assert queen and all(any(t.startswith("mate") for t in d["themes"]) for d in queen)
    ratings = [d["rating"] for d in plan._puzzles("trappedPiece", 254, random.Random(1))]
    assert ratings == sorted(ratings) and max(ratings) < 1000
