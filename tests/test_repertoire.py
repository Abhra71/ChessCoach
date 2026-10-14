from coach import repertoire

E4 = '[Event "x"]\n\n1. e4 e5 2. Nf3 Nc6 1-0'
D4 = '[Event "x"]\n\n1. d4 d5 2. c4 1-0'


def game(me_white, pgn, result="win"):
    me, them = {"username": "me", "result": result}, {"username": "them", "result": "checkmated"}
    return {"white": me if me_white else them, "black": them if me_white else me, "pgn": pgn}


class Engine:  # every line looks sound: the choice is about what you play
    def analyse(self, board, limit):
        import chess.engine
        return {"score": chess.engine.PovScore(chess.engine.Cp(0), True)}


def test_your_first_move_as_white_counts_all_its_games(tmp_path, monkeypatch):
    monkeypatch.setattr(repertoire, "FILE", tmp_path / "r.json")
    monkeypatch.setattr(repertoire.openings, "EVALS", tmp_path / "e.json")
    monkeypatch.setattr(repertoire.insights, "home", lambda: {"focus": {"pattern": repertoire.plan.HANG}})
    games = [game(True, E4) for _ in range(5)] + [game(True, D4)]
    lines = repertoire.build(Engine(), games=games, player="me")
    white = next(l for l in lines if l["side"] == "white")
    assert white["steps"][0]["san"] == "e4" and white["style"] != "sharp"
    assert repertoire.build(Engine(), games=[], player="me") == lines  # kept until asked for new ones
