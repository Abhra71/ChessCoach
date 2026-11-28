"""Nothing unused (owner, 28 Nov 2026): every page of the app must be reachable through the coaches, so no feature is
ever left for players to stumble on by themselves. A new page that isn't in the tour (coach/nudge.py TOUR) or the
side menu fails here, as a reminder to connect it."""
import re
from pathlib import Path

from coach import nudge

UI = Path(__file__).resolve().parents[1] / "coach" / "ui" / "app.js"
MENU = {"home", "games", "practice", "train", "plan", "course", "level", "progress", "settings",  # the side menu
        "daily"}  # Today's 5 minutes: the first card on Home, and Maya brings it up every day (nudge.DAILY)


def pages():
    names = re.search(r"const NAMES = \{(.*?)\};", UI.read_text(encoding="utf-8"), re.S).group(1)
    return set(re.findall(r"(\w+):", names))


def test_every_page_has_a_way_in_from_the_coaches():
    toured = {t[2].split("@")[0].split("/")[0] for t in nudge.TOUR}
    hidden = pages() - MENU
    assert hidden, "the page list in app.js wasn't found"
    left_out = sorted(hidden - toured)
    assert not left_out, f"pages no coach ever points to (add them to nudge.TOUR and a right-time moment): {left_out}"
