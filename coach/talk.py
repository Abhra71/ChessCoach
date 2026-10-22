"""Talking with your coach by voice (0.6, flagship 2): what you said -> the coach's reply, and what to do.

The AI understands what you mean (no sentence patterns: CLAUDE.md) and answers in the coach's own words, from the
facts it is given. It can also ask for one thing to be done, from a fixed list, and every one is checked here
before anything happens: open a page, open the review of a game it was told about, start a rematch of one, or show
the next step of the review on screen. A game it wasn't told about, or a page that doesn't exist, is refused.
Fair play: only finished, checked games are in the facts; nothing about a game being played.
"""
import json

from coach import coaches, insights

PAGES = {"home": "home", "games": "games", "practice": "practice", "daily": "daily", "plan": "plan",
         "progress": "progress", "openings": "openings", "settings": "settings", "level": "level",
         "endgames": "endgames", "prep": "prep", "course": "course"}
RECENT = 12  # the games the coach can find by name ("my game against X"); fewer words in, more turns a minute on a free key

RULES = (
    " This is a spoken conversation: reply in at most 3 short sentences, easy to say out loud, with no lists and no "
    "symbols. Only talk about chess and this player's games; never give advice about a game being played right now. "
    "The facts are all you know. Reply ONLY with JSON, four fields: "
    "{\"do\": \"<one of the words below, or none>\", \"what\": \"<what it applies to>\", \"say\": \"what you say\", "
    "\"offer\": \"<what you suggest next, as a do and a what, like open practice or review 1, or none>\"}. "
    "You are their coach, not a tool: when it helps, suggest the one next thing worth doing and put it in offer, so they "
    "can press it; offer never does it by itself. When they say yes, ok or please do to your last suggestion, do it. "
    "do open, what a page: home, games, practice, daily (today's five minutes), plan, progress, openings, settings, level (their level and "
    "what to work on next), endgames (the endgame trainer), prep (prep against an opponent), course (their course and "
    "the next lesson). "
    "do review, what a game's n: opens the review of one of the recent_games (n 1 is their last game, n 2 the one "
    "before, so \"my third last game\" is 3; \"my game against X\" is the n of the newest game against X). "
    "do rematch, what a game's n: replays a lost or drawn game from where it went wrong. "
    "do next: starts the review, or shows its next step or move (only when where_the_player_is says review). "
    "do back: the review's previous step or move again (only when where_the_player_is says review). "
    "In a review, \"next\", \"forward\", \"previous\", \"back\" or \"previous move\" means do next or do back, even "
    "with other words around them; moving through the review is always allowed. "
    "do prep, what a chess.com username: prepares against any player before a game (their openings and how their "
    "games end), using a name from the facts when it sounds like one of them. "
    "do guide, what a place on chess.com (puzzles, bots, archive: their game history on chess.com, lessons, friend: "
    "the Play Online page, where they press Play a Friend themselves): shows "
    "them the way there with a red ring, step by step. "
    "When the player asks you to open, show or take them to a page, do is open, every time. "
    "When where_the_player_is has chesscom and they ask how to get somewhere on chess.com (bots, puzzles, lessons, their "
    "game history), do is guide, never open: Knightwise has no bots; chess.com does. "
    "do none when the player only talks or asks. Ask for something only when the player wants it. If they ask for "
    "something you can't do yourself, like changing a setting, open the page where they can. If they name an opponent "
    "who isn't in the facts, say you can't find that game. Never say you are opening, replaying or showing something "
    "unless do does it. Nobody can delete games, change settings or change anything by talking to you: say so, and "
    "open the page only if it really has what they asked for. Mention their habit only when it answers what they "
    "asked, never as a closing line. \"say\" is always at least one sentence."
)
# what the coaches know about the app itself (22 Oct test: Maya called Viktor "the avatar" and didn't know the maker)
ABOUT = {
    "made_by": "Abhra Chakraborty, one person working alone; free forever, no account, no ads",
    "coaches": {"Maya": "your games, reviews, practice and Home", "Viktor": "your progress, plan, course, level and Train"},
    "what_they_can_do_by_voice": "open any page, review a game by its opponent or how recent it is, rematch it, say next or "
                                 "back in a review, prep against a chess.com player, and on chess.com show the way with a red ring",
    "fair_play": "completely off during a game against a real person",
    "the_games_they_see": "the last 12 games in detail; all_games has the totals",
}
REFUSED = {  # an action the coach asked for that isn't possible here: say so, never "let's replay it" and nothing (19 Oct)
    "rematch": "I can't start a rematch from here. Open a game you lost or drew, then say rematch.",
    "next": "Open a game's review first, then say next and I'll go through it step by step.",
    "back": "Open a game's review first, then say next or back to go through it.",
    "review": "I can't find that game in your recent games.",
    "guide": "I show the way on chess.com itself. Open chess.com, ask me there, and I'll ring it for you.",
}
BUSY = "Give me a minute, I'm thinking too slowly right now. Ask me again in a moment."
OPEN_FAILED = "I can't open that from here. Tell me which page, like your games, Practice or Settings."


def recent_games(n=RECENT):
    """The player's last games as the coach may name them: id, opponent, result, date, key moments."""
    games = [{k: g[k] for k in ("id", "opponent", "result", "date", "time_class", "moments")}
             for g in insights.games_list() if g.get("checked")][:n]
    return [{"n": i + 1, **g} for i, g in enumerate(games)]  # 1 = the last game: "my third last game" is 3, no counting


def level_now():
    """Where the player is on the ladder (coach/ladder.py), so the coach can say what to work on next."""
    from coach import ladder
    try:
        page = ladder.page()
        return {"level": page["current"] + 1, **(ladder.focus(page) or {})} if page.get("levels") else None
    except Exception:  # never let the ladder stop a conversation
        return None


def next_lesson():
    """The course lesson the player's games pick next (coach/course.py), so the coach can suggest it."""
    from coach import course
    try:
        c = course.course()
        row = next((r for r in c["lessons"] if r["id"] == c["next"]), None)
        return {"title": row["title"], "why": course.reason(row), "habit": row["habit"]} if row else None
    except Exception:  # never let the course stop a conversation
        return None


def parse(text):
    """The JSON object in the AI's answer (models sometimes wrap it in words or code fences)."""
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        out = json.loads(text[start:end + 1])
    except ValueError:
        return None
    if not isinstance(out, dict) or not (isinstance(out.get("say"), str) or out.get("do")):
        return None
    out["say"] = out.get("say") if isinstance(out.get("say"), str) else ""
    return out


VERBS = ("open", "review", "rematch", "next", "back", "prep", "guide")


def plain(do):
    """The AI's "do" in whatever shape it wrote it: {"review": 3}, "review 1853…", "review:3", "open settings",
    ["open", "settings"] or just "settings" (22 Oct test: a small model wrote "review 185351926500" and nothing
    opened). Returns a dict; everything is still checked by action()."""
    if isinstance(do, dict) and "do" in do:  # the whole answer: {"do": "open", "what": "settings"} (22 Oct)
        verb, what = str(do.get("do") or "").strip().lower(), do.get("what")
        if not verb or verb in ("none", "null", "nothing"):
            return None
        if isinstance(what, (dict, list)) or what in (None, ""):
            return plain(str(do["do"]))  # "review 111", "open settings", "next", or a bare "settings"
        if verb not in VERBS:  # {"do": "show", "what": "level"}: a page is a page; any other word is just talk
            return {"open": str(what).lower()} if str(what).lower() in PAGES else None
        return {verb: what}
    if isinstance(do, list) and do:
        do = do[0] if isinstance(do[0], (dict, str)) else None
    if isinstance(do, dict):
        return do
    if not isinstance(do, str) or not do.strip():
        return None
    text = do.strip().strip("{}").replace('"', "").replace("'", "")
    for sep in (":", "=", " ", "/"):
        if sep in text:
            verb, arg = (x.strip() for x in text.split(sep, 1))
            return {verb.lower(): arg}
    return {"open": text.lower()} if text.lower() in PAGES else {text.lower(): True}


def find_game(ref, games):
    """The game the AI meant: its number in the list (1 = the last), its id, or the opponent's name."""
    if isinstance(ref, bool) or ref is None:
        return None
    ref = str(ref).strip().lstrip("#")
    for g in games:
        if g["id"] == ref:
            return g
    if ref.isdigit() and 1 <= int(ref) <= len(games):
        return next((g for g in games if g.get("n") == int(ref)), games[int(ref) - 1])
    return next((g for g in games if g["opponent"].lower() == ref.lower()), None)


NAMES = {"home": "Home", "games": "your games", "practice": "Practice", "daily": "today's five minutes",
         "plan": "your plan", "progress": "your progress", "openings": "your openings", "settings": "Settings",
         "level": "your level", "endgames": "the endgame trainer", "prep": "prep", "course": "your course"}


def confirm(done, games):
    """What the coach says when the AI did something but forgot to say so (never a random line instead)."""
    route = done.get("route") or ""
    g = next((g for g in games if route.count("/") and g["id"] == route.split("/")[1]), None)
    if route.startswith("games/") and g:
        return f"Here's your game against {g['opponent']}, {g['date']}."
    if route.startswith("rematch/") and g:
        return f"Let's replay your game against {g['opponent']} from where it went wrong."
    if route.startswith("prep/"):
        return f"Here's how {route[5:]} plays."
    if route in NAMES:
        return f"Here's {NAMES[route]}."
    return "Here's the next step." if done.get("next") else "Here it is again." if done.get("back") else "Follow the red ring."


def action(do, games, where):
    """The checked action: {"route": ...} for the app, {"next": True}, or None when it isn't allowed."""
    do = plain(do)
    if not isinstance(do, dict):
        return None
    if str(do.get("open", "")).lower() in PAGES:
        return {"route": PAGES[str(do["open"]).lower()]}
    if "review" in do and find_game(do["review"], games):
        return {"route": f"games/{find_game(do['review'], games)['id']}"}
    if "rematch" in do and find_game(do["rematch"], games):
        g = find_game(do["rematch"], games)
        detail = insights.extras_for(g["id"]).get("rematch") if g["result"] != "win" else None
        return {"route": f"rematch/{g['id']}/{detail['ply']}"} if detail else None
    # next / back: whatever the AI wrote after the word ("next": "step", "move"…) (22 Oct test: "Next." was refused)
    if "next" in do and do["next"] not in (False, None, "none") and (where or {}).get("section") == "review":
        return {"next": True}
    if "back" in do and do["back"] not in (False, None, "none") and (where or {}).get("section") == "review":  # 22 Oct: going back says it again
        return {"back": True}
    if do.get("guide") in coaches.ROUTES and (where or {}).get("chesscom"):  # the red ring, on chess.com only
        return {"guide": coaches.guide(do["guide"])["guide"]}
    who = str(do.get("prep", "")).strip().lower()  # any chess.com player (19 Oct: "I can't find that game")
    if who and len(who) <= 30 and all(c.isalnum() or c in "-_" for c in who):
        return {"route": f"prep/{who}"}
    return None


def this_move(where):
    """In a review: the move on screen, as the engine and the review see it (its words, label, the better move, the key
    moment), so the coach answers about it from facts (22 Oct test: "why was that bad?" got a stock line)."""
    where = where or {}
    if where.get("section") != "review" or not where.get("game") or not str(where.get("ply", "")).isdigit():
        return {}
    try:
        d = insights.game_detail(where["game"])
        p = int(where["ply"])
        if not d or not 0 < p <= len(d.get("narration") or []):
            return {}
        m = d["narration"][p - 1]
        out = {"the_move_on_screen": {"move_number": d["move_numbers"][p - 1], "san": d["positions"][p]["san"],
                                      "by": "the player" if m["mine"] else "the opponent", "label": m["label"],
                                      "what_happened": m["text"]}}
        k = next((k for k in d.get("key_moments") or [] if k["ply"] == p), None)
        if k:
            out["the_move_on_screen"]["key_moment"] = [s["text"] for s in k["steps"]] + ([k["hard"]] if k.get("hard") else [])
        return out
    except Exception:
        return {}


def reply(coach, said, history=(), where=None, home=None, ask_ai=None, games=None):
    """{text, mood, ai, action}. Never fails: without a working AI, a written reply and no action."""
    from coach import ai
    coach = coach if coach in coaches.COACHES else coaches.COACH
    home = home if home is not None else insights.home()
    games = games if games is not None else recent_games()
    fallback = coaches.chat(coach, said, history, home=home, ask_ai=lambda *a: (_ for _ in ()).throw(ai.NoKey()))
    fallback["action"] = None
    facts = {"player": coaches.player_card(home), "recent_games": games, "where_the_player_is": where or {},
             "level": level_now(), "next_lesson": next_lesson(), "knightwise": ABOUT,
             "all_games": {"checked": home.get("games"), "results": home.get("results")}}
    facts.update(this_move(where))
    facts_text = json.dumps(facts)
    system = (ai.COACH_RULES.format(rating=home.get("rating") or "unknown") + coaches.PERSONA[coach] + RULES)
    name = coaches.COACHES[coach]["name"]
    turns = "".join(f"{'Player' if who == 'player' else name}: {text}\n" for who, text in list(history)[-6:])
    prompt = f"Facts:\n{facts_text}\n\n{turns}Player: {str(said)[:500]}\n{name} (JSON):"
    try:
        text, _provider = (ask_ai or ai.complete)(system, prompt, 400)
    except ai.NoKey:  # no key: the written sentences, as before
        return fallback
    except Exception:  # keys busy (the free limits) or down: say so plainly, never a stock line that ignores them (22 Oct)
        return {"text": BUSY, "mood": "calm", "ai": False, "action": None}
    out = parse(text or "")
    if not out or not coaches.grounded(out["say"], facts_text):
        return fallback
    order = out if "what" in out or isinstance(out.get("do"), str) else out.get("do")  # flat (do, what) or the old shapes
    done = action(order, games, where)
    wanted = plain(order) if isinstance(plain(order), dict) else {}
    if not done and next(iter(wanted), None) in VERBS:  # it meant to do something and wrote it wrong: once more, told why
        again = None
        try:
            note = (f"\nYour answer {json.dumps(out)[:300]} could not be done: \"what\" must be a page from the list, a "
                    "game's n from recent_games, a chess.com username or a place. Answer again, JSON only.\n")
            again = parse((ask_ai or ai.complete)(system, prompt + note, 400)[0] or "")
        except Exception:
            pass
        if again and coaches.grounded(again["say"], facts_text):
            order2 = again if "what" in again or isinstance(again.get("do"), str) else again.get("do")
            if action(order2, games, where) or not wanted:
                out, order, done = again, order2, action(order2, games, where)
    if not out["say"].strip():  # it did something and forgot to say what: say it, from what was done
        if not done:
            return fallback
        out["say"] = confirm(done, games)
    if done and done.get("route"):  # who the player meant: the hearing expects that name next time (flagship 6)
        from coach import heard
        route = done["route"]
        if route.startswith("prep/"):
            heard.learn(route[5:])
        elif route.startswith(("games/", "rematch/")):
            g = next((g for g in games if g["id"] == route.split("/")[1]), None)
            if g:
                heard.learn(g["opponent"])
    asked = plain(order) if isinstance(plain(order), dict) else {}
    verb = next((k for k in REFUSED if k in asked), next(iter(asked), None))
    # it asked for something that can't be done: say so, never "Opening it." with nothing opening (19 and 22 Oct)
    say = (REFUSED.get(verb, OPEN_FAILED) if verb and done is None else out["say"].strip())[:600]
    offered = None if done else action(out.get("offer"), games, where)  # her suggestion, for a "Show me" button
    if offered and not offered.get("route"):
        offered = None
    return {"text": say, "mood": "pleased" if "!" in say else "calm", "ai": True, "action": done, "offer": offered}
