"""50 badges, and the completed-badge pop-up: history counts quietly, a new Gold pops up once (23 Oct)."""
from coach import progress


def test_fifty_badges_with_three_levels_each_and_unique_ids():
    assert len(progress.BADGES) == 50
    assert len({b[1] for b in progress.BADGES}) == 50
    assert all(len(b[6]) == 3 and b[6][0] < b[6][1] < b[6][2] for b in progress.BADGES)


def test_history_is_quiet_and_a_new_gold_pops_up_once(tmp_path, monkeypatch):
    monkeypatch.setattr(progress, "_golds_file", lambda: tmp_path / "golds.json")
    gold = lambda bid: {"id": bid, "name": bid, "icon": "medal", "group": "Results", "what": "x", "tier": 3, "tiers": [1, 2, 3]}
    held = [gold("wins"), {**gold("mates"), "tier": 2}]
    monkeypatch.setattr(progress, "page", lambda: {"badges": held})
    progress._LAST.update(at=0.0, badges=None)
    assert progress.new_gold(now=1000) is None  # first look: what you already hold is history, no pop-up
    held.append(gold("comeback"))
    progress._LAST.update(at=0.0, badges=None)
    b = progress.new_gold(now=2000)
    assert b["id"] == "comeback" and b["from"] == "your real chess.com games" and b["gold"] == 3
    progress.gold_shown("comeback")
    assert progress.new_gold(now=2001) is None  # once, in one place only
