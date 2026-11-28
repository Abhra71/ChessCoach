"""The coaches' memories and the club's story moments (storyline steps 3.3 and 3.5, docs/STORYLINE.md sections 2 and 5).

Memories: short things from Maya's and Viktor's lives, each told once, at the moment it fits the player's own games;
never more than one a week per coach, always ending in something useful. Story moments: the club noticing the
player's own milestones (the first match record, a 7-day streak, a hundred games, a year). On this day: one real
event from chess history on its date, at most once a week, never the same twice, each with its source.

Everything told is remembered in data/story.json ("told": id -> the day), so nothing is said twice.
"""
import datetime
import time

from coach import story

WEEK = 7  # one memory a week per coach at most (tone rule: they stay special)
HISTORY_EVERY = 7  # "on this day" at most once a week (owner, 28 Nov: "more often", weekly)
HISTORY_LATE = 2  # an event up to 2 days old still counts ("on 9 November...") if the app wasn't opened that day

# id -> (coach, the line, where it leads). Lines from docs/STORYLINE.md, kept to one or two sentences each.
MEMORIES = {
    "maya-queen": ("maya", "At my very first tournament I left my queen hanging on move 12, and my coach said I'd "
                   "never forget to look again. Before each move, check what they can take.",
                   "practice"),
    "maya-clock": ("maya", "At a junior final I had a winning position and lost on time. That's why I made the "
                   "slow-down drill.", "clockdrill"),
    "maya-streak": ("maya", "I once lost seven games in a row online and kept clicking new game; since then, one more "
                    "game only if the last one was fun. Five minutes of practice instead?", "daily"),
    "maya-memorise": ("maya", "I once learned twenty moves of an opening by heart, and was lost when someone played "
                      "something else on move 4. Know why each move is there, not just the moves.", None),
    "maya-practised": ("maya", "My first win against a stronger player came from a fork I'd practised that same "
                       "morning. You practised, then you won: that's how it works.", "practice"),
    "viktor-regret": ("viktor", "In the last round of my championship, one win from the title, I had a winning "
                      "combination, felt sure, and played the quick move instead of checking it. I lost, not to a "
                      "better player but to a move I didn't check: see it before you move it.", None),
    "viktor-notebook": ("viktor", "For years I didn't write my games down, and half my chess life is gone because I "
                        "thought I'd remember. Yours are all kept here, every one.", "games"),
}
# told on opening a page, the first time (not as a suggestion): page -> memory
ON_PAGE = {"calc": "viktor-regret", "repertoire": "maya-memorise"}

# id -> (coach, the line). The club noticing the player's own milestones.
MOMENTS = {
    "welcome": ("maya", "Welcome to the club. I'm Maya from Chennai, Viktor is from Berlin, and your games are our "
                "work now."),
    "first-review": ("maya", "That's your first match record. Every member's starts somewhere."),
    "streak-7": ("maya", "Seven days in a row. That's how I trained as a junior: five minutes, every day."),
    "hundred": ("viktor", "A hundred matches in your records. I've seen players quit at ten."),
    "year": ("viktor", "A year in the club: {games} games since you joined. Maya and I are proud of you."),
}

# On this day: (month, day, year, what happened, source). Every date checked against its Wikipedia page (28 Nov
# 2026); events the pages give no exact day for (the Immortal Game, Kasparov's Immortal) are left out.
W = "https://en.wikipedia.org/wiki/"
HISTORY = [
    (3, 29, 1886, "Wilhelm Steinitz won the first official World Championship match, against Johannes Zukertort.",
     W + "World_Chess_Championship_1886"),
    (7, 20, 1924, "FIDE, the world chess federation, was founded in Paris. It's why 20 July is International Chess Day.",
     W + "FIDE"),
    (10, 17, 1956, "Bobby Fischer, 13, beat Donald Byrne in New York with a queen sacrifice: the Game of the Century.",
     W + "Game_of_the_Century_(chess)"),
    (5, 7, 1960, "Mikhail Tal, the magician from Riga, became world champion at 23, beating Botvinnik.",
     W + "World_Chess_Championship_1960"),
    (9, 1, 1972, "Bobby Fischer became world champion: Spassky resigned the adjourned last game without playing on.",
     W + "World_Chess_Championship_1972"),
    (11, 9, 1985, "Garry Kasparov, 22, beat Karpov to become the youngest world champion of his time.",
     W + "World_Chess_Championship_1985"),
    (2, 10, 1996, "Deep Blue beat Kasparov in a game for the first time, in Philadelphia. Kasparov still won the match.",
     W + "Deep_Blue_versus_Garry_Kasparov"),
    (5, 11, 1997, "Deep Blue won the rematch against Kasparov in New York: the first machine to beat a world champion "
     "in a match.", W + "Deep_Blue_versus_Garry_Kasparov"),
    (11, 2, 2000, "Vladimir Kramnik took the title from Kasparov in London, with the Berlin Defence as his wall.",
     W + "Classical_World_Chess_Championship_2000"),
    (11, 22, 2013, "Magnus Carlsen became world champion in Chennai, Maya's city, beating Viswanathan Anand.",
     W + "World_Chess_Championship_2013"),
    (12, 12, 2024, "Gukesh, 18, beat Ding Liren in Singapore: the youngest undisputed world champion ever.",
     W + "World_Chess_Championship_2024"),
    (6, 22, 1837, "Paul Morphy was born in New Orleans. Twenty years later he was the best player in the world.",
     W + "Paul_Morphy"),
    (12, 24, 1868, "Emanuel Lasker was born. He was world champion for 27 years and lived in Berlin, Viktor's city.",
     W + "Emanuel_Lasker"),
    (11, 19, 1888, "José Raúl Capablanca was born in Havana. He played so simply that it looked easy.",
     W + "Jos%C3%A9_Ra%C3%BAl_Capablanca"),
    (8, 17, 1911, "Mikhail Botvinnik was born. He trained his students to prepare like scientists.",
     W + "Mikhail_Botvinnik"),
    (11, 9, 1936, "Mikhail Tal was born in Riga. His sacrifices still make strong players nervous.",
     W + "Mikhail_Tal"),
    (3, 9, 1943, "Bobby Fischer was born in Chicago.", W + "Bobby_Fischer"),
    (5, 23, 1951, "Anatoly Karpov was born. World champion for ten years, a master of squeezing small advantages.",
     W + "Anatoly_Karpov"),
    (4, 13, 1963, "Garry Kasparov was born in Baku.", W + "Garry_Kasparov"),
    (12, 11, 1969, "Viswanathan Anand was born in Chennai: India's first grandmaster and five times world champion.",
     W + "Viswanathan_Anand"),
    (7, 23, 1976, "Judit Polgár was born in Budapest: the strongest woman player in history.", W + "Judit_Polg%C3%A1r"),
    (11, 30, 1990, "Magnus Carlsen was born in Norway.", W + "Magnus_Carlsen"),
    (5, 29, 2006, "Gukesh was born in Chennai.", W + "Gukesh_Dommaraju"),
]
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]


def _told(m=None):
    return (m if m is not None else story._load()).get("told_lines") or {}


def told(item_id, day=None):
    """Remember that it was said (today, or the given day)."""
    m = story._load()
    m["told_lines"] = {**_told(m), item_id: (day or datetime.date.today()).isoformat()}
    story._save(m)


def _coach_spoke_lately(coach, day, told_lines):
    cut = (day - datetime.timedelta(days=WEEK)).isoformat()
    return any(MEMORIES[i][0] == coach and d > cut for i, d in told_lines.items() if i in MEMORIES)


def on_page(page):
    """The memory that belongs to opening this page, until it has been told: {id, coach, line}, or None. The page says
    when it was really shown (told_on_page), so leaving at once doesn't lose it."""
    mid = ON_PAGE.get(page)
    if not mid or mid in _told():
        return None
    coach, line, _ = MEMORIES[mid]
    return {"id": mid, "coach": coach, "line": line}


def told_on_page(mid, day=None):
    """The page showed it: never again."""
    if mid in ON_PAGE.values():
        told(mid, day)
        return True
    return False


def joined(day=None):
    """The day the player joined the club (first seen by this version), remembered once."""
    m = story._load()
    if not m.get("joined"):
        m["joined"] = (day or datetime.date.today()).isoformat()
        story._save(m)
    return datetime.date.fromisoformat(m["joined"])


def _queen_hung(r):
    """Their very next move takes the queen the player just left hanging."""
    import chess
    try:
        b = chess.Board(r["fen"])
        b.push_san(r["move"])
        reply = chess.Move.from_uci((r.get("reply_pv") or [""])[0])
        p = b.piece_at(reply.to_square)
        return bool(p and p.piece_type == chess.QUEEN and b.is_capture(reply))
    except Exception:
        return False


def candidates(home, games, player, day, nudges):
    """[(kind, id, coach, line, route or None, action or None)]: what the club could say today, from the player's own
    data. nudges: coach/nudge.py's memory (what was opened, when)."""
    from coach import insights
    t = _told()
    out = []
    opened = (nudges or {}).get("opened_on") or {}
    ever = (nudges or {}).get("ever") or {}

    def memory(mid, when):
        coach, line, route = MEMORIES[mid]
        if mid not in t and when and not _coach_spoke_lately(coach, day, t):
            out.append(("memory", mid, coach, line, route, None))

    def moment(mid, when, **facts):
        if mid not in t and when:
            coach, line = MOMENTS[mid]
            out.append(("story", mid, coach, line.format(**facts), None, None))

    new_here = not any(d < day.isoformat() for days in ever.values() for d in days)  # nothing suggested before today
    moment("welcome", new_here and home.get("games"))
    reviews = [r for r in opened if r.startswith("games/")]
    moment("first-review", len(reviews) == 1)
    moment("streak-7", ((home.get("daily") or {}).get("streak") or 0) >= 7)
    moment("hundred", (home.get("games") or 0) >= 100)
    start = joined(day)
    if (day - start).days >= 365 and games:
        n = sum(1 for g in games if (g.get("end_time") or 0) >= time.mktime(start.timetuple()))
        moment("year", True, games=n)

    if games and player:
        moves = insights._moves()
        mine = sorted((g for g in games if g.get("url") in moves), key=lambda g: g.get("end_time") or 0, reverse=True)
        last = home.get("last_game") or {}
        fresh = time.time() - (last.get("end_time") or 0) < 3 * 86400
        if fresh and mine:
            memory("maya-queen", any(r.get("pattern") == "left a piece hanging" and _queen_hung(r)
                                     for r in moves.get(mine[0]["url"], [])))
        results = [insights._result(g, insights._side(g, player)[0]) for g in mine[:5]]
        memory("maya-streak", len(results) == 5 and all(x == "loss" for x in results) and fresh)
        if fresh and last.get("result") == "win":
            from coach import memory as practice
            end = datetime.date.fromtimestamp(last["end_time"])
            days = {e["day"] for e in practice._first_each_day()}
            memory("maya-practised", end.isoformat() in days or (end - datetime.timedelta(days=1)).isoformat() in days)
        memory("viktor-notebook", len(mine) >= 30)
    return out


def clock_memory(prog, day):
    """Maya's lost junior final, when the games show time trouble (the same need as the clock drill)."""
    clk = (prog or {}).get("clock") or {}
    t = _told()
    if "maya-clock" in t or _coach_spoke_lately("maya", day, t):
        return None
    if clk.get("big", 0) >= 8 and clk.get("fast", 0) / clk["big"] >= 0.3:
        coach, line, route = MEMORIES["maya-clock"]
        return ("memory", "maya-clock", coach, line, route, None)
    return None


def on_this_day(day):
    """(id, line, source) for a real event from chess history on this date (or up to 2 days ago), never told before and
    at most once a week; or None."""
    t = _told()
    cut = (day - datetime.timedelta(days=HISTORY_EVERY)).isoformat()
    if any(i.startswith("history-") and d > cut for i, d in t.items()):
        return None
    for late in range(HISTORY_LATE + 1):
        d = day - datetime.timedelta(days=late)
        for month, dd, year, what, src in HISTORY:
            hid = f"history-{year}-{month:02d}-{dd:02d}"
            if (month, dd) == (d.month, d.day) and hid not in t:
                when = f"On this day in {year}" if late == 0 else f"On {dd} {MONTHS[month - 1]} {year}"
                return hid, f"{when}: {what}", src
    return None
