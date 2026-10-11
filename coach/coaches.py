"""The four coaches on chess.com: who appears where, and how each one says things.

All four share one brain (Stockfish + our facts). They differ only in face, voice and wording, and each always shows up
for the same sections, so it feels like a specialist. Nothing to pick, nothing to switch.
Written sentences work for everyone, offline; an AI key (later) lets the same coach reply in conversation.
Fair play: nothing here looks at a game being played; the extension hides the coaches wherever one could be running.
"""
import random

from coach import insights

PUZZLES = "https://www.chess.com/puzzles/rated"
BOTS = "https://www.chess.com/play/computer"
LESSONS = "https://www.chess.com/lessons"

COACHES = {
    "maya": {"role": "Game reviews", "name": "Maya", "voice": "bf_emma", "about": "Former champion. Calm, patient, strategic.",
             "sections": ["review"]},
    "arjun": {"role": "Puzzles and practice", "name": "Arjun", "voice": "am_puck", "about": "Young prodigy. Quick, energetic, loves tactics.",
              "sections": ["puzzles"]},
    "zara": {"role": "Before you play", "name": "Zara", "voice": "af_nova", "about": "Attacking player. Direct, bold, competitive.",
             "sections": ["home", "play"]},
    "viktor": {"role": "Progress and lessons", "name": "Viktor", "voice": "bm_george", "about": "Veteran. Wise, dry humour, has seen it all.",
               "sections": ["progress", "lessons"]},
}
AI_HINT = ("Want to talk with your coaches and get replies? Add a free AI key in Knightwise, Settings "
           "(about 2 minutes, step by step).")
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

# Each coach says the same thing in their own way. {name}, {habit}, {lately}, {before}, {moments}... are filled in.
SAY = {
    "hello": {
        "maya": ["{greet}, {name}. Good to see you.", "{greet}, {name}. Let's take it one move at a time today."],
        "arjun": ["Hey {name}! Ready to crush some puzzles?", "{name}! Let's go, I've got good ones for you today."],
        "zara": ["{greet}, {name}. Let's win some games.", "{name}, you're here. Good. Let's get to work."],
        "viktor": ["Ah, {name}. {greet}.", "{greet}, {name}. Sit down, let's look at how you're doing."],
    },
    "better": {
        "maya": ["You're giving away fewer pieces: {lately} a game, down from {before}. That's real progress."],
        "arjun": ["Whoa, only {lately} pieces lost a game lately, down from {before}. You're getting sharp!"],
        "zara": ["You're down to {lately} pieces lost a game, from {before}. Keep that up and you'll start winning."],
        "viktor": ["{lately} pieces a game, down from {before}. I've seen worse progress from grandmasters."],
    },
    "worse": {
        "maya": ["You've lost a few more pieces lately, {lately} a game. No worry, we'll slow down and fix it."],
        "arjun": ["Pieces have been slipping lately, {lately} a game. Let's tighten that up!"],
        "zara": ["{lately} pieces lost a game lately, up from {before}. That's costing you games. Let's fix it."],
        "viktor": ["{lately} pieces a game lately. Everyone has a bad week. Even me, once, in 1987."],
    },
    "focus": {
        "maya": ["Today, let's work on {habit}. {tip}"],
        "arjun": ["Today's mission: {habit}. {tip}"],
        "zara": ["One thing today: {habit}. {tip}"],
        "viktor": ["The lesson for today is {habit}. {tip}"],
    },
    "review": {
        "maya": ["I found {moments} in this game. Click one and I'll show you on the board.",
                 "{moments} decided this game. Let's look at them together, calmly."],
    },
    "review_clean": {
        "maya": ["A clean game: no big mistakes for me to show you. Well played."],
    },
    "unknown_game": {
        "maya": ["I haven't checked this game yet. Once it's finished and saved, I'll go through it with you."],
    },
    "puzzles": {
        "arjun": ["Puzzles! Before every move, ask what they can take. Let's see how fast you are.",
                  "Warm-up time. Look for checks, captures and threats, in that order."],
    },
    "progress": {
        "viktor": ["You've played {games} games with me watching. Let's see what's changed."],
    },
    "week_better": {
        "viktor": ["This week: {this_games} games, {this_pieces} pieces given away. Last week it was {last_pieces} in "
                   "{last_games}. That is how improvement looks."],
    },
    "week_same": {
        "viktor": ["This week: {this_games} games, {this_pieces} pieces given away; last week {last_pieces} in {last_games}. "
                   "Steady. Now let's make it better."],
    },
    "week_none": {
        "viktor": ["No games this week yet. A game a day keeps the rust away, as I always say. Well, I say it now."],
    },
    "lessons": {
        "viktor": ["Lessons are good. But the best teacher is your own last game. Remember that."],
    },
    "play": {
        "zara": ["Pick a bot near your level and play it like a real game. I'll stay quiet until it's over."],
    },
    "no_player": {
        "zara": ["Hi! I'm Zara, one of your Knightwise coaches. Open the Knightwise app and tell me your chess.com name."],
    },
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


def speak(section, home=None, hour=12, moments=None, rng=random, extra=None):
    """What the coach of this section says: {coach, name, voice, mood, lines, actions}.
    moments: for a game review, the number of key moments (None = a game the coach doesn't know).
    extra: {"novelty": the new thing from coach/plan.py, "advice": a do-this-not-that line} for the home section."""
    coach = SECTION_COACH.get(section, "zara")
    home = home if home is not None else insights.home()
    info = COACHES[coach]
    out = {"coach": coach, "name": info["name"], "voice": info["voice"], "mood": "calm", "lines": [], "actions": []}
    player = home.get("player")
    if not player:
        out["lines"] = [line("no_player", "zara", rng)]
        return {**out, "coach": "zara", "name": "Zara", "voice": COACHES["zara"]["voice"]}
    face = mood(home)
    facts = {"name": player, "greet": part_of_day(hour), "lately": home.get("pieces_last20"),
             "before": home.get("pieces_per_game"), "games": home.get("games")}
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
    else:
        if face == "pleased":
            lines.append(line("better", coach, rng, **facts))
        elif face == "worried":
            lines.append(line("worse", coach, rng, **facts))
        if section == "home" and extra and extra.get("novelty"):  # something new, when it's genuinely needed
            n = extra["novelty"]
            lines.append(f"Something new for you: {n['title'].lower() if n['kind'] != 'opening' else n['title']}. {n['why']}")
            out["actions"] = [{"label": "Learn it in Knightwise", "app": "plan"}] + suggestions(home)[:1]
            return {**out, "mood": "pleased", "lines": lines}
        if section == "home" and extra and extra.get("advice"):
            lines.append(extra["advice"])
            out["actions"] = suggestions(home)
            return {**out, "mood": face, "lines": lines}
        if section == "progress":  # the weekly memory instead of the general line: three sentences at most
            lines.append(week_line(home, coach, rng))
        elif section in ("lessons", "play"):
            lines.append(line(section, coach, rng, **facts))
        elif focus:
            lines.append(line("focus", coach, rng, **facts))
        out["actions"] = suggestions(home)
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
    "maya": "You are Maya, a calm former women's world champion, about 35. Patient, warm, strategic; short calm sentences.",
    "arjun": "You are Arjun, a 19-year-old chess prodigy. Energetic, quick, friendly, a bit playful; you love tactics.",
    "zara": "You are Zara, a bold 22-year-old attacking player. Direct, motivating, competitive, never rude.",
    "viktor": "You are Viktor, a 60-year-old veteran coach. Wise, kind, with dry humour; you have seen everything.",
}
# when the AI can't answer (no key, busy, down, or it said something the facts don't back up): still a warm reply
FALLBACK = {
    "maya": ["Let me keep this simple for now: {tip}", "Here's what matters most today: {tip}"],
    "arjun": ["Quick one while my brain reboots: {tip}", "Short version: {tip} Let's keep going!"],
    "zara": ["Straight to the point: {tip}", "Here's the one thing to do: {tip}"],
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
    coach = coach if coach in COACHES else "zara"
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
