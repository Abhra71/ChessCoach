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


def speak(section, home=None, hour=12, moments=None, rng=random):
    """What the coach of this section says: {coach, name, voice, mood, lines, actions}.
    moments: for a game review, the number of key moments (None = a game the coach doesn't know)."""
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
        if section in ("progress", "lessons", "play"):
            lines.append(line(section, coach, rng, **facts))
        elif focus:
            lines.append(line("focus", coach, rng, **facts))
        out["actions"] = suggestions(home)
    return {**out, "mood": face, "lines": lines}


def suggestions(home):
    """One or two things to do next, as links on chess.com (the player clicks; we never click for them)."""
    actions = [{"label": "Warm up with puzzles", "url": PUZZLES}]
    last = home.get("last_game")
    if last and last.get("moments"):
        actions.append({"label": f"Review your game vs {last['opponent']}", "url": last["url"]})
    else:
        actions.append({"label": "Play a bot at your level", "url": BOTS})
    return actions
