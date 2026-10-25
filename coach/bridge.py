"""After a game review, the link to training (25 Oct, owner: "the coach is the brain, every part of the app a nerve").
A player who only opens reviews still gets pointed somewhere specific: this game's mistake, how often it happens in
their last games, and the exact place in Knightwise that trains it, with one button. Plain code, no AI."""
from collections import Counter

from coach import insights
from coach.paths import DATA

HANG, FORK, FREE = "left a piece hanging", "walked into a fork or trick", "missed a free capture"
STALEMATE, MATED, MISSED_MATE = "stalemated a won game", "walked into checkmate", "missed a checkmate"
RECENT = 20  # games looked at for "how often"

# where each mistake is trained when Practice has none of your own positions on it: (route, button, where in words)
# one sentence in all, so the coach's bubble shows it whole (it shows two sentences before More)
LESSON = {HANG: ("course/safe-hanging", "Open the lesson", "the lesson Keep every piece safe, in Your course, trains it"),
          FORK: ("course/tac-fork", "Open the lesson", "the lesson Forks, in Your course, trains it"),
          FREE: ("course/safe-free", "Open the lesson", "the lesson Take what they leave you, in Your course, trains it"),
          MATED: ("course/safe-checks", "Open the lesson", "the lesson Look at their checks, in Your course, trains it"),
          MISSED_MATE: ("course/safe-mate1", "Open the lesson", "the lesson Finish them: checkmate in one, in Your course, trains it"),
          STALEMATE: ("endgame/queen", "Play it", "Mate with king and queen, in Train under Endgames, trains finishing them")}


def _times(n):
    return "once" if n == 1 else "twice" if n == 2 else f"{n} times"


def _own_positions(pattern):
    """How many of your own positions on this mistake Practice has today."""
    import json
    try:
        return sum(1 for d in json.loads((DATA / "drills.json").read_text())
                   if d.get("kind") == "game" and d.get("pattern") == pattern)
    except (OSError, ValueError):
        return 0


def for_game(gid, games=None, moves=None):
    """{line, route, label} for the end of this game's review, or None (a clean game, or nothing to link)."""
    games = games if games is not None else insights._games()
    moves = moves if moves is not None else insights._moves()
    g = next((x for x in games if insights.game_id(x["url"]) == str(gid)), None)
    if not g:
        return None
    here = Counter(r["pattern"] for r in moves.get(g["url"], []) if r.get("pattern") in LESSON)
    if not here:
        return None
    recent = sorted(games, key=lambda x: x.get("end_time") or 0)[-RECENT:]
    often = Counter(r["pattern"] for x in recent for r in moves.get(x["url"], []) if r.get("pattern") in LESSON)
    pattern = max(here, key=lambda p: (often[p], here[p]))  # the one that happens most, of this game's
    line = f"You {pattern} {_times(here[pattern])} in this game"
    if often[pattern] > here[pattern]:
        line += f" and {_times(often[pattern])} in your last {len(recent)} games"
    own = _own_positions(pattern) if pattern in (HANG, FORK, FREE) else 0
    if own:
        return {"line": f"{line}: Practice has {own} of your own positions on it.", "route": f"practice/{pattern}",
                "label": "Practise it"}
    route, label, where = LESSON[pattern]
    return {"line": f"{line}: {where}.", "route": route, "label": label}
