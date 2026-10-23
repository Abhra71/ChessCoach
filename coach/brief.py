"""The coach's briefing before every position: where it comes from, what's going on, and the mindset to bring.

Facts only: the game from the player's archive, the material on the board, the phase, the engine's verdict
when the position was checked, the puzzle's Lichess themes. Nothing is invented.
"""
from datetime import datetime

from coach import insights

VALUE = {"p": 1, "n": 3, "b": 3, "r": 5, "q": 9, "k": 0}
NAME = {1: "a pawn", 2: "two pawns", 3: "a piece", 5: "a rook", 9: "a queen"}
MINDSET = {  # per habit: how to think in this kind of position; four ways to say it, so it doesn't repeat (23 Oct test)
    "left a piece hanging": [
        "Safety first. Before you look for attacks, check every one of your pieces: is it protected?",
        "Count your pieces like a goalkeeper: which one could they take for free?",
        "Before you move, ask: what does this move leave behind, unguarded?",
        "A quiet look first: every piece that can be taken, is it defended at least as many times as it's attacked?",
    ],
    "walked into a fork or trick": [
        "Think like your opponent. After your move, what is their nastiest reply?",
        "Look for squares where one of their pieces could hit two of yours at once.",
        "Knights love forks. Where can their knight jump next, and what would it hit?",
        "Before you move, check their checks and captures first: that's where tricks hide.",
    ],
    "missed a free capture": [
        "Be greedy. Look at every capture first: is something of theirs left unprotected?",
        "Scan their pieces one by one: is any of them attacked and not defended?",
        "Captures first. Before any plan, see if they left something hanging.",
        "Something may be free here. Count attackers and defenders on each of their pieces.",
    ],
    "walked into checkmate": [
        "King first. Which checks can they give after your move?",
        "Look at your king's escape squares. Are any left after your move?",
        "Before you move, play their best check in your head. Is it mate?",
        "Their queen and rooks near your king? Count the checks before anything else.",
    ],
    "missed a checkmate": [
        "Attack mode. Look at every check you can give: one of them may be mate.",
        "Where can their king go? If nowhere, one check finishes it.",
        "Checks first, every one of them, even the ones that look silly.",
        "Their king is short of squares. Find the check it can't escape.",
    ],
    "stalemated a won game": [
        "You're winning. Finish calmly, and always leave their king a square.",
        "Before each move, ask: does their king still have a legal move?",
        "Winning is the easy part now. Don't take away every square from their king.",
        "Slow and safe: give check or leave a square. Never freeze their king.",
    ],
}


def mindset_for(pattern, key):
    """One of the habit's tips, the same one every time for this position."""
    import zlib
    tips = MINDSET.get(pattern)
    if not tips:
        return "Checks, captures and threats, in that order. Then decide."
    return tips[zlib.crc32(str(key).encode()) % len(tips)]


GOAL = [  # Lichess puzzle themes -> what the player is looking for
    ("mate", "There is a checkmate here."),
    ("crushing", "There is a move that wins big."),
    ("advantage", "There is a move that wins material."),
    ("equality", "You are in trouble: find the move that saves you."),
]
PHASE_WORDS = {"opening": "still the opening", "middlegame": "the middlegame", "endgame": "the endgame"}


def material(pieces):
    """(white, black) in pawns."""
    w = sum(VALUE[p.lower()] for p in pieces.values() if p.isupper())
    b = sum(VALUE[p.lower()] for p in pieces.values() if p.islower())
    return w, b


def phase(pieces, move=None):
    heavy = sum(VALUE[p.lower()] for p in pieces.values() if p.lower() not in "pk")
    if heavy <= 26:
        return "endgame"
    return "opening" if move and move <= 10 else "middlegame"


def balance(diff):
    if diff == 0:
        return "Material is level."
    word = NAME.get(abs(diff)) or f"about {abs(diff)} pawns"
    return f"You are {word} {'up' if diff > 0 else 'down'}."


def verdict(chance):
    if chance is None:
        return ""
    if chance >= 75:
        return "You are winning here."
    if chance >= 58:
        return "You are a bit better."
    if chance > 42:
        return "The position is about even."
    if chance > 25:
        return "You are a bit worse, so careful."
    return "You are in trouble here."


def _games_by_url():
    return {g["url"]: g for g in insights._games()}


def brief(d, games=None):
    pieces, white = d.get("start") or {}, not d.get("flip")
    if d.get("steps") and (d.get("kind") == "puzzle" or d.get("last")):  # the board after their last move
        pieces = d["steps"][0].get("board") or pieces
    w, b = material(pieces)
    diff = (w - b) if white else (b - w)
    side = "White" if white else "Black"
    mindset = mindset_for(d.get("pattern"), d.get("id"))
    if d.get("kind") == "game":
        g = (games or {}).get(d.get("url"))
        ply = int(str(d.get("id", "")).rsplit("#", 1)[-1]) if "#" in str(d.get("id", "")) else None
        move = (ply + 1) // 2 if ply else None
        ph = phase(pieces, move)
        facts, title = [], "From your game"
        if g:
            me, them = insights._side(g, insights._player() or "")
            result = insights._result(g, me)
            title = f"Your game vs {g[them]['username']}"
            facts = [datetime.fromtimestamp(g["end_time"]).strftime("%d %b %Y"), g["time_class"].capitalize(),
                     f"You were {side}", f"You {'won' if result == 'win' else 'lost' if result == 'loss' else 'drew'} it"]
        situation = " ".join(x for x in [f"Move {move}, {PHASE_WORDS[ph]}." if move else "", balance(diff),
                                         f"Your opponent just played {d['their_move']}." if d.get("their_move") else "",
                                         verdict(d.get("chance")),
                                         f"In the game you played {d['played']} here, and it cost you. Find a better move."
                                         if d.get("played") else ""] if x)
        return {"title": title, "facts": facts[:4], "situation": situation, "mindset": mindset}
    if d.get("kind") == "puzzle" and str(d.get("id", "")).startswith("elite:"):  # a strong player's game: the plan
        return {"title": "Find the strong player's move", "facts": [f"You are {side}", "Players rated 2,400+", phase(pieces).capitalize()],
                "situation": f"{d.get('where')}. No trick here: the strong player made a quiet move that follows the "
                             f"structure's plan.", "mindset": d.get("hint")}
    if d.get("kind") == "puzzle":
        themes = d.get("themes") or []
        ph = next((t for t in ("opening", "middlegame", "endgame") if t in themes), phase(pieces))
        goal = next((text for t, text in GOAL if any(x.startswith(t) for x in themes)), "There is a strong move here.")
        last = d.get("their_move")
        situation = " ".join(x for x in [f"It's {PHASE_WORDS[ph]}.", balance(diff),
                                         f"Your opponent just played {last}." if last else "", goal] if x)
        facts = [f"Puzzle level {d['rating']}" if d.get("rating") else "Puzzle", f"You are {side}", ph.capitalize()]
        from coach import drills, plan
        theme = d.get("theme")
        if d.get("pattern"):
            title = "A puzzle on the same habit"
        elif theme in plan.THEME_NAME:
            title = f"Puzzle: {plan.THEME_NAME[theme]}"
        else:
            title = "Puzzle"
        if not d.get("pattern"):  # a lesson's puzzle: the theme's own advice
            mindset = drills.CLUE.get(theme) or "Checks, captures and threats, in that order. The first idea is often the right one."
        return {"title": title, "facts": facts, "situation": situation, "mindset": mindset}
    if d.get("kind") == "opening":
        return {"title": d.get("where") or "Your opening", "facts": [f"You are {side}", "From move 1", "Opening"],
                "situation": "Something new: an opening line to learn by heart. You play your side's moves, I answer"
                              " with theirs and explain each one. Then play it in your next games.",
                "mindset": "Develop a piece, take the centre, castle. Every move should do one of those."}
    return None


def add(drills):
    """The same drills, each with its briefing."""
    games = _games_by_url()
    for d in drills or []:
        if isinstance(d, dict) and d.get("steps"):
            d["brief"] = brief(d, games)
    return drills
