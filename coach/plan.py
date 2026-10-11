"""The grandmaster's sense: when to bring something new, and what.

The library is real data: 30,000 Lichess puzzles in 20 themes (coach/puzzles.py), 3,500 openings from the Lichess
catalogue (coach/openings.py), a few core ideas below. The player's own games say what is needed:
- a habit that isn't getting better, a new kind of mistake, trouble in the opening, a losing streak, a stalemated win;
- and, when none of those, something fresh after a few days of playing.
At most one new thing at a time; it stays until it is done (or a week passes), and nothing learned comes back.
"""
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
THEME_NAME = {
    "hangingPiece": "spotting free pieces", "trappedPiece": "trapping a piece", "defensiveMove": "the saving defence",
    "pin": "the pin", "capturingDefender": "removing the defender", "fork": "the fork", "skewer": "the skewer",
    "discoveredAttack": "the discovered attack", "doubleCheck": "the double check", "backRankMate": "the back-rank mate",
    "smotheredMate": "the smothered mate", "mateIn1": "checkmate in one", "mateIn2": "checkmate in two",
    "attraction": "luring the king", "deflection": "deflection", "promotion": "promoting a pawn",
    "pawnEndgame": "pawn endings", "rookEndgame": "rook endings", "queenEndgame": "winning with the queen",
}
IDEAS = [  # core ways of thinking (the AI, with a key, can explain them in the coach's own words)
    {"id": "idea:blunder-check", "title": "The 3-second blunder check", "helps": [HANG, FORK],
     "text": "Before you click, ask: after my move, what can they take? Can they check me? Is every piece protected?"},
    {"id": "idea:cct", "title": "Checks, captures, threats", "helps": [FREE, MISSED_MATE],
     "text": "Every move, look for checks first, then captures, then threats: theirs and yours."},
    {"id": "idea:castle", "title": "Castle before move 10", "helps": [MATED],
     "text": "Knights and bishops out, then castle, usually before move 10. A castled king is hard to mate."},
    {"id": "idea:slow-down", "title": "Slow down on the big moves", "helps": [HANG],
     "text": "Spend your time on captures, checks, and moves where they attack something. Play the easy moves fast."},
    {"id": "idea:trade-ahead", "title": "Ahead? Trade pieces", "helps": [STALEMATE, HANG],
     "text": "When you're ahead in material, trade pieces. Fewer pieces means fewer tricks against you."},
]
OPENING_COACH = "zara"
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
def _puzzles(theme, rating, rng, avoid=()):
    stock = json.loads(PUZZLES.read_text()) if PUZZLES.exists() else {}
    low, high = (rating or 800) - 150, (rating or 800) + 350
    pool = [p for p in stock.get(theme, []) if low <= p["rating"] <= high and p["id"] not in avoid] or stock.get(theme, [])
    return [drills.puzzle(p, "", theme) for p in rng.sample(pool, min(PUZZLES_PER_LESSON, len(pool)))]


def tactic(theme, rating, rng, why=None):
    return {"id": f"tactic:{theme}", "kind": "tactic", "coach": "arjun", "theme": theme,
            "title": THEME_NAME[theme][0].upper() + THEME_NAME[theme][1:], "why": why,
            "intro": f"New for you: {THEME_NAME[theme]}. {drills.CLUE[theme]}", "drills": _puzzles(theme, rating, rng)}


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


def idea_for(pattern, done):
    for idea in IDEAS:
        if pattern in idea["helps"] and idea["id"] not in done:
            return {**idea, "kind": "idea", "coach": "maya", "intro": idea["text"]}
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
        idea = idea_for(focus, done) or idea_for(HANG, done)
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
            return (_memory().get("ai_idea") or {}).get("idea")
        idea = next((i for i in IDEAS if i["id"] == item_id), None)
        return {**idea, "kind": "idea", "coach": "maya", "intro": idea["text"]} if idea else None
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
    theme = next((t for t in THEMES_FOR.get(focus, ROTATION) if f"tactic:{t}" not in done), ROTATION[0])
    end = "queenEndgame" if any(r.get("pattern") == STALEMATE for rs in moves.values() for r in rs) else \
        next((t for t in ENDGAMES if f"endgame:{t}" not in done), ENDGAMES[0])
    done_families = {i.split(":", 2)[2].split(":")[0] for i in done if i.startswith("opening:")}
    items = {
        "opening": opening_lesson(games, home["player"], focus in (HANG, FORK), engine, done_families) if engine else None,
        "tactic": tactic(theme, rating, rng),
        "idea": ai_idea(home, today) or idea_for(focus, done) or {**IDEAS[0], "kind": "idea", "coach": "maya", "intro": IDEAS[0]["text"]},
        "endgame": endgame(end, rating, rng),
    }
    new = novelty(home, games, moves, engine, today, rng)
    if new and items.get(new["kind"]) and items[new["kind"]]["id"] == new["id"]:  # no duplicate: the card shows another one
        if new["kind"] == "endgame":
            items["endgame"] = endgame(next(t for t in ENDGAMES if f"endgame:{t}" != new["id"]), rating, rng)
        elif new["kind"] == "tactic":
            items["tactic"] = tactic(next(t for t in ROTATION if f"tactic:{t}" != new["id"]), rating, rng)
    return {"player": home["player"], "rating": rating, "items": items, "novelty": new, "done": sorted(done)}


def ai_idea(home, today=None, ask_ai=None):
    """With the player's AI key: one fresh way of approaching the game, written for them (renewed weekly).
    No moves or squares allowed (the engine decides concrete chess); None if the AI is busy or there's no key."""
    from coach import ai, coaches
    today = today or date.today()
    week = f"{today.isocalendar()[0]}-{today.isocalendar()[1]}"
    mem = _memory()
    cached = mem.get("ai_idea")
    if cached and cached.get("week") == week:
        return cached["idea"]
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
    idea = {"id": f"idea:ai:{week}", "kind": "idea", "coach": "maya", "title": title, "intro": body, "text": body,
            "why": "A new idea Maya wrote for you this week, from your games.", "ai": True}
    mem["ai_idea"] = {"week": week, "idea": idea}
    _save(mem)
    return idea
