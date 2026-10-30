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
    "The facts are all you know. Reply ONLY with JSON, five fields: "
    "{\"do\": \"<one of the words below, or none>\", \"what\": \"<what it applies to>\", \"say\": \"what you say\", "
    "\"offer\": \"<what you suggest next, as a do and a what, like open practice or review 1, or none>\", "
    "\"asked\": \"order when they told you to do something, yes when they agreed to your last suggestion, talk for "
    "anything else, questions included\"}. "
    "You are their coach, not a tool: when it helps, suggest the one next thing worth doing and put it in offer, so they "
    "can press it; offer never does it by itself. When they ask what to do, what to work on or what you suggest, do is "
    "none and your suggestion goes in offer. Whenever say suggests something the app has (practice, daily, a game's "
    "review, the course, Train, the plan), offer names it, every time: a coach points at what she suggests. A question about an opening offers openings (their own opening tree), not practice. When they say yes, ok or please do to your last suggestion, do it. "
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
    "When they want something on chess.com (its puzzles, bots, lessons, their game history there), do is guide, "
    "even in the app: Knightwise's own practice is not chess.com. "
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
    "prep": "Tell me their exact chess.com username, and I'll get you ready for them.",
}
BUSY = "Give me a minute, I'm thinking too slowly right now. Ask me again in a moment."
KEY_REFUSED = "My AI key was refused. Check it in Settings: it may be mistyped or switched off."
NO_NET = "I can't reach my AI right now. Check your internet, then ask me again."


def why_not(error):
    """The coach's line for an AI that didn't answer: a refused key, no internet, or busy (cloud review, 26 Oct)."""
    parts = [p for p in str(error).split("; ") if p and not p.endswith(": resting")]
    if parts and all(any(code in p for code in ("HTTP 400", "HTTP 401", "HTTP 403")) for p in parts):
        return KEY_REFUSED
    if parts and all(any(w in p.lower() for w in ("urlopen error", "getaddrinfo", "timed out", "10061", "11001"))
                     for p in parts):
        return NO_NET
    return BUSY
OPEN_FAILED = "I can't open that from here. Tell me which page, like your games, Practice or Settings."


ENDED = {"checkmated": "checkmate", "resigned": "resigned", "timeout": "ran out of time", "abandoned": "left the game",
         "stalemate": "draw by stalemate", "agreed": "draw by agreement", "repetition": "draw by repetition",
         "insufficient": "draw: not enough pieces to mate", "50move": "draw by the 50-move rule",
         "timevsinsufficient": "draw: time ran out but no mate was possible"}
VALUE = {1: 1, 2: 3, 3: 3, 4: 5, 5: 9}  # pawn, knight, bishop, rook, queen


def ended(g):
    """How the game ended, in words and from the player's side: "they resigned", "you ran out of time"."""
    how = ENDED.get(g.get("how"), g.get("how") or "")
    if how.startswith("draw"):
        return how
    who = "they" if g.get("result") == "win" else "you"
    return f"{who} were checkmated" if how == "checkmate" else f"{who} {how}"


def last_game_detail(g):
    """For the last game, what a coach would look at to explain it (30 Oct test: "why did my opponent resign the
    last game" got "I don't have the engine details for that game"): the material at the end and its key moments."""
    import io
    import chess.pgn
    out = {}
    try:
        raw = next((x for x in insights._games() if x["url"] == g["url"]), None)
        board = chess.pgn.read_game(io.StringIO(raw["pgn"])).end().board()
        side = chess.WHITE if g["color"] == "white" else chess.BLACK
        count = lambda c: sum(VALUE.get(p.piece_type, 0) for p in board.piece_map().values() if p.color == c)
        diff = count(side) - count(not side)
        out["material_at_the_end"] = ("level" if not diff else
                                      f"you were {abs(diff)} points {'ahead' if diff > 0 else 'behind'} (pawn 1, knight or bishop 3, rook 5, queen 9)")
        out["position_at_the_end"] = board.fen()
    except Exception:  # the facts are a help, never a reason for no answer
        pass
    try:
        from coach import service
        rows = insights._moves().get(g["url"], [])
        out["key_moments"] = [{"move": m.get("move_number"), "say": m.get("say")}
                              for m in service.key_moments(rows, g["id"])][:3]
    except Exception:
        pass
    return out


def recent_games(n=RECENT):
    """The player's last games as the coach may name them: id, opponent, result, how it ended, date, key moments;
    the last game in more detail."""
    rows = [g for g in insights.games_list() if g.get("checked")][:n]
    games = [{**{k: g.get(k) for k in ("id", "opponent", "opponent_rating", "result", "date", "time_class", "opening",
                                       "moves", "pieces_lost", "moments")}, "ended": ended(g)} for g in rows]
    if rows:
        games[0].update(last_game_detail(rows[0]))
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
        return {"id": row["id"], "title": row["title"], "why": course.reason(row), "habit": row["habit"]} if row else None
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
    if do.get("guide") in coaches.ROUTES:  # in the app: that chess.com page opens in their browser (23 Oct test)
        return {"web": coaches.ROUTES[do["guide"]]["url"]}
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


def this_line(where):
    """On the opening tree: the line on screen, from the player's own checked games (24 Oct test: "why do I lose from
    this line?" got a guess). What they scored, which mistakes they made in those games and when, what came next."""
    import collections
    import io
    import chess.pgn
    where = where or {}
    line, side = str(where.get("line", "")).split(), where.get("side")
    if where.get("section") != "openings" or not line or side not in ("white", "black"):
        return {}
    try:
        player = (insights._player() or "").lower()
        moves = insights._moves()
        hits, nxt_theirs, nxt_mine = [], collections.Counter(), collections.Counter()
        for g in insights._games():
            if insights._side(g, player)[0] != side:
                continue
            game = chess.pgn.read_game(io.StringIO(g.get("pgn") or ""))
            if not game:
                continue
            board, sans = game.board(), []
            for m in list(game.mainline_moves())[:len(line) + 1]:
                sans.append(board.san(m))
                board.push(m)
            if sans[:len(line)] != line:
                continue
            hits.append(g)
            if len(sans) > len(line):
                mine = (len(line) % 2 == 0) == (side == "white")  # whose move comes next
                (nxt_mine if mine else nxt_theirs)[sans[len(line)]] += 1
        if not hits:
            return {}
        res = collections.Counter(insights._result(g, side) for g in hits)
        habits, first_big = collections.Counter(), []
        for g in hits:
            rows = moves.get(g["url"], [])
            habits.update(r["pattern"] for r in rows if r.get("pattern") and r["pattern"] != "other")
            big = [r for r in rows if r["loss"] >= 25]
            if big:
                first_big.append((big[0]["ply"] + 1) // 2)
        first_big.sort()
        return {"this_line": {"line": " ".join(line), "you_are": side, "games": len(hits), "won": res["win"],
                              "drawn": res["draw"], "lost": res["loss"],
                              "your_mistakes_in_these_games": dict(habits.most_common(4)),
                              "games_with_a_big_mistake": len(first_big),
                              "first_big_mistake_move_typically": first_big[len(first_big) // 2] if first_big else None,
                              "what_they_play_next": dict(nxt_theirs.most_common(3)),
                              "what_you_play_next": dict(nxt_mine.most_common(3)),
                              "note": "Counted from the player's own checked games that went this way. Use these numbers."}}
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
    facts.update(this_line(where))
    facts_text = json.dumps(facts)
    system = (ai.COACH_RULES.format(rating=home.get("rating") or "unknown") + coaches.PERSONA[coach] + RULES)
    name = coaches.COACHES[coach]["name"]
    turns = "".join(f"{'Player' if who == 'player' else name}: {text}\n" for who, text in list(history)[-6:])
    prompt = f"Facts:\n{facts_text}\n\n{turns}Player: {str(said)[:500]}\n{name} (JSON):"
    try:
        text, _provider = (ask_ai or ai.complete)(system, prompt, 400)
    except ai.NoKey:  # no key: the written sentences, as before
        return fallback
    except Exception as e:  # keys busy (the free limits), refused or offline: say which, plainly (22 and 26 Oct)
        return {"text": why_not(e), "mood": "calm", "ai": False, "action": None}
    out = parse(text or "")
    if not out or not coaches.grounded(out["say"], facts_text):
        import logging  # what the AI wrote that couldn't be used, to see why (24 Oct: Gemini failed on "open my last review")
        logging.getLogger("knightwise").info("talk: unusable reply from %s: %r", _provider, (text or "")[:300])
        return fallback
    order = out if "what" in out or isinstance(out.get("do"), str) else out.get("do")  # flat (do, what) or the old shapes
    done = action(order, games, where)
    wanted = plain(order) if isinstance(plain(order), dict) else {}
    if not done and next(iter(wanted), None) in ("open", "review", "prep"):  # it meant to do something and wrote it
        # wrong: once more, told why. Not for next, back, guide or rematch: those were understood, just not possible here
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
    verb = next((k for k in REFUSED if k in asked), next((k for k in asked if k in VERBS), None))  # "talk": just talk
    # it asked for something that can't be done: say so, never "Opening it." with nothing opening (19 and 22 Oct)
    say = (REFUSED.get(verb, OPEN_FAILED) if verb and done is None else out["say"].strip())[:600]
    if done and done.get("route") and str(out.get("asked", "")).strip().lower() == "talk":
        done, out["offer"] = None, order  # a question gets a suggestion she points at, never a page opened (23 Oct test)
        if not out["say"].strip():
            return fallback
    offered = None if done else action(out.get("offer"), games, where)  # her suggestion: the menu item glows
    if not done and not offered and isinstance(out.get("offer"), str):  # "practice left a piece hanging": its page (23 Oct)
        first = (out["offer"].strip().lower().split() or [""])[0]
        offered = action({"open": first}, games, where) if first in PAGES else None
    if offered and not offered.get("route"):
        offered = None
    return {"text": say, "mood": "pleased" if "!" in say else "calm", "ai": True, "action": done, "offer": offered}
