"""The feature map (step 1 of docs/CONNECTIONS.md, 28 Nov 2026): every feature Knightwise has, in one place.

Owner's rule: players come to *view*; the coaches must bring every feature to them at the right time, and nothing
may sit unused. So each feature lists:
  page     where it lives in the app (a route, as in "#/route")
  coach    who brings it ("maya" or "viktor")
  story    its reason in the storyline (docs/STORYLINE.md)
  tour     its introductions in the coaches' tour (coach/nudge.py TOUR ids)
  moments  the suggestions that bring it up from the player's own data (coach/nudge.py kinds)
  data     the files in data/ it reads or writes
  always   True for the few things that are always in front of the player (Home, the ask box, Settings)

A feature with no moment and not always in view is a GAP: it's only ever shown once, by the tour. GAPS lists them
(empty since step 3.2, 28 Nov); tests/test_features.py makes sure the list can only shrink, and that every new feature, page, suggestion and
data file is mapped here. coach/nudge.py reads it to know whose voice a suggestion is in.
"""

FEATURES = [
    # the clubhouse
    {"id": "home", "name": "Home", "page": "home", "coach": "maya", "always": True,
     "moments": ["memory", "story", "history"],  # the coaches' memories, the club's moments, on this day (3.3, 3.5)
     "story": "The clubhouse: the coaches greet you and show your week",
     "data": ["player.txt", "patterns.json", "games-*.json"]},
    {"id": "ask", "name": "Ask the coach (typed or out loud)", "page": "home", "coach": "maya", "always": True,
     "tour": ["ask", "talk"],
     "story": "Like asking your coach after a lesson",
     "data": ["ai-usage.json", "explanations.json", "heard.jsonl", "heard-words.json"]},
    {"id": "extension", "name": "The coach on chess.com", "page": "settings", "coach": "maya",
     "tour": ["extension"], "moments": ["chesscom", "bots"],
     "story": "Maya sits beside you where you play (never during a live game)"},
    # your games
    {"id": "games", "name": "Game review and key moments", "page": "games", "coach": "maya", "moments": ["game"],
     "story": "Viktor lost half his games by not writing them down: every game kept, every lesson kept",
     "data": ["games-*.json", "moves.jsonl", "checked.txt", "review.html"]},
    {"id": "rematch", "name": "Rematch from the move it went wrong", "page": "rematch", "coach": "maya",
     "moments": ["rematch"],
     "story": "Viktor's wish to play his last round again; the player's chance",
     "data": ["moves.jsonl"]},
    # training ground
    {"id": "daily", "name": "Today's 5 minutes", "page": "daily", "coach": "maya", "moments": ["daily"],
     "story": "Maya's morning routine as a junior: five minutes, every day",
     "data": ["daily.json", "today-sets.json", "kept-sets.json"]},
    {"id": "practice", "name": "Practice from your own positions", "page": "practice", "coach": "maya",
     "tour": ["practice"], "moments": ["practice"],  # positions due again today (step 3.2)
     "story": "Maya's coach made her replay her own mistakes until they stuck",
     "data": ["drills.json", "drill-cache.json", "drills.html", "practice.jsonl", "verdicts.jsonl", "puzzles.json"]},
    {"id": "clock", "name": "Slow down (the clock drill)", "page": "clockdrill", "coach": "maya", "moments": ["clock"],
     "story": "Maya lost a winning junior final on time"},
    # Viktor's rooms
    {"id": "plan", "name": "Your plan (cards, Explore, Done)", "page": "plan", "coach": "viktor",
     "tour": ["plan", "explore", "done"], "moments": ["novelty"],  # Home: "Something new for you" (features.SPOKEN)
     "story": "Viktor picks what matters for you now, from thousands of positions",
     "data": ["novelty.json"]},
    {"id": "course", "name": "Your course", "page": "course", "coach": "viktor", "tour": ["course"],
     "moments": ["lesson"],
     "story": "Viktor's thirty years of lessons, in order",
     "data": ["course.json"]},
    {"id": "level", "name": "Your level (the ranks)", "page": "level", "coach": "viktor", "tour": ["level"],
     "moments": ["rank"],  # a new rank (step 3.1, 28 Nov)
     "story": "Your membership rank in the club; each rank opens a page of Viktor's notebook",
     "data": ["story.json"]},
    {"id": "progress", "name": "Progress and badges", "page": "progress", "coach": "viktor", "tour": ["progress"],
     "moments": ["badge", "week"],
     "story": "Your record as a member",
     "data": ["badges-golds.json"]},
    {"id": "report", "name": "Weekly report", "page": "report", "coach": "viktor", "tour": ["report"], "moments": ["report"],  # Sunday, after a week with games
     "story": "Viktor's short letter about your week"},
    {"id": "film", "name": "Game of the month (film)", "page": "progress", "coach": "maya", "tour": ["film"], "moments": ["film"],  # the month's best win, on the 1st
     "story": "Maya: this one deserves to be watched"},
    {"id": "wrapped", "name": "Your month as Wrapped", "page": "report", "coach": "maya", "tour": ["wrapped"], "moments": ["wrapped"],  # the 1st, after a month with games
     "story": "Viktor's monthly letter, told as cards"},
    # the practice hall (Train)
    {"id": "train", "name": "Train (the practice hall)", "page": "train", "coach": "viktor", "always": True,
     "story": "Viktor's drills, all in one hall"},
    {"id": "openings", "name": "Opening tree", "page": "openings", "coach": "viktor", "tour": ["openings"],
     "moments": ["opening"],
     "story": "Know why each move is there, not just the moves (Maya's lesson)",
     "data": ["opening-evals.json"]},
    {"id": "repertoire", "name": "Repertoire", "page": "repertoire", "coach": "viktor", "tour": ["repertoire"],
     "moments": ["repertoire"],
     "story": "Maya's memorising-vs-understanding lesson; lines you know by heart and by reason",
     "data": ["repertoire.json", "repertoire-check.json"]},
    {"id": "calc", "name": "In your head (calculation)", "page": "calc", "coach": "viktor", "tour": ["calc"],
     "moments": ["calc"],
     "story": "Viktor's regret: the move he didn't check"},
    {"id": "endgames", "name": "Endgames", "page": "endgames", "coach": "viktor", "tour": ["endgames"],
     "moments": ["endgame"],
     "story": "Most games are decided after the queens are gone (Viktor's school motto)",
     "data": ["endgames.json"]},
    {"id": "blindfold", "name": "Blindfold", "page": "blindfold", "coach": "viktor", "tour": ["blindfold"], "moments": ["blindfold"],  # reaching Club player
     "story": "Viktor's boyhood training in Berlin: whole games in his head",
     "data": ["blindfold.json"]},
    {"id": "guess", "name": "Guess the move", "page": "guess", "coach": "viktor", "tour": ["guess"], "moments": ["guess"],  # walking into what they planned, again and again
     "story": "Think like them for five minutes (Maya)",
     "data": ["guess.json"]},
    {"id": "prep", "name": "Prep, Punish and Spar", "page": "prep", "coach": "viktor",
     "tour": ["prep", "punish", "spar"], "moments": ["prep"],
     "story": "Viktor's chess-school habit: study the opponent the night before",
     "data": ["preps.json"]},
    # the club (storyline 3.4 and 3.6, 28 Nov)
    {"id": "words", "name": "Chess words (tap to explain, and the list)", "page": "words", "coach": "viktor",
     "tour": ["words"], "moments": ["words"],
     "story": "The library's dictionary: the words strong players use, in plain language",
     "data": ["words.json"]},
    {"id": "coaches", "name": "Meet your coaches", "page": "coaches", "coach": "maya", "tour": ["coaches"],
     "moments": ["meet"],
     "story": "Maya from Chennai and Viktor from Berlin: who they are and why they coach"},
    # always there
    {"id": "settings", "name": "Settings", "page": "settings", "coach": "maya", "always": True,
     "story": "Your locker in the club",
     "data": ["settings.json"]},
]

# Moments the coach says in her own greeting (coach/coaches.py speak) rather than as a suggestion (coach/nudge.py):
# kind -> where. "novelty": Home's "Something new for you: ...", when coach/plan.py picks a new card for a fresh
# weakness in the player's games (found by the step 3.2 audit, 28 Nov: it was there, the map had missed it).
SPOKEN = {"novelty": "coach/coaches.py"}

# Data the app keeps for itself, not for one feature (the machinery): never shown to the player directly.
SYSTEM_DATA = ["service.pid", "health.json", "fixes.json", "update-try.json", "voice-cache", "said.json",
               "nudges.json", "feedback.jsonl", "feedback-sent.json"]

# Features with no right-time moment today: only the tour ever brings them up. To be connected (STORYLINE.md 3b);
# tests/test_features.py lets this list shrink, never grow.
GAPS = []  # all connected (step 3.2, 28 Nov)


ROUTE_ALIASES = {"endgame": "endgames", "clockdrill": "clockdrill", "plan/explore": "plan", "plan/done": "plan",
                 "punish": "prep", "spar": "prep", "film": "progress"}


def feature_of(route=None, kind=None, tour=None):
    """Which feature a page, a suggestion kind or a tour item belongs to (None if it's none of ours)."""
    for f in FEATURES:
        if kind and kind in f.get("moments", []):
            return f["id"]
        if tour and tour in f.get("tour", []):
            return f["id"]
    if route:
        top = str(route).strip("/").split("/")[0].split("@")[0]
        top = ROUTE_ALIASES.get(top, top)
        if top == "report":
            return "wrapped" if "/month" in str(route) else "report"
        own = ([f for f in FEATURES if f["id"] == top] or [f for f in FEATURES if f["page"] == top and not f.get("always")]
               or [f for f in FEATURES if f["page"] == top])
        return own[0]["id"] if own else None
    return None


def gaps():
    """Features only the tour ever brings up (no moment from the player's data, not always in view)."""
    return [f["id"] for f in FEATURES if not f.get("moments") and not f.get("always")]


def coverage():
    """In numbers, for the weekly memo later: how many features, how many connected, which aren't."""
    g = gaps()
    return {"features": len(FEATURES), "connected": len(FEATURES) - len(g), "gaps": g}
