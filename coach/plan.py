"""The grandmaster's sense: when to bring something new, and what.

The library is real data: 30,000 Lichess puzzles in 20 themes (coach/puzzles.py), 3,500 openings from the Lichess
catalogue (coach/openings.py), a few core ideas below. The player's own games say what is needed:
- a habit that isn't getting better, a new kind of mistake, trouble in the opening, a losing streak, a stalemated win;
- and, when none of those, something fresh after a few days of playing.
At most one new thing at a time; it stays until it is done (or a week passes), and nothing learned comes back.
"""
import collections
import json
import random
import time
from datetime import date

import chess

from coach import drills, insights, openings
from coach.paths import DATA
from coach.puzzles import OUT as PUZZLES
from coach.review import LOSING_MATERIAL

MEMORY = DATA / "novelty.json"
COOLDOWN_DAYS = 3  # at most one new thing every few days
STALE_DAYS = 7  # a new thing not done after a week makes room for another
PUZZLES_PER_LESSON = 4

HANG, FREE, FORK = "left a piece hanging", "missed a free capture", "walked into a fork or trick"
MATED, MISSED_MATE, STALEMATE = "walked into checkmate", "missed a checkmate", "stalemated a won game"
# the new tactics to bring for each habit, in the order a coach would teach them
THEMES_FOR = {
    HANG: ["hangingPiece", "trappedPiece", "defensiveMove", "pin"],
    FREE: ["hangingPiece", "capturingDefender", "fork"],
    FORK: ["fork", "pin", "skewer", "discoveredAttack", "doubleCheck"],
    MATED: ["backRankMate", "defensiveMove", "smotheredMate"],
    MISSED_MATE: ["mateIn1", "mateIn2", "backRankMate", "smotheredMate", "attraction"],
    STALEMATE: ["queenEndgame", "pawnEndgame"],
}
ROTATION = ["fork", "pin", "skewer", "discoveredAttack", "deflection", "backRankMate", "smotheredMate", "promotion"]
ENDGAMES = ["pawnEndgame", "rookEndgame", "queenEndgame"]
# the whole Lichess library on the roads (23 Oct test: "practise everything about chess, curated for us"): after the
# player's own habit and the rotation, every other tactic theme, simplest first; every ending
LADDER = ["mateIn1", "hangingPiece", "fork", "pin", "skewer", "mateIn2", "backRankMate", "trappedPiece",
          "discoveredAttack", "capturingDefender", "defensiveMove", "deflection", "attraction", "doubleCheck",
          "promotion", "smotheredMate", "opening", "quietMove", "intermezzo", "clearance", "interference",
          "xRayAttack", "exposedKing", "kingsideAttack", "advancedPawn", "zugzwang"]
ENDINGS_ALL = ["pawnEndgame", "rookEndgame", "queenEndgame", "bishopEndgame", "knightEndgame"]
THEME_NAME = {
    "hangingPiece": "spotting free pieces", "trappedPiece": "trapping a piece", "defensiveMove": "the saving defence",
    "pin": "the pin", "capturingDefender": "removing the defender", "fork": "the fork", "skewer": "the skewer",
    "discoveredAttack": "the discovered attack", "doubleCheck": "the double check", "backRankMate": "the back-rank mate",
    "smotheredMate": "the smothered mate", "mateIn1": "checkmate in one", "mateIn2": "checkmate in two",
    "attraction": "luring the king", "deflection": "deflection", "promotion": "promoting a pawn",
    "pawnEndgame": "pawn endings", "rookEndgame": "rook endings", "queenEndgame": "winning with the queen",
    "quietMove": "the quiet move", "zugzwang": "zugzwang: making them move", "intermezzo": "the in-between move",
    "clearance": "clearing the way", "interference": "cutting the line", "xRayAttack": "the X-ray attack",
    "exposedKing": "attacking an open king", "kingsideAttack": "the kingside attack", "advancedPawn": "the advanced pawn",
    "bishopEndgame": "bishop endings", "knightEndgame": "knight endings", "opening": "tricks in the opening",
}
# Core ways of thinking, each practised on the board: positions from the player's own games ("own": patterns) or
# Lichess puzzles ("puzzles": themes), with a checklist the player ticks before every move (the habit itself).
IDEAS = [
    {"id": "idea:blunder-check", "title": "The 3-second blunder check", "helps": [HANG, FORK],
     "text": "Before you click, ask: after my move, what can they take? Can they check me? Is every piece protected?",
     "own": [HANG, FORK], "puzzles": ["hangingPiece", "fork"],
     "checklist": ["After my move, what can they take?", "Can they check me?", "Is every piece of mine protected?"]},
    {"id": "idea:cct", "title": "Checks, captures, threats", "helps": [FREE, MISSED_MATE],
     "text": "Every move, look for checks first, then captures, then threats: theirs and yours.",
     "own": [FREE], "puzzles": ["mateIn1", "hangingPiece"],
     "checklist": ["Checks: can I give check?", "Captures: is anything free to take?", "Threats: what are they threatening?"]},
    {"id": "idea:castle", "title": "Castle before move 10", "helps": [MATED],
     "text": "Knights and bishops out, then castle, usually before move 10. A castled king is hard to mate.",
     "own": [MATED], "puzzles": ["backRankMate", "defensiveMove"],
     "checklist": ["Is my king safe, or still in the middle?", "Can they check me next move?", "Is there a move that stops their threat?"]},
    {"id": "idea:slow-down", "title": "Slow down on the big moves", "helps": [HANG],
     "text": "Spend your time on captures, checks, and moves where they attack something. Play the easy moves fast.",
     "own": [HANG], "puzzles": ["hangingPiece", "trappedPiece"],
     "checklist": ["Is this a big moment: a capture, a check, an attack?",
                   "If yes: after my move, what can they take, and which checks can they give?"]},  # the drill has mates too (19 Oct)
    {"id": "idea:trade-ahead", "title": "Ahead? Trade pieces", "helps": [STALEMATE, HANG],
     "text": "When you're ahead in material, trade pieces. Fewer pieces means fewer tricks against you.",
     "own": [], "puzzles": ["queenEndgame", "pawnEndgame"],
     "checklist": ["Am I ahead in material?", "Can I trade, or finish it?", "Does their king still have a square to move to?"]},
]


def idea_drills(idea, rating, rng):
    """Positions to practise an idea on: the player's own (from the practice set), topped up with puzzles."""
    own = []
    try:
        own = [d for d in json.loads((DATA / "drills.json").read_text()) if d["kind"] == "game" and d["pattern"] in idea.get("own", [])]
    except (OSError, ValueError):
        pass
    rng.shuffle(own)
    picked = own[:PUZZLES_PER_LESSON]
    for theme in idea.get("puzzles", []):
        if len(picked) >= PUZZLES_PER_LESSON + 1:
            break
        picked += _puzzles(theme, rating, rng)[:2]
    return picked


def idea_lesson(idea, rating, rng):
    return {**idea, "kind": "idea", "coach": "viktor", "intro": idea["text"], "drills": idea_drills(idea, rating, rng)}
OPENING_COACH = "viktor"  # Your plan is Viktor's
WHY = {
    "stalemate": "You've stalemated {n}. This is the habit that keeps those points.",
    "new": "{pattern_cap} is new for you: {recent} times in your last 10 games, more than before.",
    "opening": "In {pct}% of your last 20 games you lost material before move 12. A solid opening helps most there.",
    "slump": "You lost {losses} of your last 5 games. Time for something fresh, not more of the same.",
    "stuck": "{pattern_cap} isn't improving yet ({lately} a game lately, {before} before). Let's attack it from a new angle.",
    "fresh": "You've been playing steadily. Here's something new to add to your game.",
}


# ---------- memory ----------
def _memory():
    try:
        return json.loads(MEMORY.read_text())
    except (OSError, ValueError):
        return {"shown": {}, "done": []}


def _save(mem):
    MEMORY.parent.mkdir(parents=True, exist_ok=True)
    MEMORY.write_text(json.dumps(mem))


def mark(item_id, done=False, today=None, novelty=False):
    """The player saw (or finished) something. novelty: it was the coach's new thing (one at a time, with cooldown);
    opening a card in Your plan is not."""
    mem = _memory()
    day = (today or date.today()).isoformat()
    mem.setdefault("shown", {}).setdefault(item_id, day)
    if novelty:
        mem.setdefault("novelty", {}).setdefault(item_id, day)
    if done and item_id not in mem["done"]:
        mem["done"].append(item_id)
    _save(mem)


# ---------- the signals ----------
def signals(home, games, moves, player):
    """What the player's games say right now (all from engine-checked games)."""
    checked = [g for g in games if g["url"] in moves]  # newest first
    out = {"stalemates": sum(1 for g in checked for r in moves[g["url"]] if r.get("pattern") == STALEMATE)}
    recent, earlier = checked[:10], checked[10:]
    rate = lambda gs, p: sum(1 for g in gs for r in moves[g["url"]] if r.get("pattern") == p) / max(1, len(gs))
    out["new"] = [(p, sum(1 for g in recent for r in moves[g["url"]] if r.get("pattern") == p))
                  for p in THEMES_FOR if len(earlier) >= 10 and rate(recent, p) >= 2 * max(rate(earlier, p), 0.1)
                  and rate(recent, p) * len(recent) >= 3]
    last20 = checked[:20]
    early = sum(1 for g in last20 if any(r.get("pattern") in LOSING_MATERIAL and r.get("ply", 99) <= 24 for r in moves[g["url"]]))
    out["opening_trouble"] = round(100 * early / len(last20)) if last20 else 0
    res = [insights._result(g, insights._side(g, player)[0]) for g in checked[:5]]
    out["losses"] = res.count("loss")
    out["stuck"] = bool(home.get("focus")) and (home.get("pieces_last20") or 0) >= 0.85 * (home.get("pieces_per_game") or 0) > 0
    out["active"] = sum(1 for g in checked if g["end_time"] >= time.time() - 7 * 86400)
    return out


# ---------- the things to bring ----------
# a lesson's puzzles must match what the lesson teaches: "winning with the queen" is for players who stalemate won
# games, so it takes only the queen endings that end in checkmate (13 Oct test: a queen ending about winning
# material ended with the player's queen taken, and the lesson's "checkmate, no stalemate" advice made no sense)
LESSON_NEEDS = {"queenEndgame": "mate"}


def _puzzles(theme, rating, rng, avoid=None):
    """Puzzles on a theme at the player's level, easiest first. When there are too few at that level, the easiest
    ones of the theme, never a random one (13 Oct test: a 1428 puzzle for a 254 player). A puzzle answered on an
    earlier day is never offered again, in a lesson, the plan or today's 5 minutes (23 Oct test)."""
    if avoid is None:
        from coach import memory
        avoid = memory.seen_before()
    stock = json.loads(PUZZLES.read_text()) if PUZZLES.exists() else {}
    every = [p for p in stock.get(theme, []) if p["id"] not in avoid] or stock.get(theme, [])
    need = LESSON_NEEDS.get(theme)
    if need:
        every = [p for p in every if any(t.startswith(need) for t in p.get("themes", []))] or every
    low, high = (rating or 800) - 150, (rating or 800) + 350
    pool = [p for p in every if low <= p["rating"] <= high]
    if len(pool) < PUZZLES_PER_LESSON:
        pool = sorted(every, key=lambda p: p["rating"])[:PUZZLES_PER_LESSON * 3]
    chosen = sorted(rng.sample(pool, min(PUZZLES_PER_LESSON, len(pool))), key=lambda p: p["rating"])
    return [drills.puzzle(p, "", theme) for p in chosen]


def tactic(theme, rating, rng, why=None):
    return {"id": f"tactic:{theme}", "kind": "tactic", "coach": "viktor", "theme": theme,
            "title": THEME_NAME[theme][0].upper() + THEME_NAME[theme][1:], "why": why,
            "intro": drills.CLUE[theme], "drills": _puzzles(theme, rating, rng)}


def endgame(theme, rating, rng, why=None):
    return {**tactic(theme, rating, rng, why), "id": f"endgame:{theme}", "kind": "endgame", "coach": "viktor"}


def opening_lesson(games, player, loose, engine, done_families, why=None):
    o = openings.suggest(games, player, loose, engine, avoid=done_families)
    if not o:
        return None
    side_word = "White" if o["side"] == "white" else "Black"
    lines = []
    if o["side"] == "black" and o.get("current"):
        lines.append(f"Against {o['against']} you usually answer {o['current']}: {o['score'][0]} wins in {o['score'][1]} games.")
    lines.append(f"Try the {o['name']} as {side_word}: {'solid and safe' if o['style'] == 'solid' else 'a clear plan'}, "
                 "and hard to get tricked in.")
    return {**o, "coach": OPENING_COACH, "why": why or " ".join(lines), "intro": " ".join(lines),
            "drills": [opening_drill(o)]}


def opening_drill(o):
    """Play your side of the opening's main line; the coach explains each move."""
    board, steps = chess.Board(), []
    moves = o["steps"]
    i = 0
    if not moves[0]["mine"]:  # Black: White's first move is shown first
        board.push_uci(moves[0]["uci"])
        i = 1
    start = drills.squares(chess.Board())
    while i < len(moves):
        st = moves[i]
        right = chess.Move.from_uci(st["uci"])
        reply = chess.Move.from_uci(moves[i + 1]["uci"]) if i + 1 < len(moves) else None
        idea = st["idea"]
        steps.append(drills.step(board, {right}, lambda m, idea=idea: f"Not in this opening. The move here: {idea}", reply))
        steps[-1]["idea"] = idea
        board.push(right)
        if reply:
            board.push(reply)
        i += 2
    first = o["steps"][0]
    return {"id": o["id"], "kind": "opening", "flip": o["side"] == "black", "pattern": "", "hint": "Develop, take the centre, castle.",
            "intro": f"Play the {o['name']}. Make your moves; I'll answer and explain.", "where": o["name"],
            "url": "https://lichess.org/opening/" + o["name"].replace(" ", "_").replace(":", ""), "link": "see it on lichess.org",
            "start": start, "last": [first["uci"][:2], first["uci"][2:4]] if not first["mine"] else None, "steps": steps}


def idea_for(pattern, done, rating=None, rng=None):
    for idea in IDEAS:
        if pattern in idea["helps"] and idea["id"] not in done:
            return idea_lesson(idea, rating, rng or random.Random(0))
    return None


# ---------- the sense ----------
def novelty(home=None, games=None, moves=None, engine=None, today=None, rng=None):
    """The one new thing to bring now, or None (its reason is remembered, so it reads the same when it comes back)."""
    new = _novelty(home, games, moves, engine, today, rng)
    if new and not new.get("again") and new.get("why"):
        mem = _memory()
        mem.setdefault("why", {})[new["id"]] = new["why"]
        _save(mem)
    return new


def _novelty(home=None, games=None, moves=None, engine=None, today=None, rng=None):
    """The one new thing to bring now, or None. {..., why} says why it is needed now."""
    home = home if home is not None else insights.home()
    player = home.get("player")
    if not player or not home.get("games"):
        return None
    games = games if games is not None else insights._games()
    moves = moves if moves is not None else insights._moves()
    today = today or date.today()
    rng = rng or random.Random(today.isoformat())
    mem = _memory()
    done = set(mem.get("done", []))
    # one at a time: the current new thing stays until done, or for a week
    open_items = [(i, d) for i, d in mem.get("novelty", {}).items() if i not in done]
    if open_items:
        item_id, since = max(open_items, key=lambda x: x[1])
        if (today - date.fromisoformat(since)).days < STALE_DAYS:
            again = build(item_id, home, games, moves, engine, rng, done)
            if again:
                return {**again, "why": mem.get("why", {}).get(item_id) or again.get("why") or "", "again": True}
    recent = max((date.fromisoformat(d) for d in mem.get("novelty", {}).values()), default=None)
    if recent and (today - recent).days < COOLDOWN_DAYS:
        return None
    s = signals(home, games, moves, player)
    focus = (home.get("focus") or {}).get("pattern")
    rating = home.get("rating")
    fresh = lambda themes: next((t for t in themes if f"tactic:{t}" not in done and f"tactic:{t}" not in mem["shown"]), None)
    fill = lambda key, **kw: WHY[key].format(**kw)

    if s["stalemates"] and f"endgame:queenEndgame" not in done:
        return endgame("queenEndgame", rating, rng, fill("stalemate", n=f"{s['stalemates']} won game" + ("" if s["stalemates"] == 1 else "s")))
    for pattern, recent_n in s["new"]:
        theme = fresh(THEMES_FOR[pattern])
        if theme:
            return tactic(theme, rating, rng, fill("new", pattern_cap=pattern[0].upper() + pattern[1:], recent=recent_n))
    if s["opening_trouble"] >= 25 and engine is not None:
        done_families = {i.split(":", 2)[2].split(":")[0] for i in done if i.startswith("opening:")}
        o = opening_lesson(games, player, focus in (HANG, FORK), engine, done_families, fill("opening", pct=s["opening_trouble"]))
        if o and o["id"] not in done:
            return o
    if s["losses"] >= 4:
        idea = idea_for(focus, done, rating, rng) or idea_for(HANG, done, rating, rng)
        if idea:
            return {**idea, "why": fill("slump", losses=s["losses"])}
    if s["stuck"] and focus:
        theme = fresh(THEMES_FOR.get(focus, []))
        if theme:
            return tactic(theme, rating, rng, fill("stuck", pattern_cap=focus[0].upper() + focus[1:],
                                                     lately=home.get("pieces_last20"), before=home.get("pieces_per_game")))
    if s["active"] >= 3:
        theme = fresh(ROTATION)
        if theme:
            return tactic(theme, rating, rng, fill("fresh"))
    return None


def build(item_id, home, games, moves, engine, rng, done):
    """Rebuild a new thing shown before (so it stays the same until it is done)."""
    kind, _, rest = item_id.partition(":")
    rating = home.get("rating")
    if kind == "tactic":
        return tactic(rest, rating, rng)
    if kind == "endgame":
        return endgame(rest, rating, rng)
    if kind == "idea":
        if item_id.startswith("idea:ai:"):
            idea = (_memory().get("ai_idea") or {}).get("idea")
            return _practised(idea, rating, rng) if idea else None
        idea = next((i for i in IDEAS if i["id"] == item_id), None)
        return idea_lesson(idea, rating, rng) if idea else None
    if kind == "opening" and engine is not None:
        focus = (home.get("focus") or {}).get("pattern")
        return opening_lesson(games, home["player"], focus in (HANG, FORK), engine, set())
    return None


def plan(home=None, engine=None, today=None):
    """The 'Your plan' page: one opening, one tactic, one idea, one endgame (each from its own coach), and the
    one new thing if the coach senses it's needed now."""
    home = home if home is not None else insights.home()
    if not home.get("player"):
        return {"player": None}
    games, moves = insights._games(), insights._moves()
    today = today or date.today()
    rng = random.Random(today.isoformat())
    mem = _memory()
    done = set(mem.get("done", []))
    focus = (home.get("focus") or {}).get("pattern") or HANG
    rating = home.get("rating")
    # each card walks a fixed road, one topic after another; a done topic leaves the road and stays replayable
    # (23 Oct test: "I lose track of what I've done and what's coming next")
    tactic_road = ["tactic:" + t for t in THEMES_FOR.get(focus, []) + ROTATION + LADDER]
    tactics = _path(tactic_road, done)
    stalemated = any(r.get("pattern") == STALEMATE for rs in moves.values() for r in rs)
    endings = _path(["endgame:" + t for t in (["queenEndgame"] if stalemated else []) + ENDINGS_ALL], done)
    ideas = _path([i["id"] for i in sorted(IDEAS, key=lambda i: focus not in i["helps"])], done)
    done_families = {i.split(":", 2)[2].split(":")[0] for i in done if i.startswith("opening:")}
    opening = opening_lesson(games, home["player"], focus in (HANG, FORK), engine, done_families) if engine else None
    if opening and mem.get("openings", {}).get(opening["id"]) != opening["side"]:  # so a done one replays from its side
        mem.setdefault("openings", {})[opening["id"]] = opening["side"]
        _save(mem)
    items = {
        "opening": opening,
        "tactic": tactic(tactics["now"].split(":")[1], rating, rng),
        "idea": ai_idea(home, today, rating=rating, rng=rng) or idea_lesson(next(i for i in IDEAS if i["id"] == ideas["now"]), rating, rng),
        "endgame": endgame(endings["now"].split(":")[1], rating, rng),
    }
    if items["idea"].get("ai"):  # Maya's idea of the week comes first; the road's own next one after it
        ideas = {**ideas, "next": (done_item(ideas["now"]) or {}).get("title")}
    paths = {"tactic": tactics, "endgame": endings, "idea": ideas,
             "opening": {"at": len(done_families) + 1, "of": None, "next": "another opening from your games"}}
    new = novelty(home, games, moves, engine, today, rng)
    if new and items.get(new["kind"]) and items[new["kind"]]["id"] == new["id"]:  # no duplicate: the card shows another one
        if new["kind"] == "endgame":
            paths["endgame"] = _path(["endgame:" + t for t in ENDINGS_ALL if "endgame:" + t != new["id"]], done)
            items["endgame"] = endgame(paths["endgame"]["now"].split(":")[1], rating, rng)
        elif new["kind"] == "tactic":
            paths["tactic"] = _path([t for t in dict.fromkeys(tactic_road) if t != new["id"]], done)
            items["tactic"] = tactic(paths["tactic"]["now"].split(":")[1], rating, rng)
    for kind, item in items.items():
        if item:
            item["path"] = {k: v for k, v in paths[kind].items() if k != "now"}
    return {"player": home["player"], "rating": rating, "items": items, "novelty": new, "done": sorted(done),
            "done_items": [x for x in (done_item(i, mem) for i in mem.get("done", [])) if x]}


def _path(ids, done):
    """One card's road: the topic now, how far along it is, and the one after (all done: round again)."""
    seq = list(dict.fromkeys(ids))
    left = [t for t in seq if t not in done]
    after = left[1] if len(left) > 1 else None
    return {"now": left[0] if left else seq[0], "at": min(len(seq) - len(left) + 1, len(seq)), "of": len(seq),
            "more": max(len(left) - 1, 0),
            "next": (done_item(after) or {}).get("title") if after else None}


def done_item(item_id, mem=None):
    """A topic's name for the Done row: {id, kind, title}."""
    kind, _, rest = item_id.partition(":")
    if kind in ("tactic", "endgame") and rest in THEME_NAME:
        return {"id": item_id, "kind": kind, "title": THEME_NAME[rest][0].upper() + THEME_NAME[rest][1:]}
    if kind == "idea":
        idea = next((i for i in IDEAS if i["id"] == item_id), None)
        if item_id.startswith("idea:ai:"):
            idea = ((mem or _memory()).get("ai_idea") or {}).get("idea")
            idea = idea if idea and idea.get("id") == item_id else None
        return {"id": item_id, "kind": "idea", "title": idea["title"]} if idea else None
    if kind == "opening":
        side = (mem or _memory()).get("openings", {}).get(item_id, "white")
        return {"id": item_id, "kind": "opening", "title": f"{rest.split(':', 1)[-1]} (as {side.title()})"}
    return None


def replay(item_id, home, rng, side=None):
    """A done or explored topic built again, to practise (puzzles from Lichess; an opening's line from the Lichess
    catalogue, played from side, or the side it was played from before)."""
    kind, _, rest = item_id.partition(":")
    if kind in ("tactic", "endgame"):
        theme = rest
        if theme not in _library_themes():
            return None
        return (tactic if kind == "tactic" else endgame)(theme, home.get("rating"), rng)
    if kind == "opening":
        eco, _, name = rest.partition(":")
        sans = next((x[2] for x in _catalogue() if x[0] == eco and x[1] == name), None)
        if not sans:
            return None
        mem = _memory()
        if side in ("white", "black"):
            if mem.setdefault("openings", {}).get(item_id) != side:
                mem["openings"][item_id] = side
                _save(mem)
        else:
            side = mem.get("openings", {}).get(item_id) or default_side(name)
        if not any((i % 2 == 0) == (side == "white") for i in range(len(sans))) or \
                (side == "black" and len(sans) < 2):  # nothing of their own to play
            return None
        o = {"id": item_id, "kind": "opening", "title": f"{name} (as {side.title()})", "name": name, "eco": eco,
             "side": side, "style": openings.style(name), **openings.teach(sans, side)}
        line = f"The {name}, as played on Lichess: make your moves as {side.title()}, I'll answer and explain."
        return {**o, "coach": OPENING_COACH, "why": line, "intro": line, "drills": [opening_drill(o)]}
    return build(item_id, home, None, None, None, rng, set())


# ---------- Explore: the whole library, to browse or search (23 Oct test) ----------
_CATALOGUE = []


def _catalogue():
    """The Lichess opening catalogue, read once."""
    if not _CATALOGUE:
        _CATALOGUE.extend(openings.catalogue())
    return _CATALOGUE


def _library_themes():
    """The Lichess puzzle themes this computer has puzzles for."""
    try:
        stock = json.loads(PUZZLES.read_text())
    except (OSError, ValueError):
        return set()
    return {t for t, v in stock.items() if isinstance(v, list) and v and t in THEME_NAME}


def default_side(name):
    """Whose opening it is, from its Lichess name: a Defence, a Countergambit or a Declined/Accepted gambit is Black's."""
    first = name.split(":")[0].lower()
    return "black" if any(w in first for w in ("defense", "defence", "countergambit", "declined", "accepted")) else "white"


def _plain(text):
    return "".join(c for c in text.lower().replace("defence", "defense") if c.isalnum() or c == " ").split()


def library():
    """Everything there is, grouped, for Explore before anything is typed: every tactic and ending theme, and the
    opening families with the most lines first."""
    themes = _library_themes()
    name = lambda t: THEME_NAME[t][0].upper() + THEME_NAME[t][1:]
    ends = [t for t in ENDINGS_ALL if t in themes]
    tactics = [t for t in dict.fromkeys(LADDER + ROTATION) if t in themes and t not in ENDINGS_ALL]
    lines = _lines()
    fams = collections.Counter(_family(n) for _, n, _ in lines)
    return {"tactics": [{"id": "tactic:" + t, "title": name(t)} for t in tactics],
            "endings": [{"id": "endgame:" + t, "title": name(t)} for t in ends],
            "families": [{"name": f, "lines": n} for f, n in sorted(fams.items(), key=lambda x: (-x[1], x[0]))],
            "openings": len(lines)}


def _family(name):
    """Explore's family: "London System, with Bd3" belongs to London System."""
    return name.split(":")[0].split(",")[0].strip()


def _lines():
    """Every playable catalogue line once (by name; at least two moves)."""
    seen, out = set(), []
    for eco, n, s in _catalogue():
        if len(s) >= 2 and n not in seen:
            seen.add(n)
            out.append((eco, n, s))
    return out


def family_lines(family):
    """One family's lines for its dropdown: the main line first, then its variations by name."""
    rows = [(eco, n, s) for eco, n, s in _lines() if _family(n) == family]
    rows.sort(key=lambda o: (o[1] != family, o[1]))
    return [{"id": f"opening:{eco}:{n}", "kind": "opening", "title": n, "side": default_side(n), "moves": len(s)}
            for eco, n, s in rows]


def search(q, limit=40):
    """Everything whose name has every word typed: tactics and endings by their plain name, openings by their Lichess
    name. Openings come back with the side they're usually learned from."""
    words = _plain(q or "")
    if not words:
        return []
    hit = lambda text: all(any(t.startswith(w) for t in _plain(text)) for w in words)  # word starts: "rook" is not "Brooklyn"
    lib = library()
    out = [{**x, "kind": "tactic"} for x in lib["tactics"] if hit(x["title"] + " " + x["id"].split(":")[1])]
    out += [{**x, "kind": "endgame"} for x in lib["endings"] if hit(x["title"] + " " + x["id"].split(":")[1])]
    found = [(eco, n, s) for eco, n, s in _catalogue() if len(s) >= 2 and hit(n)]
    found.sort(key=lambda o: (not hit(openings.family(o[1])), o[1].count(":"), len(o[1])))
    seen = set()
    for eco, n, s in found:
        if n in seen:
            continue
        seen.add(n)
        out.append({"id": f"opening:{eco}:{n}", "kind": "opening", "title": n, "side": default_side(n),
                    "moves": len(s)})
        if len(out) >= limit:
            break
    return out


def ai_idea(home, today=None, ask_ai=None, rating=None, rng=None):
    """With the player's AI key: one fresh way of approaching the game, written for them (renewed weekly).
    No moves or squares allowed (the engine decides concrete chess); None if the AI is busy or there's no key."""
    from coach import ai, coaches
    today = today or date.today()
    week = f"{today.isocalendar()[0]}-{today.isocalendar()[1]}"
    mem = _memory()
    cached = mem.get("ai_idea")
    if cached and cached.get("week") == week:
        return _practised(cached["idea"], rating, rng)
    if ask_ai is None:
        if not ai.ready():
            return None
        ask_ai = ai.complete
    card = coaches.player_card(home)
    system = (coaches.PERSONA["maya"] + " Suggest ONE new way of approaching chess for this player, at their level, that "
              "would help with their main habit. Not a generic tip they already know from their card. Never name squares or "
              'moves. Reply as JSON only: {"title": "3 to 6 words", "text": "2 short sentences"}.')
    try:
        text, _ = ask_ai(system, json.dumps(card), 200)
        data = json.loads(text[text.index("{"): text.rindex("}") + 1])
        title, body = str(data["title"]).strip()[:60], str(data["text"]).strip()[:400]
    except Exception:  # busy, down, or not JSON: the written ideas stay
        return None
    if not title or not body or coaches.SQUARE.search(title + " " + body):
        return None
    idea = {"id": f"idea:ai:{week}", "kind": "idea", "coach": "viktor", "title": title, "intro": body, "text": body,
            "why": "A new idea Maya wrote for you this week, from your games.", "ai": True}
    mem["ai_idea"] = {"week": week, "idea": idea}
    _save(mem)
    return _practised(idea, rating, rng)


def _practised(idea, rating, rng):
    """An AI idea is practised on the player's own positions, with the blunder-check questions."""
    base = IDEAS[0]
    return {**idea, "own": base["own"], "puzzles": base["puzzles"], "checklist": base["checklist"],
            "drills": idea_drills(base, rating, rng or random.Random(0))}
