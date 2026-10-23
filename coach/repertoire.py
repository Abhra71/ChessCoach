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
CHECK = DATA / "repertoire-check.json"  # when the lines were last checked against your games, and what's out of date
CHECK_GAMES, CHECK_DAYS = 50, 30  # re-check after 50 new games AND a month (24 Oct: openings need months, not days)
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
        line = _choose(fits, side, loose, engine, first, None)
        if line:  # why this one, from your games (19 Oct: every line said the same words)
            line["because"] = (f"It starts with 1. {mine}, the move you play most as White"
                               + (f", against 1... {reply}, the answer you meet most." if reply else "."))
        return line
    answers = {k[2]: v for k, v in seen.items() if k[0] == "black" and k[1] == first and k[2]}
    own = max(answers, key=lambda m: answers[m][1], default=None)
    keep = own and answers[own][1] >= 3 and answers[own][0] / answers[own][1] >= 0.5
    if keep:  # your own answer works: a sound line with it, or else the best sound answer of all
        line = _choose(lambda sans: sans[0] == first and len(sans) > 1 and sans[1] == own, side, loose, engine, first, own)
        if line:
            return line
    line = _choose(lambda sans: sans[0] == first and len(sans) > 1, side, loose, engine, first, None)
    if line and own:
        wins, played = answers[own]
        line["because"] = (f"Against 1. {first} you usually play 1... {own}, and you score {round(100 * wins / played)}% "
                           f"with it in {played} game{'s' if played != 1 else ''}. "
                           + ("That works, but it has no well-known line to learn, so here is one."
                              if keep else "This line is a sounder start."))
    return line


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
    _mark(len(games))  # new lines: the count starts again
    return lines


def why(line):
    """Why this line, from your games."""
    style = f"{'Solid and safe' if line['style'] == 'solid' else 'A clear plan'}, and hard to get tricked in."
    return ("You already play this, and it works for you." if line.get("kept")
            else f"{line['because']} {style}" if line.get("because") else style)


def lesson(line):
    """A line as a board lesson: you play your side, the coach explains each move."""
    side = "White" if line["side"] == "white" else "Black"
    reason = why(line)
    return {**line, "coach": "viktor", "title": f"{line['name']} (as {side})", "why": reason, "intro": reason,
            "drills": [plan.opening_drill(line)]}


# ---------- the re-check (24 Oct, owner: "your gameplay changes; how can three lines stay fixed?") ----------
def _mark(n_games, stale=(), now=None):
    import time
    try:
        CHECK.write_text(json.dumps({"at": int(now or time.time()), "games": n_games, "stale": list(stale)}))
    except OSError:
        pass


def stale(games=None, player=None, now=None):
    """The lines your recent games have moved away from: [{name, why}]. Checked only after CHECK_GAMES new games
    and CHECK_DAYS days; the answer is kept until the next check or until new lines are chosen."""
    import time
    from coach import prep
    now = now or time.time()
    try:
        lines = json.loads(FILE.read_text())
    except (OSError, ValueError):
        return []
    games = games if games is not None else insights._games()
    player = (player or insights._player() or "").lower()
    try:
        m = json.loads(CHECK.read_text())
    except (OSError, ValueError):
        _mark(len(games), now=now)  # lines from before the re-check existed: start counting now
        return []
    if len(games) - m.get("games", 0) < CHECK_GAMES or now - m.get("at", 0) < CHECK_DAYS * 86400:
        return m.get("stale", [])
    recent = [g for g in games if g.get("end_time", 0) > m["at"]]
    out = []
    for line in lines:
        sans = [s["san"] for s in line.get("steps", [])]
        if len(sans) < 2:
            continue
        side = line["side"]
        mine_at = 0 if side == "white" else 1  # your first move in the line
        slot = []
        for g in recent:
            if insights._side(g, player)[0] != side:
                continue
            first = prep._first_moves(g.get("pgn"), 2)
            if len(first) < 2 or (side == "black" and first[0] != sans[0]):
                continue
            slot.append((g, first[mine_at] == sans[mine_at]))
        if len(slot) < 5:
            continue
        played = [g for g, same in slot if same]
        if len(played) / len(slot) < 1 / 3:
            out.append({"name": line["name"], "why": f"you played it in only {len(played)} of your last {len(slot)} games where it could come up"})
            continue
        if len(played) >= 5:
            score = sum({"win": 1, "draw": 0.5}.get(insights._result(g, side), 0) for g in played) / len(played)
            if score < 0.4:
                out.append({"name": line["name"], "why": f"you scored {round(100 * score)}% with it in your last {len(played)} games"})
    _mark(len(games), out, now)
    return out
