"""The feature map stays true to the app (coach/features.py, owner's rule "nothing unused", 28 Nov 2026).

Fails when: a page, a tour item, a suggestion kind or a data file isn't in the map; a feature is missing its coach,
page or story; or a new feature arrives without a right-time moment (the gap list may only shrink)."""
import re
from pathlib import Path

from coach import features, nudge

ROOT = Path(__file__).resolve().parents[1]
F = features.FEATURES


def test_every_feature_is_complete():
    ids = [f["id"] for f in F]
    assert len(ids) == len(set(ids)), "two features share an id"
    for f in F:
        assert f.get("name") and f.get("page") and f.get("story"), f"{f['id']}: name, page and story are needed"
        assert f.get("coach") in ("maya", "viktor"), f"{f['id']}: the coach is maya or viktor"


def test_every_page_belongs_to_a_feature():
    names = re.search(r"const NAMES = \{(.*?)\};", (ROOT / "coach/ui/app.js").read_text(encoding="utf-8"), re.S).group(1)
    pages = set(re.findall(r"(\w+):", names))
    mapped = {f["page"] for f in F}
    assert pages - mapped == set(), f"pages with no feature in coach/features.py: {sorted(pages - mapped)}"


def test_every_tour_item_belongs_to_a_feature():
    toured = {t[0] for t in nudge.TOUR}
    mapped = {t for f in F for t in f.get("tour", [])}
    assert toured - mapped == set(), f"tour items with no feature: {sorted(toured - mapped)}"
    assert mapped - toured == set(), f"features name tour items that don't exist: {sorted(mapped - toured)}"


def test_every_suggestion_kind_belongs_to_a_feature():
    src = (ROOT / "coach/nudge.py").read_text(encoding="utf-8")
    kinds = set(re.findall(r'\badd\("(\w+)"', src)) | set(re.findall(r'"kind": "(\w+)"', src))
    kinds.discard("tour")  # the tour itself
    kinds |= set(nudge.TOLD)  # the club's moments, added from coach/memories.py
    for kind, (where, marker) in features.SPOKEN.items():  # said in the coach's greeting: it must really be there
        assert marker in (ROOT / where).read_text(encoding="utf-8"), f"{kind} isn't in {where}"
        kinds.add(kind)
    mapped = {m for f in F for m in f.get("moments", [])}
    assert kinds - mapped == set(), f"suggestions with no feature: {sorted(kinds - mapped)}"
    assert mapped - kinds == set(), f"features name moments that don't exist: {sorted(mapped - kinds)}"


def test_every_data_file_is_used_by_something():
    found = set()
    for py in (ROOT / "coach").glob("*.py"):
        for name in re.findall(r'DATA\s*/\s*f?"([^"]+)"', py.read_text(encoding="utf-8")):
            found.add("games-*.json" if name.startswith("games-") else name)
    claimed = {d for f in F for d in f.get("data", [])} | set(features.SYSTEM_DATA)
    assert found - claimed == set(), f"data files no feature uses (connect them, or stop keeping them): {sorted(found - claimed)}"
    assert claimed - found == set(), f"the map names data files the code doesn't keep: {sorted(claimed - found)}"


def test_gaps_only_shrink():
    """A feature connected to a moment leaves the list (remove it from GAPS); a new feature must come with one."""
    now = features.gaps()
    new = sorted(set(now) - set(features.GAPS))
    assert not new, f"new features with no right-time moment (owner's rule: nothing unused): {new}"
    closed = sorted(set(features.GAPS) - set(now))
    assert not closed, f"connected now, take them off features.GAPS: {closed}"
