"""Your two coaches, on chess.com and in Knightwise: Maya and Viktor. What they say, and where.

13 Oct 2026: two coaches instead of four, the player's choice ("that voice was the best", and they like Viktor too).
Maya: home, games and reviews, practice and puzzles. Viktor: your progress, your plan and lessons. One brain
(Stockfish + our facts); each always shows up for the same sections, so nothing to pick.
Written sentences work for everyone, offline; with an AI key she replies in conversation.
Fair play: nothing here looks at a game being played; the extension hides her wherever one could be running.
"""
import json
import random
import threading
import time

from coach import insights
from coach.paths import DATA

PUZZLES = "https://www.chess.com/puzzles/rated"
BOTS = "https://www.chess.com/play/computer"
LESSONS = "https://www.chess.com/lessons"
# The red ring's routes (1.0): from any coach page, step by step to the exact chess.com page; the extension rings
# the furthest step it can see on the page you're on (extension/buddy.js). Mapped on chess.com on 20 Oct 2026.
# A step is a link to that address, or a button with those words ("text"); "exact": that address only.
# fixes.json "nav" can replace a route's steps for everyone: {"puzzles": ["/puzzles", "/puzzles/rated|Solve Puzzles"]}.
ROUTES = {
    "puzzles": {"to": "/puzzles/rated", "name": "rated puzzles", "url": "https://www.chess.com/puzzles/rated",
                "steps": [{"path": "/puzzles", "name": "Puzzles", "exact": True},
                          {"path": "/puzzles/rated", "name": "Solve Puzzles", "text": "Solve Puzzles"}]},
    "bots": {"to": "/play/computer", "name": "the bots", "url": "https://www.chess.com/play/computer",
             "steps": [{"path": "/play", "name": "Play", "exact": True},
                       {"path": "/play/computer", "name": "Play Bots"}]},
    "archive": {"to": "/games/archive", "name": "your game history", "url": "https://www.chess.com/games/archive",
                "steps": [{"path": "/play", "name": "Play", "exact": True},
                          {"path": "/games/archive", "name": "Game History"}]},
    # a friend: the ring goes as far as chess.com's Play Online page and stops there (a game starts on it: fair play);
    # the coach says to press Play a Friend (22 Oct test)
    "friend": {"to": "/play/online", "name": "Play a Friend, on the Play Online page", "url": "https://www.chess.com/play/online",
               "steps": [{"path": "/play", "name": "Play", "exact": True},
                         {"path": "/play/online", "name": "Play Online"}]},
    "lessons": {"to": "/lessons", "name": "the lessons", "url": "https://www.chess.com/lessons",
                "steps": [{"path": "/learn", "name": "Learn", "exact": True},
                          {"path": "/lessons", "name": "Next Lesson"}]},
}


def guide(route_id, label=None):
    """A coach button that guides the player there with the red ring (on chess.com; a plain link elsewhere)."""
    r = ROUTES[route_id]
    return {"label": label or f"Show me the way to {r['name']}", "url": r["url"], "guide": {"id": route_id, **r}}

COACHES = {
    "maya": {"role": "Your games and practice", "name": "Maya", "voice": "af_heart",
             "about": "Former champion. Calm, patient, clear.", "sections": ["home", "play", "review", "games", "puzzles", "archive", "member"]},
    "viktor": {"role": "Your progress and plan", "name": "Viktor", "voice": "am_michael",
               "about": "Veteran. Wise, dry humour, has seen it all.", "sections": ["progress", "lessons", "plan"]},
}
COACH = "maya"  # where no section says otherwise
SAID = DATA / "said.json"  # which sentences were said lately, and the jokes already told
_SAID_LOCK = threading.Lock()
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

# What each coach says, many ways each (1.0, "no line twice"); a kind with only Maya's words is said by Maya's words.
# {name}, {habit}, {lately}, {before}, {moments}... are filled in. line() remembers what was said lately and picks
# something else; JOKES are told once, ever, then retired.
SAY = {
    "hello": {"maya": ["{greet}, {name}. Good to see you.", "{greet}, {name}. Let's take it one move at a time today.",
                       "{greet}, {name}. Nice to have you back.", "Hi {name}. {greet}. Ready when you are.",
                       "{greet}, {name}. Let's make today count, calmly.", "{greet}, {name}. I've been looking at your games.",
                       "Hey {name}. {greet}. Shall we?", "{greet}, {name}. One good habit at a time."],
              "viktor": ["Ah, {name}. {greet}.", "{greet}, {name}. Sit down, let's look at how you're doing.",
                         "{greet}, {name}. Let's see what the numbers say.", "{name}. {greet}. Tea first, then chess.",
                         "{greet}, {name}. I have your games here. Let's talk.", "{greet}, {name}. Good, you came."]},
    "better": {"maya": ["You're giving away fewer pieces: {lately} a game, down from {before}. That's real progress.",
                        "{lately} pieces a game now, down from {before}. Your habit is working.",
                        "Fewer pieces given away: {lately} a game, it used to be {before}. Keep it going.",
                        "Down from {before} to {lately} pieces a game. That's you getting more careful."],
               "viktor": ["{lately} pieces a game, down from {before}. That is how improvement looks.",
                          "From {before} pieces a game to {lately}. Steady work pays.",
                          "{lately} a game now, {before} before. Good. Don't get comfortable."]},
    "worse": {"maya": ["You've lost a few more pieces lately, {lately} a game, up from {before}. No worry, we'll slow down and fix it.",
                       "{lately} pieces a game lately, up from {before}. A slower move or two will fix that.",
                       "A few more pieces slipped lately: {lately} a game, it was {before}. Let's take a breath and look again.",
                       "Up to {lately} pieces a game from {before}. It happens. We'll get it back."],
              "viktor": ["{lately} pieces a game lately. Everyone has a bad week.",
                         "{lately} a game, up from {before}. A dip, not a trend. Not yet.",
                         "Up from {before} to {lately}. Fine. Now we work."]},
    "focus": {"maya": ["Today, let's work on {habit}. {tip}", "Our one thing today: {habit}. {tip}",
                       "Let's keep going with {habit}. {tip}", "The habit to build: {habit}. {tip}"],
              "viktor": ["The lesson for today is {habit}. {tip}", "Today's work: {habit}. {tip}",
                         "One thing, done well: {habit}. {tip}"]},
    "review": {"maya": ["I found {moments} in this game. Click one and I'll show you on the board.",
                        "{moments} decided this game. Let's look at them together, calmly.",
                        "This game had {moments}. Pick one and we'll go through it.",
                        "{moments} in this one. Let's see what happened, one at a time.",
                        "I've gone through it: {moments}. Start wherever you like."]},
    "review_clean": {"maya": ["A clean game: no big mistakes for me to show you. Well played.",
                              "Nothing big to fix here. A clean game, nicely done.",
                              "No big mistakes in this one. That's the kind of game we want."]},
    "unknown_game": {"maya": ["I haven't checked this game yet. Once it's finished and saved, I'll go through it with you.",
                              "This one isn't checked yet. Once chess.com saves it, I'll be ready.",
                              "I don't know this game yet. Give me a moment after it's saved."]},
    "puzzles": {"maya": ["Puzzles. I won't look at the board while you solve: that's chess.com's rule, and mine. "
                         "Before every move, ask what they can take.",
                         "Warm-up time. I stay out of the puzzle itself. Look for checks, captures and threats, in that order.",
                         "Puzzles: I'll stay quiet while you solve. Checks first, then captures, then threats.",
                         "Your puzzles. I don't peek, that's the rule. Ask what each move attacks.",
                         "Puzzle time. You solve, I stay out of it. What does their last move attack?"]},
    "archive": {"maya": ["Every game I've checked has a Knightwise tag under it. Click one and I'll open its review, "
                         "one moment at a time.",
                         "Your games, with my tag on each one I've checked. The red ones are where to look first.",
                         "Each checked game has my tag. Pick one and I'll take you through it.",
                         "My tags are under your games. The red ones have the most to teach."]},
    "progress": {"viktor": ["You've played {games} games with me watching. Let's see what's changed.",
                            "{games} games so far. Let's see what they tell us.",
                            "{games} games checked. Here's the story they tell."]},
    "week_better": {"viktor": ["This week: {this_games} games, {this_pieces} pieces given away. Last week it was {last_pieces} in "
                               "{last_games}. That is how improvement looks.",
                               "{this_games} games this week, {this_pieces} pieces given away. Last week: {last_pieces} in "
                               "{last_games}. Better. Good.",
                               "This week {this_pieces} pieces in {this_games} games, against {last_pieces} in {last_games} "
                               "last week. Keep doing what you're doing."]},
    "week_same": {"viktor": ["This week: {this_games} games, {this_pieces} pieces given away; last week {last_pieces} in "
                             "{last_games}. Steady. Now let's make it better.",
                             "{this_games} games this week, {this_pieces} pieces given away. Last week {last_pieces} in "
                             "{last_games}. Not worse. Let's make it better.",
                             "This week {this_pieces} pieces in {this_games} games; last week {last_pieces} in {last_games}. "
                             "The habit needs a bit more work."]},
    "week_none": {"viktor": ["No games this week yet. One game is enough to start.",
                             "Nothing played this week yet. One calm game, then we look at it.",
                             "A quiet week so far. Play one, and I'll have something to tell you."]},
    "lessons": {"viktor": ["Lessons are good. But the best teacher is your own last game. Remember that.",
                           "Learn the idea here, then use it in your next game. That's when it sticks.",
                           "A lesson is a start. Your games are where it becomes yours."]},
    "games": {"maya": ["Pick a game and I'll show you the moments that decided it.",
                       "Every game has one or two moments that matter. Choose one and let's find them.",
                       "Your games. Choose one and we'll find what mattered.",
                       "Pick any game. I'll show you where it turned."]},
    "plan": {"viktor": ["Here's your plan: one opening, one tactic, one idea, one endgame. Pick one and we start.",
                        "Not a pile of homework. Four things, chosen for you. Start with whichever you like.",
                        "Four things, picked from your games. Any order you like.",
                        "Your plan. Small, on purpose. Pick one."]},
    "play": {"maya": ["Pick a bot near your level and play it like a real game. I'll stay quiet until it's over.",
                      "Play a bot near your level, slowly, like it matters. I'll be quiet until the end.",
                      "A game against a bot: treat it as real. I'll see you after."]},
    "no_player": {"maya": ["Hi, I'm Maya, your Knightwise coach. Open the Knightwise app and tell me your chess.com name."]},
}
# Told once, ever, then retired (19 Oct: "jokes stay, casual and chill, never repeated"). Same facts as SAY.
JOKES = {
    "better": {"viktor": ["{lately} pieces a game, down from {before}. I've seen worse progress from grandmasters.",
                          "{lately} a game, down from {before}. If you keep this up, I'll have to retire."],
               "maya": ["{lately} pieces a game, down from {before}. Your pieces are starting to trust you."]},
    "worse": {"viktor": ["{lately} pieces a game lately. Everyone has a bad week. Even me, once, in 1987.",
                         "{lately} a game, up from {before}. Your pieces have been sneaking off. We'll fetch them back."],
              "maya": ["{lately} pieces a game, up from {before}. Your knights went on holiday. Let's call them home."]},
    "week_none": {"viktor": ["No games this week yet. A game a day keeps the rust away, as I always say. Well, I say it now."]},
    "hello": {"viktor": ["{greet}, {name}. I was just explaining the Sicilian to my cat. She wasn't listening either."],
              "maya": ["{greet}, {name}. The pieces missed you. Well, the pawns did."]},
    "review_clean": {"maya": ["A clean game. I had my red pen ready for nothing. Well played."]},
    "lessons": {"viktor": ["Lessons are good. In my day we learned from books so heavy they counted as exercise."]},
}
JOKE_CHANCE = 0.25  # how often a joke is told when one is left for that kind


def _said():
    try:
        return json.loads(SAID.read_text())
    except (OSError, ValueError):
        return {}


def line(kind, coach, rng=random, **facts):
    """One sentence of this kind in this coach's words (any coach's if they have none of their own): never one said
    lately, and a joke at most once, ever (data/said.json remembers)."""
    who = coach if SAY[kind].get(coach) else next(iter(SAY[kind]))
    options = SAY[kind][who]
    with _SAID_LOCK:
        said = _said()
        told = set(said.get("jokes", []))
        jokes = [j for j in (JOKES.get(kind) or {}).get(who, []) if j not in told]
        if jokes and rng.random() < JOKE_CHANCE:
            pick = rng.choice(jokes)
            said["jokes"] = sorted(told | {pick})
        else:
            key = f"{kind}/{who}"
            recent = said.get(key, [])
            fresh = [i for i in range(len(options)) if i not in recent] or [0]
            i = rng.choice(fresh)
            pick = options[i]
            said[key] = (recent + [i])[-(len(options) - 1):] if len(options) > 1 else []
        try:
            SAID.parent.mkdir(parents=True, exist_ok=True)
            SAID.write_text(json.dumps(said))
        except OSError:
            pass
    return pick.format(**facts)


AGAIN = ["Back again. Here's where we are.", "Good, you're back.", "Picking up where we were.", "Welcome back.",
         "There you are. Where were we?", "Back for more. Good."]
SAY["again"] = {"maya": AGAIN}


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


# the chess.com place that trains this player's habit, offered by itself on chess.com's home (22 Oct test: "the coach
# doesn't suggest sections useful for me on chess.com, it only points when I tell it")
CHESSCOM_FOR = {
    "left a piece hanging": ("puzzles", "Puzzles on chess.com: spot what's loose"),
    "walked into a fork or trick": ("puzzles", "Puzzles on chess.com: forks and tricks"),
    "missed a free capture": ("puzzles", "Puzzles on chess.com: free pieces"),
    "walked into checkmate": ("lessons", "Lessons on chess.com: checkmate patterns"),
    "missed a checkmate": ("lessons", "Lessons on chess.com: checkmate patterns"),
    "stalemated a won game": ("lessons", "Lessons on chess.com: finishing won games"),
}


def chesscom_pick(home):
    """A red-ring button to the chess.com section for the player's focus, or None."""
    f = (home or {}).get("focus") or {}
    route = CHESSCOM_FOR.get(f.get("pattern"))
    return guide(route[0], route[1]) if route else None


def speak(section, home=None, hour=12, moments=None, rng=random, extra=None, again=False, in_app=False):
    """again: a second visit to this section today, so no full welcome again, just where things stand (13 Oct test:
    "welcoming is an art"; the coach was greeting every time, then folding silently)."""
    said = _speak(section, home, hour, moments, rng, extra, in_app)
    if section == "home" and not in_app and said.get("lines"):  # on chess.com: the place there that fits your habit
        if home is None:  # chess.com asks without the player's facts: look them up (22 Oct: the pick never showed)
            try:
                from coach import insights
                home = insights.home()
            except Exception:
                home = {}
        pick = chesscom_pick(home)
        acts = said.get("actions") or []
        if pick and not any((a.get("guide") or {}).get("id") == pick["guide"]["id"] for a in acts):
            said = {**said, "actions": [a for a in acts if a is not OPEN_APP] + [pick] + [a for a in acts if a is OPEN_APP]}
    if in_app:
        said = _for_app(said)
    if again and said.get("lines") and section != "review":
        lines = said["lines"]
        keep = [lines[-1]] if lines[-1].startswith("My pick") else lines[1:2]  # where things stand, in one line
        if keep and not fresh_today(keep[0]):  # the same stat once a day, not on every visit (22 Oct test)
            return {**said, "lines": [], "again": True, "quiet": True}
        said = {**said, "lines": [line("again", said["coach"], rng)] + keep, "again": True}
    return said


def fresh_today(text, today=None):
    """True the first time this sentence is shown today (data/said.json remembers), then False until tomorrow."""
    import datetime
    today = today or datetime.date.today().isoformat()
    with _SAID_LOCK:
        said = _said()
        shown = said.get("shown", {}) if said.get("shown_day") == today else {}
        if text in shown:
            return False
        said["shown_day"], said["shown"] = today, {**shown, text: 1}
        try:
            SAID.parent.mkdir(parents=True, exist_ok=True)
            SAID.write_text(json.dumps(said))
        except OSError:
            pass
    return True


def _for_app(said):
    """Inside Knightwise there's no "Open Knightwise", and no "… in Knightwise" on the buttons (full test, 14 Oct:
    "Knightwise is already open, why the route in the pop-up?")."""
    acts = [{**a, "label": a["label"].replace(" in Knightwise", "")} for a in said.get("actions") or [] if a != OPEN_APP]
    lines = [l.replace(" in Knightwise", "") if l.startswith("My pick") else l for l in said.get("lines") or []]
    return {**said, "actions": acts, "lines": lines}


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

    if section == "member":  # someone's chess.com profile: prep against them, before you play (0.8)
        who = (extra or {}).get("who")
        if not who or who == (player or "").lower():
            return {**out, "lines": []}  # your own profile, or no name: nothing to say
        out["actions"] = [{"label": f"Prep against {who} in Knightwise", "app": f"prep/{who}", "best": True,
                           "why": "Their openings and how their games end, from their public games."}, OPEN_APP]
        return {**out, "mood": "calm", "lines": [f"Playing {who} soon? I can show you how they play: their openings, "
                                                 "and how their games usually end. Only before the game, never during."]}
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
            warm = [WARMUP] if not in_app and home.get("daily") else suggestions(home)[:1]  # the warm-up stays on chess.com (19 Oct)
            out["actions"] = [{"label": "Learn it in Knightwise", "app": "plan", "best": True,
                               "why": "It's new for you, and it fits your habit."}] + warm + [OPEN_APP]
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
        elif section in ("lessons", "play", "games", "plan", "archive"):
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
    elif section == "archive" and last.get("id") and last.get("moments"):  # your games list: the latest one first
        pick = {"label": f"Review vs {last.get('opponent', 'your last opponent')} in Knightwise", "app": f"games/{last['id']}",
                "why": "One moment at a time, with your clock" + (", and a rematch from where it went wrong."
                                                                  if last.get("result") != "win" else ".")}
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
    actions = [guide("puzzles", "Warm up with puzzles")]
    last = home.get("last_game")
    if last and last.get("moments") and "/game/live/" in last["url"]:  # daily/bot addresses can point elsewhere
        actions.append({"label": f"Review your game vs {last['opponent']}", "url": last["url"]})
    elif last and last.get("moments") and home.get("player"):
        actions.append({**guide("archive", "Review your recent games"), "url": f"https://www.chess.com/games/archive/{home['player']}"})
    else:
        actions.append(guide("bots", "Play a bot at your level"))
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
            if last else None, "repertoire": _repertoire()}


def _repertoire():
    """The player's three opening lines, as saved (19 Oct: "what should I play against e4?" got a general tip,
    because the answer's squares weren't in the facts). Read from the file only: never runs the engine."""
    import json
    from coach import repertoire
    try:
        lines = json.loads(repertoire.FILE.read_text())
    except (OSError, ValueError):
        return None
    return [{"as": l["side"], "against": l.get("against"), "name": l["name"],
             "moves": " ".join(s["san"] for s in l.get("steps", []))} for l in lines] or None


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
