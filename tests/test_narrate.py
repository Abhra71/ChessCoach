"""The whole-game review: one short line a move, from the rules and the engine, no AI (22 Oct)."""
import chess

from coach import narrate, talk


def _positions(sans):
    b = chess.Board()
    pos, played = [{"fen": b.fen()}], []
    for s in sans:
        m = b.parse_san(s); played.append(m); b.push(m); pos.append({"fen": b.fen()})
    return pos, played


def test_who_moved_what_from_where():
    pos, played = _positions(["e4", "e5", "Nf3", "Nc6", "Bc4", "Nd4", "Nxe5"])
    out = narrate.game(pos, played, [], chess.WHITE, "rival")
    assert out[0]["text"].startswith("You moved your pawn from e2 to e4.")
    assert out[1]["text"].startswith("rival moved their pawn from e7 to e5.")  # the opponent's name, the first time
    assert out[3]["text"].startswith("They moved their knight from b8 to c6.")
    assert "took their pawn on e5 with your knight" in out[6]["text"]


def test_engine_verdict_and_better_move_for_your_moves():
    pos, played = _positions(["e4", "e5", "Qh5"])
    rows = [{"ply": 3, "loss": 25, "best": "Nf3", "fen": pos[2]["fen"]}]
    out = narrate.game(pos, played, rows, chess.WHITE, "rival")
    assert "A blunder: Nf3 was much better." in out[2]["text"] and out[2]["kind"] == "bad"
    assert out[2]["label"] == "Blunder" and out[2]["sign"] == "??"
    assert ["g1f3", "better"] in out[2]["arrows"]


def test_book_moves_and_the_opening_by_name():
    pos, played = _positions(["e4", "e5", "Nf3", "Nf6"])
    rows = [{"ply": 2, "loss": 1, "best": "e5"}, {"ply": 4, "loss": 1, "best": "Nc6"}]
    out = narrate.game(pos, played, rows, chess.BLACK, "rival")
    assert [m["label"] for m in out] == ["Book"] * 4
    assert "This is the Petrov's Defense." in out[3]["text"]


def test_checkmate_is_said():
    pos, played = _positions(["f3", "e5", "g4", "Qh4#"])
    assert narrate.game(pos, played, [], chess.WHITE, "rival")[-1]["text"].endswith("Checkmate.")


def test_back_by_voice_only_in_a_review():
    assert talk.action({"do": "back"}, [], {"section": "review"}) == {"back": True}
    assert talk.action({"do": "back"}, [], {"section": "home"}) is None
