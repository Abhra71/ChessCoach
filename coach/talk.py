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
         "endgames": "endgames", "prep": "prep"}
RECENT = 20  # the games the coach can find by name ("my game against X")

RULES = (
    " This is a spoken conversation: reply in at most 3 short sentences, easy to say out loud, with no lists and no "
    "symbols. Only talk about chess and this player's games; never give advice about a game being played right now. "
    "The facts are all you know. Reply ONLY with JSON: {\"say\": \"what you say\", \"do\": null} or with \"do\" one of: "
    "{\"open\": \"<page>\"} (pages: home, games, practice, daily, plan, progress, openings, settings, level: their level and what to work on next, endgames: the endgame trainer, prep: prep against an opponent), "
    "{\"review\": \"<game id>\"} to open the review of one of the games in the facts, "
    "{\"rematch\": \"<game id>\"} to replay a lost or drawn game from where it went wrong, "
    "{\"next\": true} to show the next step of the review on screen, "
    "{\"open\": \"level\"} for their level and what to work on. Ask for something only when the player wants it. "
    "If they name an opponent who isn't in the facts, say you can't find that game."
)


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
             "level": level_now()}
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
    return {"text": out["say"].strip()[:600], "mood": "pleased" if "!" in out["say"] else "calm", "ai": True,
            "action": action(out.get("do"), games, where)}
