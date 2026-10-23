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


def test_whose_opening_from_its_name():
    assert plan.default_side("Sicilian Defense: Open") == "black"
    assert plan.default_side("Queen's Gambit Declined") == "black"
    assert plan.default_side("Italian Game: Two Knights Defense") == "white"
    assert plan.default_side("London System") == "white"


def test_search_matches_word_starts(monkeypatch):
    monkeypatch.setattr(plan, "_catalogue", lambda: [("A00", "Polish Opening", ["b4"] * 2),
                                                     ("B27", "Sicilian Defense", ["e4", "c5"]),
                                                     ("C00", "Alekhine Defense: Brooklyn Variation", ["e4", "Nf6", "e5", "Ng8"])])
    monkeypatch.setattr(plan, "_library_themes", lambda: {"rookEndgame", "fork"})
    assert [x["title"] for x in plan.search("rook")] == ["Rook endings"]  # not Brooklyn
    assert plan.search("sicil")[0] == {"id": "opening:B27:Sicilian Defense", "kind": "opening",
                                       "title": "Sicilian Defense", "side": "black", "moves": 2}
    assert plan.search("fork")[0]["id"] == "tactic:fork"
    assert plan.search("   ") == []


def _item(i, n=4):
    return {"id": i, "kind": "tactic", "title": i, "drills": [{"id": f"{i}-{k}", "steps": []} for k in range(n)]}


def test_started_goes_to_in_progress_then_done(tmp_path, monkeypatch):
    monkeypatch.setattr(plan, "MEMORY", tmp_path / "novelty.json")
    plan.progress("tactic:skewer", _item("tactic:skewer"), [None, None, None, None])
    assert plan.in_progress() == {}  # opened, nothing answered: not started
    plan.progress("tactic:skewer", _item("tactic:skewer"), ["right", None, None, None])
    started = plan.in_progress()
    assert list(started) == ["tactic:skewer"] and started["tactic:skewer"]["state"] == ["right", None, None, None]
    assert len(started["tactic:skewer"]["drills"]) == 4  # its own positions, to carry on with
    plan.progress("tactic:skewer", None, ["right", "missed", None, None])  # later answers need no item
    assert plan.in_progress()["tactic:skewer"]["state"][1] == "missed"
    plan.mark("tactic:skewer", done=True)
    assert plan.in_progress() == {} and "tactic:skewer" in plan._memory()["done"]


def test_done_played_again_stays_done(tmp_path, monkeypatch):
    monkeypatch.setattr(plan, "MEMORY", tmp_path / "novelty.json")
    plan.mark("endgame:rookEndgame", done=True)
    plan.progress("endgame:rookEndgame", _item("endgame:rookEndgame"), ["right", None, None, None])
    assert plan.in_progress() == {}


def test_in_progress_keeps_the_newest(tmp_path, monkeypatch):
    import datetime
    monkeypatch.setattr(plan, "MEMORY", tmp_path / "novelty.json")
    for n in range(plan.IN_PROGRESS_MAX + 3):
        plan.progress(f"tactic:t{n}", _item(f"tactic:t{n}"), ["right"], today=datetime.date(2026, 1, 1) + datetime.timedelta(days=n))
    kept = plan.in_progress()
    assert len(kept) == plan.IN_PROGRESS_MAX and "tactic:t0" not in kept and next(iter(kept)) == f"tactic:t{plan.IN_PROGRESS_MAX + 2}"
