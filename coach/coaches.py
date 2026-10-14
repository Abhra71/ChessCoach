"""Your two coaches, on chess.com and in Knightwise: Maya and Viktor. What they say, and where.

13 Oct 2026: two coaches instead of four, the player's choice ("that voice was the best", and they like Viktor too).
Maya: home, games and reviews, practice and puzzles. Viktor: your progress, your plan and lessons. One brain
(Stockfish + our facts); each always shows up for the same sections, so nothing to pick.
Written sentences work for everyone, offline; with an AI key she replies in conversation.
Fair play: nothing here looks at a game being played; the extension hides her wherever one could be running.
"""
import random
import time

from coach import insights

PUZZLES = "https://www.chess.com/puzzles/rated"
BOTS = "https://www.chess.com/play/computer"
LESSONS = "https://www.chess.com/lessons"

COACHES = {
    "maya": {"role": "Your games and practice", "name": "Maya", "voice": "af_heart",
             "about": "Former champion. Calm, patient, clear.", "sections": ["home", "play", "review", "games", "puzzles"]},
    "viktor": {"role": "Your progress and plan", "name": "Viktor", "voice": "am_michael",
               "about": "Veteran. Wise, dry humour, has seen it all.", "sections": ["progress", "lessons", "plan"]},
}
COACH = "maya"  # where no section says otherwise
AI_HINT = "Want real replies? Add a free AI key in Knightwise Settings. It takes 2 minutes."
SECTION_COACH = {s: c for c, info in COACHES.items() for s in info["sections"]}

# the focus habit in a few words
SHORT = {
    "left a piece hanging": "keeping every piece safe",
    "missed a free capture": "spotting the free piece they leave you",
    "walked into a fork or trick": "checking their forks and checks before you move",
    "walked into checkmate": "looking for their checks before every move",
    "missed a checkmate": "looking for checkmate when you attack",
    "stalemated a won game": "giving the king a square when you're winning",
}

# What each coach says, a few ways each; a kind with only Maya's words is said by Maya's words. {name}, {habit}, {lately}, {before}, {moments}... are filled in.
SAY = {
    "hello": {"maya": ["{greet}, {name}. Good to see you.", "{greet}, {name}. Let's take it one move at a time today."],
              "viktor": ["Ah, {name}. {greet}.", "{greet}, {name}. Sit down, let's look at how you're doing."]},
    "better": {"maya": ["You're giving away fewer pieces: {lately} a game, down from {before}. That's real progress."],
               "viktor": ["{lately} pieces a game, down from {before}. I've seen worse progress from grandmasters."]},
    "worse": {"maya": ["You've lost a few more pieces lately, {lately} a game, up from {before}. No worry, we'll slow down and fix it."],
              "viktor": ["{lately} pieces a game lately. Everyone has a bad week. Even me, once, in 1987."]},
    "focus": {"maya": ["Today, let's work on {habit}. {tip}"], "viktor": ["The lesson for today is {habit}. {tip}"]},
    "review": {"maya": ["I found {moments} in this game. Click one and I'll show you on the board.",
                        "{moments} decided this game. Let's look at them together, calmly."]},
    "review_clean": {"maya": ["A clean game: no big mistakes for me to show you. Well played."]},
    "unknown_game": {"maya": ["I haven't checked this game yet. Once it's finished and saved, I'll go through it with you."]},
    "puzzles": {"maya": ["Puzzles. Before every move, ask what they can take.",
                         "Warm-up time. Look for checks, captures and threats, in that order."]},
    "progress": {"viktor": ["You've played {games} games with me watching. Let's see what's changed."]},
    "week_better": {"viktor": ["This week: {this_games} games, {this_pieces} pieces given away. Last week it was {last_pieces} in "
                               "{last_games}. That is how improvement looks."]},
    "week_same": {"viktor": ["This week: {this_games} games, {this_pieces} pieces given away; last week {last_pieces} in "
                             "{last_games}. Steady. Now let's make it better."]},
    "week_none": {"viktor": ["No games this week yet. A game a day keeps the rust away, as I always say. Well, I say it now."]},
    "lessons": {"viktor": ["Lessons are good. But the best teacher is your own last game. Remember that."]},
    "games": {"maya": ["Pick a game and I'll show you the moments that decided it.",
                       "Every game has one or two moments that matter. Choose one and let's find them."]},
    "plan": {"viktor": ["Here's your plan: one opening, one tactic, one idea, one endgame. Pick one and we start.",
                      "Not a pile of homework. Four things, chosen for you. Start with whichever you like."]},
    "play": {"maya": ["Pick a bot near your level and play it like a real game. I'll stay quiet until it's over."]},
    "no_player": {"maya": ["Hi, I'm Maya, your Knightwise coach. Open the Knightwise app and tell me your chess.com name."]},
}


def mood(home):
    """pleased: giving away fewer pieces lately; worried: more; else calm. Drives the coach's face."""
    before, lately = home.get("pieces_per_game") or 0, home.get("pieces_last20") or 0
    if not home.get("games") or not before:
        return "calm"
    if lately <= before * 0.8:
        return "pleased"
    if lately >= before * 1.2:
        return "worried"
    return "calm"


def part_of_day(hour):
    return "Good morning" if 5 <= hour < 12 else "Good afternoon" if 12 <= hour < 18 else "Good evening"


def line(kind, coach, rng=random, **facts):
    """One sentence of this kind in this coach's words (any coach's if they have none of their own)."""
    options = SAY[kind].get(coach) or next(iter(SAY[kind].values()))
    return rng.choice(options).format(**facts)


AGAIN = ["Back again. Here's where we are.", "Good, you're back.", "Picking up where we were."]


def speak(section, home=None, hour=12, moments=None, rng=random, extra=None, again=False, in_app=False):
    """again: a second visit to this section today, so no full welcome again, just where things stand (13 Oct test:
    "welcoming is an art"; the coach was greeting every time, then folding silently)."""
    said = _speak(section, home, hour, moments, rng, extra, in_app)
    if again and said.get("lines") and section != "review":
        lines = said["lines"]
        keep = [lines[-1]] if lines[-1].startswith("My pick") else lines[1:2]  # where things stand, in one line
        said = {**said, "lines": [rng.choice(AGAIN)] + keep, "again": True}
    return said


def _speak(section, home=None, hour=12, moments=None, rng=random, extra=None, in_app=False):
    """What the coach of this section says: {coach, name, voice, mood, lines, actions}.
    moments: for a game review, the number of key moments (None = a game the coach doesn't know).
    extra: {"novelty": the new thing from coach/plan.py, "advice": a do-this-not-that line} for the home section."""
    coach = SECTION_COACH.get(section, COACH)
    home = home if home is not None else insights.home()
    info = COACHES[coach]
    out = {"coach": coach, "name": info["name"], "voice": info["voice"], "mood": "calm", "lines": [], "actions": []}
    player = home.get("player")
    if not player:
        out["lines"] = [line("no_player", COACH, rng)]
        return out
    face = mood(home)
    facts = {"name": player, "greet": part_of_day(hour), "lately": round(home.get("pieces_last20") or 0, 1),
             "before": round(home.get("pieces_per_game") or 0, 1), "games": home.get("games")}
    focus = home.get("focus")
    if focus:
        facts.update(habit=SHORT.get(focus["pattern"], focus["pattern"]), tip=focus["habit"])
    lines = [line("hello", coach, rng, **facts)]

    if section == "review":
        if moments is None:
            return {**out, "mood": "thinking", "lines": [line("unknown_game", coach, rng)]}
        face = "pleased" if moments == 0 else "calm"
        words = f"{moments} key moment" + ("" if moments == 1 else "s")
        lines = [line("review_clean" if moments == 0 else "review", coach, rng, moments=words, **facts)]
    elif section == "puzzles":
        lines.append(line("puzzles", coach, rng, **facts))
        out["actions"], why = recommend(section, home, actions=[], in_app=in_app)
        if why:
            lines.append(why)
    else:
        if face == "pleased":
            lines.append(line("better", coach, rng, **facts))
        elif face == "worried":
            lines.append(line("worse", coach, rng, **facts))
        if section == "home" and extra and extra.get("novelty"):  # something new, when it's genuinely needed
            n = extra["novelty"]
            lines.append(f"Something new for you: {n['title'].lower() if n['kind'] != 'opening' else n['title']}. {n.get('why') or ''}".strip())
            out["actions"] = [{"label": "Learn it in Knightwise", "app": "plan", "best": True,
                               "why": "It's new for you, and it fits your habit."}] + suggestions(home)[:1] + [OPEN_APP]
            return {**out, "mood": "pleased", "lines": lines}
        if section == "home" and extra and extra.get("advice"):
            lines.append(extra["advice"])
            out["actions"], why = recommend(section, home, in_app=in_app)
            return {**out, "mood": face, "lines": lines + ([why] if why else [])}
        if section == "progress":  # the weekly memory instead of the general line: three sentences at most
            lines.append(week_line(home, coach, rng))
        elif section == "plan" and extra and extra.get("novelty"):
            n = extra["novelty"]
            lines.append(f"But first, something new: {n['title']}. {n.get('why') or ''}".strip())
        elif section in ("lessons", "play", "games", "plan"):
            lines.append(line(section, coach, rng, **facts))
        elif focus:
            lines.append(line("focus", coach, rng, **facts))
        if section not in ("games", "plan"):
            out["actions"], why = recommend(section, home, in_app=in_app)
            if why:
                lines.append(why)
    return {**out, "mood": face, "lines": lines}


def week_line(home, coach, rng=random):
    """The progress coach remembers: this week against last week."""
    w = home.get("week") or {}
    this, last = w.get("this") or {}, w.get("last") or {}
    if not this.get("games"):
        return line("week_none", coach, rng)
    facts = {"this_games": this["games"], "this_pieces": this["pieces"], "last_games": last.get("games", 0),
             "last_pieces": last.get("pieces", 0)}
    per = lambda d: d["pieces"] / d["games"] if d.get("games") else None
    better = last.get("games") and per(this) < per(last)
    return line("week_better" if better else "week_same", coach, rng, **facts)


OPEN_APP = {"label": "Open Knightwise", "app": "home"}
# chess.com's home, before you play: three positions from your own games in the coach's box (extension/buddy.js)
WARMUP = {"label": "Warm up here: 3 positions", "warmup": True,
          "why": "Three positions from your own games, right here, in about two minutes. Then play."}


HERE = {"home": "home", "puzzles": "practice", "progress": "progress", "lessons": "plan", "plan": "plan"}  # app pages


def recommend(section, home, actions=None, now=None, in_app=False):
    """The coach's pick of where to practise, and why: chess.com for what it's best at (a warm-up, the review on its
    board right after a game), Knightwise for your own positions and your plan (13 Oct test: "no preference from the
    coach, where to practise what"). Returns (actions with the pick first and marked, the line that says why).
    Open Knightwise is always there: the way back to the app from chess.com."""
    actions = list(actions if actions is not None else suggestions(home))
    focus, daily, last = home.get("focus"), home.get("daily") or {}, home.get("last_game") or {}
    habit = SHORT.get(focus["pattern"], focus["pattern"]) if focus else None
    pick = None
    fresh = (last.get("moments") and "/game/" in last.get("url", "")
             and (now or time.time()) - last.get("end_time", 0) < 86400)  # a game from today
    if section == "home" and not in_app and daily and not fresh:  # on chess.com, before you play: warm up right there
        pick = dict(WARMUP)
        if not daily.get("done_today"):
            actions.insert(0, {"label": "Today's 5 minutes in Knightwise", "app": "daily"})
    elif section in ("home", "puzzles") and daily and not daily.get("done_today") and not (section == "home" and fresh and not in_app):
        pick = {"label": "Today's 5 minutes in Knightwise", "app": "daily",
                "why": "It's built from your own games, so it trains exactly the moves you get wrong."}
    elif section == "home" and fresh:  # a game from today: review it while it's fresh
        pick = next((a for a in actions if a.get("url") == last["url"]), None)
        if pick and in_app and last.get("id"):  # in Knightwise: its own review, with Try it again
            actions = [a for a in actions if a is not pick]
            pick = {"label": pick["label"], "app": f"games/{last['id']}",
                    "why": "Go through it now, while you still remember the game."}
        elif pick:
            pick = {**pick, "why": "Look at it on chess.com's own board now, while you still remember the game."}
    elif section == "puzzles" and habit:
        pick = {"label": "Practise your habit in Knightwise", "app": "practice",
                "why": f"These puzzles come from other people's games. Your own positions train exactly this: {habit}."}
    elif section == "progress":
        pick = {"label": "Your progress in Knightwise", "app": "progress",
                "why": "It shows you against yourself, on the habit you're fixing, game by game."}
    elif section == "lessons":
        pick = {"label": "Your plan in Knightwise", "app": "plan",
                "why": "It picks the lesson that fixes your habit, instead of a general one."}
    if in_app and pick and (pick.get("app") == HERE.get(section) or (section == "puzzles" and pick.get("app") == "daily")):
        pick = None  # in Knightwise already, on that very page: no "open what you're looking at"
    if pick is None and actions:
        pick = {**actions[0], "why": "A few puzzles on chess.com: a quick warm-up before you play." if in_app
                else "A few puzzles here first: a quick warm-up before you play."}
    if section == "home" and not in_app and daily and not (pick and pick.get("warmup")):  # the warm-up is always there
        actions = [WARMUP] + [a for a in actions if a.get("url") != PUZZLES]
    actions = [a for a in actions if not pick or (a.get("label"), a.get("app")) != (pick.get("label"), pick.get("app"))]
    if pick:
        actions.insert(0, {**pick, "best": True})
    actions = actions[:3]
    if not in_app and not any(a.get("app") for a in actions):
        actions = actions[:2] + [OPEN_APP]  # always the way back into Knightwise
    said = f"My pick: {pick['label']}. {pick['why']}" if pick else None
    return actions, said


def suggestions(home):
    """One or two things to do next, as links on chess.com (the player clicks; we never click for them)."""
    # find: the coach can point at chess.com's own link (red ring) and check the player clicked it
    actions = [{"label": "Warm up with puzzles", "url": PUZZLES, "find": {"path": "/puzzles", "name": "Puzzles"}}]
    last = home.get("last_game")
    if last and last.get("moments") and "/game/live/" in last["url"]:  # daily/bot addresses can point elsewhere
        actions.append({"label": f"Review your game vs {last['opponent']}", "url": last["url"]})
    elif last and last.get("moments") and home.get("player"):
        actions.append({"label": "Review your recent games", "url": f"https://www.chess.com/games/archive/{home['player']}"})
    else:
        actions.append({"label": "Play a bot at your level", "url": BOTS})
    return actions


# ---------- talking with a coach (needs the player's own free AI key) ----------
PERSONA = {
    "maya": "You are Maya, a calm former women's world champion, about 35, and this player's only coach. Patient, warm, "
            "clear; short calm sentences.",
    "viktor": "You are Viktor, a 60-year-old veteran coach, one of this player's two coaches. Wise, kind, with dry "
              "humour; you have seen everything.",
}
# when the AI can't answer (no key, busy, down, or it said something the facts don't back up): still a warm reply
FALLBACK = {
    "maya": ["Let me keep this simple for now: {tip}", "Here's what matters most today: {tip}"],
    "viktor": ["The old advice still works: {tip}", "Let me give you the one lesson I'd give anyone: {tip}"],
}
SQUARE = __import__("re").compile(r"\b[a-h][1-8]\b")


def player_card(home):
    """The short card the AI gets about the player: engine facts only, never a game being played."""
    focus = home.get("focus") or {}
    last = home.get("last_game") or {}
    return {"name": home.get("player"), "rating": home.get("rating"), "games_checked": home.get("games"),
            "results": home.get("results"), "main_habit_to_fix": focus.get("pattern"), "habit_tip": focus.get("habit"),
            "pieces_given_away_per_game": home.get("pieces_per_game"), "lately_last_20_games": home.get("pieces_last20"),
            "other_patterns": home.get("patterns"),
            "last_game": {k: last.get(k) for k in ("date", "result", "opponent", "opponent_rating", "pieces_lost", "moments")}
            if last else None}


def grounded(text, facts_text):
    """Every square the AI names must appear in the facts it was given (Stockfish decides the chess, not the AI)."""
    return all(sq in facts_text for sq in SQUARE.findall(text))


def chat(coach, message, history=(), home=None, extra=None, ask_ai=None, rng=random):
    """The coach's reply: {text, mood, ai}. Never fails: without a working AI it answers with written words."""
    import json

    from coach import ai
    coach = coach if coach in COACHES else COACH
    home = home if home is not None else insights.home()
    focus = home.get("focus") or {}
    tip = focus.get("habit") or "Before every move, ask: what can they take, and is every piece of mine safe?"
    fallback = {"text": rng.choice(FALLBACK[coach]).format(tip=tip), "mood": "calm", "ai": False}
    ask_ai = ask_ai or ai.complete
    facts = {"player": player_card(home), **(extra or {})}
    facts_text = json.dumps(facts)
    system = (ai.COACH_RULES.format(rating=home.get("rating") or "unknown") + PERSONA[coach] +
              " Stay in character. Reply in at most 3 short sentences, like a real conversation. Only talk about chess and "
              "this player's games; never give advice about a game being played right now. The facts are all you know.")
    turns = "".join(f"{'Player' if who == 'player' else COACHES[coach]['name']}: {said}\n" for who, said in list(history)[-6:])
    prompt = f"Facts:\n{facts_text}\n\n{turns}Player: {str(message)[:500]}\n{COACHES[coach]['name']}:"
    try:
        text, _provider = ask_ai(system, prompt, 300)
    except Exception:  # no key, both providers busy or down: the conversation still goes on
        return fallback
    text = (text or "").strip()
    if not text or not grounded(text, facts_text):
        return fallback
    return {"text": text[:700], "mood": "pleased" if "!" in text else "calm", "ai": True}


# ---------- what to do and what not to do today (from the player's own data) ----------
def advice(games, moves, player, now=None):
    """One 'do this, not that' line, or None: a losing streak today, or a time control that costs pieces."""
    import collections
    import time

    from coach.review import LOSING_MATERIAL
    now = now or time.time()
    today = [g for g in games if now - g["end_time"] < 12 * 3600]  # newest first
    streak = 0
    for g in today:
        if insights._result(g, insights._side(g, player)[0]) != "loss":
            break
        streak += 1
    if streak >= 3:
        return f"You've lost {streak} in a row today. Take a 10-minute break, then review the last one before you play again."
    by = collections.defaultdict(lambda: [0, 0])
    for g in games:
        if g["url"] in moves and g["time_class"] != "daily":
            by[g["time_class"]][0] += sum(1 for r in moves[g["url"]] if r.get("pattern") in LOSING_MATERIAL)
            by[g["time_class"]][1] += 1
    rates = {tc: lost / n for tc, (lost, n) in by.items() if n >= 8}
    if len(rates) < 2:
        return None
    worst, best = max(rates, key=rates.get), min(rates, key=rates.get)
    if rates[worst] >= 1.5 * rates[best] and worst != best:
        return (f"Skip {worst} for now: you give away {rates[worst]:.1f} pieces a game there, "
                f"{rates[best]:.1f} in {best}.")
    return None
