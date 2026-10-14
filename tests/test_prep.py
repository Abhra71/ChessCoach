from coach import prep

PGN = '[Event "x"]\n\n1. e4 e5 2. Nf3 1-0'


def g(white, black, wres, bres, pgn=PGN):
    return {"white": {"username": white, "result": wres, "rating": 500}, "black": {"username": black, "result": bres, "rating": 480},
            "time_class": "rapid", "pgn": pgn, "end_time": 1, "eco": "https://www.chess.com/openings/Kings-Pawn-Opening"}


def test_their_openings_and_how_their_games_end():
    games = [g("them", "x", "win", "checkmated"), g("them", "y", "timeout", "win"), g("z", "them", "win", "checkmated")]
    s = prep.scout("them", me="me", games=games, mine=[])
    assert s["as_white"][0] == {"what": "e4", "games": 2, "share": 100}
    assert s["as_black"][0]["what"] == "e4 e5"
    assert s["endings"] == {"won": 1, "lost on time": 1, "lost by checkmate": 1}
    assert any("on time" in a for a in s["advice"]) and any("checkmated" in a for a in s["advice"])


def test_your_score_against_their_favourite_first_move():
    theirs = [g("them", "x", "win", "resigned") for _ in range(5)]
    mine = [g("other", "me", "resigned", "win") for _ in range(3)]  # you won 3 of 3 as Black against 1.e4
    s = prep.scout("them", me="me", games=theirs, mine=mine)
    assert any("you score 100% in 3 games: that one is yours" in a for a in s["advice"])


def test_no_games_no_prep():
    assert prep.scout("them", me="me", games=[], mine=[]) is None
