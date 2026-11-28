"""The Knightwise Club's story (step 3 of docs/LEARNING-STATION.md; docs/STORYLINE.md). No AI: written once, shipped.

3.1 (28 Nov 2026): the five levels of Your level are the club's ranks, and each rank opens a page of Viktor's
notebook: a short, true story from chess history in his voice, with its source. Pages not reached yet are still
scorched (Viktor's notebook was damaged in a fire; finishing a rank restores its page: STORYLINE.md section 11).
When the player reaches a new rank, Viktor brings it up himself (coach/nudge.py, kind "rank").
"""
import json

from coach.paths import DATA

FILE = DATA / "story.json"  # which rank the player has reached, and which they have already been told about

# the ladder's level ids (coach/ladder.py) -> the club's rank (owner, 28 Nov: "rank names okay")
RANKS = {"safe": "New member", "tactics": "Club player", "club": "Team player", "precise": "First board",
         "expert": "Club master"}
ORDER = list(RANKS)

# One page per rank, in Viktor's voice. Every fact is well documented; the source is shown with the page.
NOTEBOOK = {
    "safe": {"title": "The greats keep it simple",
             "text": "José Raúl Capablanca was world champion from 1921 to 1927, and famous for clear, simple chess. "
                     "He rarely left a piece where it could be taken. Before you attack, make sure everything you own "
                     "is safe. Every club player starts there.",
             "source": "https://en.wikipedia.org/wiki/Jos%C3%A9_Ra%C3%BAl_Capablanca"},
    "tactics": {"title": "The Opera Game",
                "text": "Paris, 1858. Paul Morphy played a game at the opera against the Duke of Brunswick and Count "
                        "Isouard, and it is still taught today. Bring your pieces out fast, open the lines, and the "
                        "tactics come by themselves.",
                "source": "https://en.wikipedia.org/wiki/Opera_Game"},
    "club": {"title": "The magician from Riga",
             "text": "Mikhail Tal became world champion in 1960 with sacrifices nobody else dared to play. He saw "
                     "further than his opponents. Fewer mistakes doesn't mean fewer risks: it means checking them "
                     "before you take them.",
             "source": "https://en.wikipedia.org/wiki/Mikhail_Tal"},
    "precise": {"title": "The Berlin Wall",
                "text": "London, 2000. Vladimir Kramnik took the world title from Garry Kasparov without losing a "
                        "single game, with a quiet defence everyone now calls the Berlin Wall. Precision is choosing "
                        "the move that leaves your opponent nothing.",
                "source": "https://en.wikipedia.org/wiki/Classical_World_Chess_Championship_2000"},
    "expert": {"title": "The machine and the man",
               "text": "May 1997. IBM's computer Deep Blue beat Kasparov in a six-game match. A year later Kasparov "
                       "answered with a new idea: a person and an engine playing together, as one team. The best "
                       "player in the room is the one who keeps learning.",
               "source": "https://en.wikipedia.org/wiki/Deep_Blue_versus_Garry_Kasparov"},
}


def _load():
    try:
        return json.loads(FILE.read_text())
    except (OSError, ValueError):
        return {}


def _save(m):
    try:
        FILE.parent.mkdir(parents=True, exist_ok=True)
        FILE.write_text(json.dumps(m))
    except OSError:
        pass


def note_level(current):
    """The ladder's current level after a check. The first time it's only remembered (no fanfare for where a player
    already stands); a higher level later is a rank-up Viktor will bring up."""
    if not isinstance(current, int) or not 0 <= current < len(ORDER):
        return
    m = _load()
    if "reached" not in m:
        m["reached"], m["told"] = current, current
    elif current > m["reached"]:
        m["reached"] = current
    _save(m)


def pending_rank():
    """A rank reached but not yet celebrated: {"id", "rank", "page"} or None."""
    m = _load()
    reached, told = m.get("reached"), m.get("told")
    if reached is None or told is None or reached <= told:
        return None
    lid = ORDER[reached]
    return {"id": lid, "rank": RANKS[lid], "page": NOTEBOOK[lid]["title"]}


def told_rank():
    """The player opened Your level: the new rank has been seen."""
    m = _load()
    if m.get("reached") is not None and m.get("told") != m["reached"]:
        m["told"] = m["reached"]
        _save(m)


def notebook(current):
    """Viktor's notebook for the level page: every page, restored up to the player's rank, scorched beyond it."""
    current = current if isinstance(current, int) else 0
    return [{"id": lid, "rank": RANKS[lid], **({**NOTEBOOK[lid], "open": True} if i <= current else
                                               {"title": None, "text": None, "source": None, "open": False})}
            for i, lid in enumerate(ORDER)]
