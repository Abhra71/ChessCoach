"""Your plan: each card's road (where it is, what's next) and the Done row (23 Oct test)."""
from coach import plan


def test_path_walks_on_and_rounds_again():
    ids = ["tactic:fork", "tactic:pin", "tactic:skewer"]
    assert plan._path(ids, set()) == {"now": "tactic:fork", "at": 1, "of": 3, "more": 2, "next": "The pin"}
    assert plan._path(ids, {"tactic:fork"})["now"] == "tactic:pin"
    assert plan._path(ids, {"tactic:fork"})["at"] == 2
    every = plan._path(ids, set(ids))
    assert every["now"] == "tactic:fork" and every["at"] == 3 and every["next"] is None


def test_done_items_have_names():
    assert plan.done_item("endgame:pawnEndgame")["title"] == "Pawn endings"
    assert plan.done_item("idea:cct")["title"] == "Checks, captures, threats"
    assert plan.done_item("opening:C47:Four Knights Game", {"openings": {}})["title"] == "Four Knights Game (as White)"
    assert plan.done_item("nonsense") is None
