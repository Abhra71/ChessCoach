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
RECENT = 20  # the games the coach can find by name ("my game against X")

RULES = (
    " This is a spoken conversation: reply in at most 3 short sentences, easy to say out loud, with no lists and no "
    "symbols. Only talk about chess and this player's games; never give advice about a game being played right now. "
    "The facts are all you know. Reply ONLY with JSON: {\"say\": \"what you say\", \"do\": null} or with \"do\" one of: "
    "{\"open\": \"<page>\"} (pages: home, games, practice, daily, plan, progress, openings, settings, level: their level and what to work on next, endgames: the endgame trainer, prep: prep against an opponent, course: their course and the next lesson), "
    "{\"review\": \"<game id>\"} to open the review of one of the games in the facts, "
    "{\"rematch\": \"<game id>\"} to replay a lost or drawn game from where it went wrong, "
    "{\"next\": true} to show the next step of the review on screen, "
    "{\"prep\": \"<chess.com username>\"} to prepare against any player before a game (their openings and how their "
    "games end), using a name from the facts when it sounds like one of them, "
    "{\"open\": \"level\"} for their level and what to work on, "
    "{\"guide\": \"<place>\"} to show them the way on chess.com with a red ring, step by step (places: puzzles, bots, "
    "archive: their game history on chess.com, lessons). Ask for something only when the player wants it. "
    "If they name an opponent who isn't in the facts, say you can't find that game. Never say you are opening, "
    "replaying or showing something unless \"do\" does it; if you can't do it from here, say what to open first."
)
REFUSED = {  # an action the coach asked for that isn't possible here: say so, never "let's replay it" and nothing (19 Oct)
    "rematch": "I can't start a rematch from here. Open a game you lost or drew, then say rematch.",
    "next": "Open a game's review first, then say next and I'll go through it step by step.",
    "review": "I can't find that game in your recent games.",
    "guide": "I show the way on chess.com itself. Open chess.com, ask me there, and I'll ring it for you.",
}


def recent_games(n=RECENT):
    """The player's last games as the coach may name them: id, opponent, result, date, key moments."""
    return [{k: g[k] for k in ("id", "opponent", "result", "date", "time_class", "moments")}
            for g in insights.games_list()[:n] if g.get("checked")]


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
    return out if isinstance(out, dict) and isinstance(out.get("say"), str) else None


def action(do, games, where):
    """The checked action: {"route": ...} for the app, {"next": True}, or None when it isn't allowed."""
    if not isinstance(do, dict):
        return None
    ids = {g["id"]: g for g in games}
    if do.get("open") in PAGES:
        return {"route": PAGES[do["open"]]}
    if str(do.get("review", "")) in ids:
        return {"route": f"games/{do['review']}"}
    if str(do.get("rematch", "")) in ids:
        g = ids[str(do["rematch"])]
        detail = insights.extras_for(g["id"]).get("rematch") if g["result"] != "win" else None
        return {"route": f"rematch/{g['id']}/{detail['ply']}"} if detail else None
    if do.get("next") is True and (where or {}).get("section") == "review":
        return {"next": True}
    if do.get("guide") in coaches.ROUTES and (where or {}).get("chesscom"):  # the red ring, on chess.com only
        return {"guide": coaches.guide(do["guide"])["guide"]}
    who = str(do.get("prep", "")).strip().lower()  # any chess.com player (19 Oct: "I can't find that game")
    if who and len(who) <= 30 and all(c.isalnum() or c in "-_" for c in who):
        return {"route": f"prep/{who}"}
    return None


def reply(coach, said, history=(), where=None, home=None, ask_ai=None, games=None):
    """{text, mood, ai, action}. Never fails: without a working AI, a written reply and no action."""
    from coach import ai
    coach = coach if coach in coaches.COACHES else coaches.COACH
    home = home if home is not None else insights.home()
    games = games if games is not None else recent_games()
    fallback = coaches.chat(coach, said, history, home=home, ask_ai=lambda *a: (_ for _ in ()).throw(ai.NoKey()))
    fallback["action"] = None
    facts = {"player": coaches.player_card(home), "recent_games": games, "where_the_player_is": where or {},
             "level": level_now(), "next_lesson": next_lesson()}
    facts_text = json.dumps(facts)
    system = (ai.COACH_RULES.format(rating=home.get("rating") or "unknown") + coaches.PERSONA[coach] + RULES)
    name = coaches.COACHES[coach]["name"]
    turns = "".join(f"{'Player' if who == 'player' else name}: {text}\n" for who, text in list(history)[-6:])
    prompt = f"Facts:\n{facts_text}\n\n{turns}Player: {str(said)[:500]}\n{name} (JSON):"
    try:
        text, _provider = (ask_ai or ai.complete)(system, prompt, 400)
    except Exception:  # no key, both busy or down: the conversation still goes on
        return fallback
    out = parse(text or "")
    if not out or not out["say"].strip() or not coaches.grounded(out["say"], facts_text):
        return fallback
    done = action(out.get("do"), games, where)
    if done and done.get("route"):  # who the player meant: the hearing expects that name next time (flagship 6)
        from coach import heard
        route = done["route"]
        if route.startswith("prep/"):
            heard.learn(route[5:])
        elif route.startswith(("games/", "rematch/")):
            g = next((g for g in games if g["id"] == route.split("/")[1]), None)
            if g:
                heard.learn(g["opponent"])
    asked = next((k for k in REFUSED if isinstance(out.get("do"), dict) and k in out["do"]), None)
    say = REFUSED[asked] if asked and done is None else out["say"].strip()[:600]
    return {"text": say, "mood": "pleased" if "!" in say else "calm", "ai": True, "action": done}
