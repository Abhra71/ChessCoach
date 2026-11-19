"""50 badges, and the completed-badge pop-up: history is celebrated once, together (19 Nov); a new Gold pops up once."""
from coach import progress


def test_fifty_badges_with_three_levels_each_and_unique_ids():
    assert len(progress.BADGES) == 51  # 51st: Homework done (24 Oct)
    assert len({b[1] for b in progress.BADGES}) == 51
    assert all(len(b[6]) == 3 and b[6][0] < b[6][1] < b[6][2] for b in progress.BADGES)


def test_history_is_quiet_and_a_new_gold_pops_up_once(tmp_path, monkeypatch):
    monkeypatch.setattr(progress, "_golds_file", lambda: tmp_path / "golds.json")
    gold = lambda bid: {"id": bid, "name": bid, "icon": "medal", "group": "Results", "what": "x", "tier": 3, "tiers": [1, 2, 3]}
    held = [gold("wins"), {**gold("mates"), "tier": 2}]
    monkeypatch.setattr(progress, "page", lambda: {"badges": held})
    progress._LAST.update(at=0.0, badges=None)
    h = progress.new_gold(now=1000)  # first look: what you already hold, celebrated once, together (19 Nov)
    assert h["id"] == "history" and h["name"] == "You already hold 1 Gold badge" and h["line"].startswith("wins, ")
    progress._LAST.update(at=0.0, badges=None)
    assert progress.new_gold(now=1500) is None  # and never again
    held.append(gold("comeback"))
    progress._LAST.update(at=0.0, badges=None)
    b = progress.new_gold(now=2000)
    assert b["id"] == "comeback" and b["from"] == "your real chess.com games" and b["gold"] == 3
    progress.gold_shown("comeback")
    assert progress.new_gold(now=2001) is None  # once, in one place only


def test_no_baseline_while_the_games_are_still_being_checked(tmp_path, monkeypatch):
    monkeypatch.setattr(progress, "_golds_file", lambda: tmp_path / "golds.json")
    gold = lambda bid: {"id": bid, "name": bid, "icon": "medal", "group": "Results", "what": "x", "tier": 3, "tiers": [1, 2, 3]}
    held = []
    monkeypatch.setattr(progress, "page", lambda: {"badges": held})
    progress._LAST.update(at=0.0, badges=None)
    assert progress.new_gold(now=1000, ready=False) is None and not (tmp_path / "golds.json").exists()
    held.extend([gold("wins"), gold("mates")])  # the first check finishes: history found
    progress._LAST.update(at=0.0, badges=None)
    # history: one welcome for both, never one pop-up each (cloud review: it all popped up)
    assert progress.new_gold(now=2000, ready=True)["name"] == "You already hold 2 Gold badges"
    progress._LAST.update(at=0.0, badges=None)
    assert progress.new_gold(now=3000, ready=True) is None



def test_a_player_updating_from_1_0_gets_the_history_welcome_once(tmp_path, monkeypatch):
    """1.0 recorded history quietly and never celebrated it: after the update, once (the owner, 19 Nov)."""
    import json
    f = tmp_path / "golds.json"
    f.write_text(json.dumps({"shown": ["wins", "mates", "comeback", "streak"]}))  # 1.0's file: no "history"
    monkeypatch.setattr(progress, "_golds_file", lambda: f)
    gold = lambda bid: {"id": bid, "name": bid.title(), "icon": "medal", "group": "Results", "what": "x", "tier": 3, "tiers": [1, 2, 3]}
    monkeypatch.setattr(progress, "page", lambda: {"badges": [gold(x) for x in ("wins", "mates", "comeback", "streak")]})
    progress._LAST.update(at=0.0, badges=None)
    h = progress.new_gold(now=1000)
    assert h["name"] == "You already hold 4 Gold badges" and h["line"].startswith("Wins, Mates, Comeback and 1 more")
    progress._LAST.update(at=0.0, badges=None)
    assert progress.new_gold(now=2000) is None
