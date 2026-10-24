"""Conversation without an AI key (24 Oct, owner: "most players won't add a key; they mustn't get bored").

Without AI, typed words can't be understood (CLAUDE.md: no word patterns for understanding speech), so the coach
offers questions to tap, picked for the page. Every answer is built from the player's own numbers (their games,
Stockfish's check, the review, the opening tree), said in one of several ways, never the same twice in a row, with
follow-up questions. Nothing is made up: a number that isn't there isn't said.
"""
import random

from coach import insights

# id -> the question as the player taps it
QUESTIONS = {
    "how": "How am I doing?",
    "work": "What should I work on?",
    "lose": "Why do I lose?",
    "last": "How did my last game go?",
    "opening": "Which openings work for me?",
    "move": "Why was that move good or bad?",
    "turn": "Where did this game turn?",
    "hint": "Give me a hint",
    "about": "What is this teaching me?",
}
PAGE = {  # the questions offered on each page, the most useful first
    "home": ["work", "how", "lose", "last", "opening"],
    "review": ["move", "turn", "work", "how"],
    "lesson": ["hint", "about", "work"],
}
_LAST = {}
DOING = {"left a piece hanging": "leaving pieces hanging", "walked into a fork or trick": "walking into forks and tricks",
         "missed a free capture": "missing free pieces", "walked into checkmate": "walking into checkmate",
         "missed a checkmate": "missing checkmates", "stalemated a won game": "stalemating won games"}  # question id -> the wording used last time, so the next answer is said differently


def _up(t):
    return t[:1].upper() + t[1:]


def questions(section, asked=None):
    """[{id, label}] for this page, without the one just answered."""
    ids = [q for q in PAGE.get(section, PAGE["home"]) if q != asked]
    return [{"id": q, "label": QUESTIONS[q]} for q in ids[:4]]


def _say(qid, options, rng=random):
    """One of several wordings, never the one used last time for this question."""
    options = [o for o in options if o]
    if not options:
        return ""
    fresh = [o for o in options if o != _LAST.get(qid)] or options
    pick = rng.choice(fresh)
    _LAST[qid] = pick
    return pick


def answer(qid, where=None, extra=None, home=None, rng=random):
    """{text, questions}: the answer to one tapped question, from the player's data."""
    where, extra = where or {}, extra or {}
    home = home if home is not None else insights.home()
    fn = {"how": _how, "work": _work, "lose": _lose, "last": _last, "opening": _opening,
          "move": _move, "turn": _turn, "hint": _hint, "about": _about}.get(qid)
    text = fn(home, where, extra, rng) if fn else ""
    if not text:
        text = _say("none", ["I don't have the numbers for that yet. Play and check a few more games, and ask me again.",
                             "Not enough games checked yet to answer that properly. A few more and I can."], rng)
    section = where.get("section") or "home"
    return {"text": text, "questions": questions(section, qid), "ai": False}


def _how(home, where, extra, rng):
    v = home.get("you_vs_you") or {}
    now, then = v.get("now"), v.get("then")
    res = home.get("results") or {}
    rc = home.get("rating_change")
    if not now or not then:
        if not res:
            return ""
        return f"In {home.get('games')} checked games: {res.get('win', 0)} won, {res.get('draw', 0)} drawn, {res.get('loss', 0)} lost."
    better = [x for x in (now["pieces"] < then["pieces"], now["wins"] > then["wins"], now["moments"] < then["moments"]) if x]
    pieces = (f"pieces given away down from {then['pieces']} to {now['pieces']} a game" if now["pieces"] < then["pieces"]
              else f"pieces given away up from {then['pieces']} to {now['pieces']} a game" if now["pieces"] > then["pieces"]
              else f"pieces given away the same, {now['pieces']} a game")
    wins = f"you won {now['wins']}% of your last {now['games']}, against {then['wins']}% in the {then['games']} before"
    rating = (f" Your {home.get('rating_class', '')} rating is {'up' if rc > 0 else 'down'} {abs(rc)}." if rc else "")
    if len(better) >= 2:
        return _say("how", [f"Better than before: {pieces}, and {wins}.{rating}",
                            f"Good trend. {_up(wins)}, with {pieces}.{rating}",
                            f"You're improving: {pieces}. And {wins}.{rating}"], rng)
    return _say("how", [f"Mixed: {pieces}, and {wins}.{rating} Keep going with your main habit.",
                        f"Not better yet: {wins}, with {pieces}.{rating} The work is still the same habit.",
                        f"Honestly, flat for now: {pieces}; {wins}.{rating}"], rng)


def _work(home, where, extra, rng):
    f = home.get("focus") or {}
    pats = {p["pattern"]: p for p in home.get("patterns") or []}
    if not f.get("pattern"):
        return ""
    p = pats.get(f["pattern"], {})
    rate = f" ({p['recent']} a game lately, {p['per_game']} overall)" if p.get("per_game") is not None else ""
    habit = f.get("habit") or ""
    try:
        from coach import course
        nxt = next((l for l in course.course()["lessons"] if l.get("next")), None)
    except Exception:
        nxt = None
    lesson = f" The lesson for it now: {nxt['title']}, in Your course." if nxt else ""
    doing = DOING.get(f["pattern"], f["pattern"])
    return _say("work", [f"Your biggest habit is {doing}{rate}. {habit}{lesson}",
                         f"One thing first: {doing}{rate}. {habit} Practice has your own positions for it.",
                         f"Still {doing}{rate}. The cure is a habit. {habit}{lesson}"], rng)


def _lose(home, where, extra, rng):
    games = insights._games()
    player = (insights._player() or "").lower()
    lost = []
    for g in games[:40]:
        me = insights._side(g, player)[0]
        if insights._result(g, me) == "loss":
            lost.append(g[me]["result"])
    if len(lost) < 3:
        return ""
    n = len(lost)
    mated, time_, resigned = lost.count("checkmated"), lost.count("timeout"), lost.count("resigned")
    top = (home.get("patterns") or [{}])[0]
    how = sorted([(mated, "checkmate"), (time_, "the clock"), (resigned, "resigning")], reverse=True)[0]
    habit = (f" The mistake behind most of it: {DOING.get(top['pattern'], top['pattern'])}, {top['per_game']} a game."
             if top.get("pattern") else "")
    return _say("lose", [f"Of your last {n} losses, {mated} were checkmate, {time_} on time and {resigned} resigned.{habit}",
                         f"Most of your losses ({how[0]} of the last {n}) end by {how[1]}.{habit}",
                         f"Your last {n} losses: {how[0]} by {how[1]}.{habit} Fix that and many of them turn into games."], rng)


def _last(home, where, extra, rng):
    g = home.get("last_game") or {}
    if not g.get("checked"):
        return ""
    how = {"checkmated": "by checkmate", "timeout": "on time", "resigned": "by resignation"}.get(g.get("how"), "")
    res = {"win": "You won", "loss": "You lost", "draw": "A draw"}.get(g["result"], "It ended")
    d = insights.game_detail(g["id"]) or {}
    k = [x for x in d.get("key_moments") or [] if x.get("steps")]
    km = k[0] if k else None  # the first key moment: where it went wrong
    moment = (f" The moment that mattered: move {km['move_number']}. {km['steps'][0]['text']} "
              f"{km['steps'][1]['text'] if len(km['steps']) > 1 else ''}") if km else " No big mistakes in it."
    rh = f"{res} {how}".strip()
    return _say("last", [f"{rh} against {g['opponent']} ({g['opponent_rating']}).{moment}",
                         f"Against {g['opponent']}: {rh[0].lower() + rh[1:]}, {g['moves']} moves.{moment}",
                         f"{g['opponent']}, {g['date']}: {rh[0].lower() + rh[1:]}.{moment}"], rng).replace("  ", " ").strip()


def _opening(home, where, extra, rng):
    from coach import tree
    try:
        t = tree.page().get("tree") or {}
    except Exception:
        return ""
    rows = []
    for side, root in (("White", t.get("white")), ("Black", t.get("black"))):
        if not root:
            continue
        for c in root.get("children", []):
            for n, line in [(c, f"1. {c['san']}")] + [(k, f"1. {c['san']} {k['san']}") for k in c.get("children", [])]:
                if n.get("games", 0) >= 5:
                    rows.append((n["score"], n["games"], side, {**n, "line": line}))
    if len(rows) < 2:
        return ""
    best, worst = max(rows, key=lambda r: (r[0], r[1])), min(rows, key=lambda r: (r[0], -r[1]))
    name = lambda r: f"{r[3]['line']}{' (' + r[3]['name'] + ')' if r[3].get('name') else ''} as {r[2]}"
    return _say("opening", [f"Best for you: {name(best)}, {best[0]}% in {best[1]} games. Worst: {name(worst)}, {worst[0]}% in {worst[1]}. The Opening tree in Train shows every line.",
                            f"You do well with {name(best)} ({best[0]}%, {best[1]} games) and badly after {name(worst)} ({worst[0]}%, {worst[1]} games).",
                            f"{_up(name(worst))} is where you struggle: {worst[0]}% in {worst[1]} games. {_up(name(best))} works: {best[0]}%."], rng)


def _move(home, where, extra, rng):
    if not where.get("game") or not str(where.get("ply", "")).isdigit():
        return ""
    d = insights.game_detail(where["game"]) or {}
    p = int(where["ply"])
    nar = d.get("narration") or []
    if not 0 < p <= len(nar):
        return ""
    m = nar[p - 1]
    who = "Your move" if m.get("mine") else "Their move"
    return _say("move", [f"{who}, {m.get('label', '').lower() or 'this one'}: {m['text']}",
                         f"{m['text']}", f"{m.get('label') or who}. {m['text']}"], rng)


def _turn(home, where, extra, rng):
    if not where.get("game"):
        return ""
    d = insights.game_detail(where["game"]) or {}
    nar = d.get("narration") or []
    mine = [(i, m) for i, m in enumerate(nar, 1) if m.get("mine") and m.get("lost")]
    if not mine:
        return ""
    i, m = max(mine, key=lambda x: x[1]["lost"])
    if m["lost"] < 10:
        return _say("turn", [f"No real turning point: none of your moves cost more than {round(m['lost'])} points. A clean game.",
                             "Nothing turned it: no move of yours lost much. That's a clean game."], rng)
    num = (d.get("move_numbers") or [])[i - 1] if i - 1 < len(d.get("move_numbers") or []) else (i + 1) // 2
    return _say("turn", [f"Move {num}: it cost you {round(m['lost'])} points of your chance to win. {m['text']}",
                         f"The turn came at move {num}. {m['text']}",
                         f"Look at move {num}: your chance to win dropped by {round(m['lost'])}. {m['text']}"], rng)


def _hint(home, where, extra, rng):
    hint = str(extra.get("hint") or "").strip()
    habit = str(extra.get("habit") or "").strip()
    if not hint and not habit:
        return ""
    return _say("hint", [f"{hint or habit}", f"Here's a nudge: {(hint or habit)[0].lower() + (hint or habit)[1:]}",
                         f"{habit or hint} Look again before you move."], rng)


def _about(home, where, extra, rng):
    title, teaches = str(extra.get("title") or ""), str(extra.get("teaches") or "")
    if not title and not teaches:
        return ""
    return _say("about", [f"{title}: {teaches}".strip(": "), f"This is about {title.lower() or 'one idea'}. {teaches}",
                          f"{teaches} That's the whole point of {title or 'this'}."], rng)
