from coach import ladder

PGN = """[Event "x"]

1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. O-O Nf6 5. d3 d6 1-0"""


def game(url, result="win", cp=0):
    return {"url": url, "white": {"username": "me", "result": result, "rating": 500},
            "black": {"username": "them", "result": "checkmated" if result == "win" else "win", "rating": 500},
            "time_class": "rapid", "time_control": "600", "pgn": PGN, "end_time": 1}


def row(pattern=None, loss=1.0, cp=0, ply=1):
    return {"pattern": pattern, "loss": loss, "cp_before": cp, "ply": ply}


def test_a_level_is_done_only_when_every_skill_meets_its_goal(monkeypatch):
    from coach import course
    games = [game(f"g{i}") for i in range(10)]
    clean = {g["url"]: [row()] for g in games}
    monkeypatch.setattr(course, "tags", lambda moves: {})
    page = ladder.ladder(games, clean, "me")
    assert page["levels"][0]["done"] and page["current"] >= 1
    hanging = {g["url"]: [row(ladder.HANG, 30)] for g in games}
    monkeypatch.setattr(course, "tags", lambda moves: {u: [(1, "hanging", 30)] for u in moves})
    page = ladder.ladder(games, hanging, "me")
    assert page["current"] == 0 and ladder.focus(page)["id"] == "hang"
    assert ladder.focus(page)["train"]["route"] == "practice/" + ladder.HANG


def test_a_skill_that_is_a_lesson_shows_the_course_number(monkeypatch):
    """The same skill on Your level and Your course: one number, not two (19 Oct)."""
    from coach import course
    games = [game(f"g{i}") for i in range(4)]
    moves = {g["url"]: [row()] for g in games}
    monkeypatch.setattr(course, "tags", lambda m: {games[0]["url"]: [(1, "free", 20)]})
    skill = next(s for s in ladder.ladder(games, moves, "me")["levels"][0]["skills"] if s["id"] == "free")
    lesson = next(l for l in course.course(games, moves, "me", current="safe")["lessons"] if l["id"] == "safe-free")
    assert skill["value"] == lesson["rate"] == 0.25


def test_converting_won_games():
    games = [game("a", "win"), game("b", "resigned")]
    moves = {"a": [row(cp=400)], "b": [row(cp=500)]}
    assert ladder._conversion(games, moves, {"player": "me"}) == 50
    assert ladder._conversion(games, {"a": [row()], "b": [row()]}, {"player": "me"}) is None


def test_a_good_start_counts_pieces_out_and_castling():
    two_out = game("a")  # Nf3 and Bc4 only, then castles: not enough
    three_out = dict(game("b"), pgn=PGN.replace("5. d3 d6", "5. Nc3 d6"))  # Nf3, Bc4, Nc3 and castled
    assert ladder._development([two_out], {}, {"player": "me"}) == 0
    assert ladder._development([three_out], {}, {"player": "me"}) == 100
