"""Your repertoire (0.8): three opening lines to know by heart, chosen from what you already play.

As White: your usual first move, against the answer you meet most. As Black: your answer to 1.e4, and to 1.d4.
Where your own choice scores half or better it stays (you already know it); where it doesn't, a sound main line
from the Lichess opening catalogue (CC0) that starts the same way, checked by Stockfish. Solid lines first for a
player whose main habit is losing material. Once chosen, a line stays until you ask for a new one, and you practise
it on the board like the rest of your practice: each line comes back until you know it.
"""
import json

from coach import insights, openings, plan
from coach.paths import DATA

FILE = DATA / "repertoire.json"
SLOTS = [("white", None), ("black", "e4"), ("black", "d4")]


def _pick(seen, side, first, loose, engine):
    """One sound catalogue line for this slot, or None."""
    if side == "white":
        firsts = {}
        for (s, a, _), (wins, played) in seen.items():  # your first moves as White, games added up
            if s == "white":
                firsts[a] = firsts.get(a, 0) + played
        mine = max(firsts, key=firsts.get, default="e4")
        replies = {k[2]: v for k, v in seen.items() if k[0] == "white" and k[1] == mine and k[2]}
        reply = max(replies, key=lambda m: replies[m][1], default=None)
        fits = lambda sans: sans[0] == mine and (reply is None or (len(sans) > 1 and sans[1] == reply))
        own = None
    else:
        answers = {k[2]: v for k, v in seen.items() if k[0] == "black" and k[1] == first and k[2]}
        own = max(answers, key=lambda m: answers[m][1], default=None)
        keep = own and answers[own][1] >= 3 and answers[own][0] / answers[own][1] >= 0.5
        if keep:  # your own answer works: a sound line with it, or else the best sound answer of all
            line = _choose(lambda sans: sans[0] == first and len(sans) > 1 and sans[1] == own, side, loose, engine, first, own)
            if line:
                return line
        fits = lambda sans: sans[0] == first and len(sans) > 1
        own = None
    return _choose(fits, side, loose, engine, first, own)


def _choose(fits, side, loose, engine, first, own):
    options = [(eco, name, sans) for eco, name, sans in openings.catalogue()
               if 5 <= len(sans) <= 12 and fits(sans) and name.count(":") <= 1 and "," not in name]
    if any(openings.style(o[1]) != "sharp" for o in options):  # gambits and sharp lines only when nothing else fits
        options = [o for o in options if openings.style(o[1]) != "sharp"]
    options.sort(key=lambda o: (openings._rank(o[1], loose, side), -len(o[2])))
    for eco, name, sans in options[:25]:
        lesson = openings.teach(sans, side)
        if openings._eval(lesson["fen"], side, engine) >= -60:
            return {"id": f"rep:{eco}:{name}", "kind": "opening", "name": name, "eco": eco, "side": side,
                    "against": first or (sans[1] if len(sans) > 1 else None), "style": openings.style(name),
                    "kept": bool(own and fits([first, own])), **lesson}
    return None


def build(engine, games=None, player=None, fresh=False):
    """Your three lines (kept from last time unless fresh)."""
    try:
        saved = json.loads(FILE.read_text()) if not fresh else None
    except (OSError, ValueError):
        saved = None
    if saved:
        return saved
    player = player or insights._player()
    games = games if games is not None else insights._games()
    if not player or not games:
        return []
    home = insights.home()
    loose = (home.get("focus") or {}).get("pattern") in (plan.HANG, plan.FORK)
    seen = openings.habits(games, player)
    lines = [x for x in (_pick(seen, side, first, loose, engine) for side, first in SLOTS) if x]
    FILE.parent.mkdir(parents=True, exist_ok=True)
    FILE.write_text(json.dumps(lines))
    return lines


def lesson(line):
    """A line as a board lesson: you play your side, the coach explains each move."""
    side = "White" if line["side"] == "white" else "Black"
    why = (f"You already play this, and it works for you." if line.get("kept")
           else f"{'Solid and safe' if line['style'] == 'solid' else 'A clear plan'}, and hard to get tricked in.")
    return {**line, "coach": "viktor", "title": f"{line['name']} (as {side})", "why": why, "intro": why,
            "drills": [plan.opening_drill(line)]}
