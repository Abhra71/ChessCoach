"""28 Nov, the owner's game against salmonetetete: "a lot of things seem to be missing". They resigned a pawn up (the
engine: +3.3) after five Best moves; the review said only "You resigned", and 5.Qe2? said only "A mistake by them"."""
import chess
import pytest

from coach import insights, narrate, nudge, rematch
from tests.test_narrate import _positions

OWNER_GAME = ["d4", "d5", "Bf4", "c5", "e3", "Nc6", "Bd3", "cxd4", "Qe2", "dxe3", "Qxe3", "f6", "Nf3", "e5"]


def test_their_punished_mistake_says_what_they_should_have_played_and_what_it_gave_you():
    pos, played = _positions(OWNER_GAME)
    rows = [{"ply": 8, "loss": 0, "best": "cxd4", "cp_after": 20, "reply_pv": ["e3d4"], "fen": pos[7]["fen"]},
            {"ply": 10, "loss": 0, "best": "dxe3", "cp_before": 200, "cp_after": 200, "fen": pos[9]["fen"]}]
    out = narrate.game(pos, played, rows, chess.BLACK, "salmonetetete")
    qe2 = out[8]["text"]
    assert "exd4 was stronger for them, and it let you play dxe3." in qe2, qe2
    assert ["e3d4", "reply", "They missed"] in out[8]["arrows"]


class FakeEngine:
    def __init__(self, cp):
        self.cp = cp

    def analyse(self, board, limit):
        return {"score": chess.engine.PovScore(chess.engine.Cp(self.cp), chess.WHITE)}


@pytest.fixture(autouse=True)
def _fresh(monkeypatch):
    monkeypatch.setattr(insights, "_END", {})


END = chess.Board("r1bqkbnr/pp4pp/2n2p2/3pp3/5B2/3BQN2/PPP2PPP/RN2K2R w KQkq - 0 8")  # the owner's real last position


def test_resigned_while_ahead_is_said_with_numbers_and_can_be_played_on():
    e = insights.the_end("1", END, False, "loss", "resigned", 15, engine=FakeEngine(-333))  # -3.3 for White = +3.3 for you
    assert e["say"] == "You resigned while ahead: the engine gives you +3.3, worth about a piece. It wasn't lost."
    assert e["play_on"] == {"ply": 15}


def test_even_behind_won_or_not_given_up():
    assert "still about even (+0.4)" in insights.the_end("2", END, False, "loss", "timeout", 15, engine=FakeEngine(-40))["say"]
    behind = insights.the_end("3", END, False, "loss", "resigned", 15, engine=FakeEngine(500))
    assert behind["say"] is None and behind["play_on"] is None  # really lost: the plain ending stays
    assert insights.the_end("4", END, False, "win", "resigned", 15, engine=FakeEngine(-333)) is None
    assert insights.the_end("5", END, False, "loss", "checkmated", 15, engine=FakeEngine(-333)) is None


def test_play_on_their_move_first_then_yours(monkeypatch):
    pos, _ = _positions(OWNER_GAME)
    g = {"id": "9", "color": "black", "positions": pos, "opponent": "salmonetetete", "opponent_rating": 453,
         "result": "loss", "the_end": {"say": "You resigned while ahead.", "play_on": {"ply": len(pos)}}}
    monkeypatch.setattr(rematch, "_human", lambda rating: False)
    monkeypatch.setattr(rematch, "pick", lambda board, rating, rng=None: board.parse_san("Bg3"))
    s = rematch.play_on(g)
    assert s["first_reply"] == "Bg3" and s["play_on"] and s["real_move"] is None
    assert s["legal"] and chess.Board(s["fen"]).turn == chess.BLACK  # your move now
    assert s["move_number"] == 8 and s["lead_in"][-1] == s["fen"]


def test_maya_brings_it_up_after_the_game(tmp_path, monkeypatch):
    monkeypatch.setattr(nudge, "FILE", tmp_path / "nudges.json")
    import time
    home = {"games": 10, "daily": {"done_today": True},
            "last_game": {"id": "9", "opponent": "salmonetetete", "checked": True, "result": "loss", "moments": 0,
                          "end_time": time.time() - 600}}
    c = [x for x in nudge.candidates("app", home, rematch={"ply": 15, "play_on": True,
                                                            "say": "You resigned while ahead."}) if x["kind"] == "rematch"]
    assert c and c[0]["line"].startswith("Your game against salmonetetete: You resigned while ahead. Play it on")
    assert c[0]["route"] == "rematch/9/15"
