"""The Knightwise course (0.10): the teacher. Lessons in order, from beginner to 2,000+, picked by your games.

Every mistake in your games gets a reason (coach/why.py): an *idea* such as a fork, a guard moved away, pieces left at
home. Each lesson teaches one or two of those ideas, and the course follows you:
  * the next lesson is the one whose idea costs you most in your last 20 games, at your level or below;
  * a lesson is done when you've studied and practised it AND the mistake has dropped in the games you played after,
    not when you've read it;
  * a lesson whose mistake you rarely make is marked "you already do this", so you never sit through the obvious.

The text is written for Knightwise, in our own words: the order follows what chess coaches broadly agree on (safety,
then tactics, then good starts, then plans and endings). The positions come from your games and the Lichess puzzle
database; Stockfish checks every one. Lessons that need strong players' games ("coming") wait for that download.
"""
import collections
import datetime
import json

from coach import insights
from coach.paths import DATA

FILE = DATA / "course.json"
WINDOW = 20  # your last 20 checked games
MISTAKE = 10  # a move that cost at least 10 points of your chance to win gets a reason
AFTER = 5  # games played after studying a lesson before it can be passed
FINE = 0.5  # a lesson's mistake at under half its goal: "you already do this"
NEEDS_ELITE = "Needs strong players' games (coach/elite.py builds them from the Lichess Elite download)."
REPERTOIRE_STRUCTURES = {"Italian": "italian", "Caro-Kann": "caro", "Queen's Gambit Declined": "carlsbad",
                         "Sicilian": "sicilian", "French": "french", "King's Indian": "kid"}
LEVEL_ORDER = ["safe", "tactics", "club", "precise", "expert"]
LEVEL_NAME = {"safe": "Safe pieces", "tactics": "Tactics and good starts", "club": "Fewer mistakes",
              "precise": "Precision", "expert": "Expert"}


def L(lid, level, title, ideas, goal, teach, habit, themes=(), train=None, coming=None, elite=None):
    """One lesson. ideas: the reasons (coach/why.py) it fixes; goal: at most this many such mistakes a game.
    teach: short paragraphs; habit: the one check to make every move; themes: Lichess puzzle themes to practise;
    train: (label, app route) of a trainer that goes with it; coming: why it isn't ready yet;
    elite: pawn structures from strong players' games (coach/elite.py) to practise, or "repertoire" for yours."""
    return {"id": lid, "level": level, "title": title, "ideas": list(ideas), "goal": goal, "teach": teach,
            "habit": habit, "themes": list(themes), "train": train, "coming": coming, "elite": elite}


LESSONS = [
    # ---------- Safe pieces: up to about 800 ----------
    L("safe-hanging", "safe", "Keep every piece safe", ["hanging"], 0.3, [
        "Most games below 1,000 are decided by one thing: a piece left where it can be taken for free.",
        "A piece is safe when nothing attacks it, or when it's defended and nothing cheaper attacks it. A knight "
        "defended by a pawn is still lost if their pawn can take it: you get a pawn back for a knight.",
        "The trick is to look at the square you're moving to *before* you let go: what of theirs can reach it?",
    ], "Before every move: after I move here, what can they take?", ["hangingPiece"]),
    L("safe-threats", "safe", "Answer their threat first", ["threats"], 0.3, [
        "Every move your opponent makes is saying something. Often it says: \"I'm attacking your piece.\"",
        "When you only think about your own plan, you miss it, and the piece goes. Strong players read the "
        "opponent's move first, every single time.",
        "If a piece is attacked, you have four answers: move it, defend it, block the attack, or take the attacker.",
    ], "After every move they make: what does it attack? What does it threaten next?", ["hangingPiece", "defensiveMove"]),
    L("safe-free", "safe", "Take what they leave you", ["free"], 0.3, [
        "Your opponents make the same mistake you do: they leave pieces hanging. The player who notices wins material.",
        "Look at every capture you have, every move. Count: what do I take, what can they take back?",
        "A free piece is a free piece: take it, unless taking walks into a checkmate.",
    ], "Every move: which of their pieces can I take, and is it defended?", ["hangingPiece"]),
    L("safe-guard", "safe", "Don't move the guard", ["defender"], 0.2, [
        "Some of your pieces have a job: they guard another piece or an important square.",
        "Move the guard away and whatever it was guarding is suddenly loose. It looks like a new mistake, but the "
        "mistake was moving the guard.",
        "Before you move a piece, ask what it was protecting.",
    ], "Before you move a piece: what was it guarding?", ["capturingDefender"]),
    L("safe-checks", "safe", "Look at their checks", ["king_danger"], 0.1, [
        "Losing by checkmate is the fastest way to lose a game you were winning.",
        "Before every move, look at every check they could give after it. Most checkmates start with a check you "
        "didn't look at.",
        "Keep your king safe: castle, keep pawns in front of it, and don't open lines towards it.",
    ], "Before every move: after it, what checks can they give?", ["mateIn1", "defensiveMove"]),
    L("safe-backrank", "safe", "The back rank", ["back_rank"], 0.05, [
        "Your castled king behind three pawns feels safe, until a rook or queen lands on your first rank and it has "
        "no square to run to: that's back-rank mate.",
        "The cure is simple and cheap: one pawn move in front of the king (h3 or g3 as White, h6 or g6 as Black), "
        "when you have a quiet moment, gives it a square to escape to.",
        "And keep a rook or queen watching your back rank while their heavy pieces are on the board.",
    ], "When their rook or queen can reach your first rank: does my king have a square?", ["backRankMate"]),
    L("safe-mate1", "safe", "Finish them: checkmate in one", ["mate_finish"], 0.1, [
        "Sometimes the game can end right now and you play something else.",
        "Checks come first. Every move, look at each check you can give: is any of them checkmate?",
        "Checkmate means: the king is attacked, it can't move to a safe square, nothing can block, and nothing can "
        "take the attacker.",
    ], "Every move: look at all my checks first.", ["mateIn1"]),
    L("safe-stalemate", "safe", "Don't stalemate a won game", ["stalemate"], 0.0, [
        "Stalemate is a draw: their king isn't in check, but they have no legal move.",
        "It happens when you're far ahead and their king is alone in a corner. Your queen takes away its last square, "
        "and the game you'd won is a draw.",
        "With a queen against a lone king: push the king to the edge, then bring your own king close, and always "
        "leave their king a square until the move that mates.",
    ], "When they have only a king: after my move, can their king move?", [], ("Mate with king and queen", "endgame/queen")),

    # ---------- Tactics and good starts: about 800 to 1,200 ----------
    L("tac-fork", "tactics", "Forks", ["fork"], 0.2, [
        "A fork is one piece attacking two at once. They can save only one.",
        "Knights are the great forkers, because their attack is hard to see. Queens fork too, often with check.",
        "To see forks coming, look at the squares their knight can reach in one move. If two of your valuable "
        "pieces (or your king) are on squares one knight jump from the same square, watch out.",
    ], "Their knights and queen: can one of them reach a square that hits two of my pieces?", ["fork"]),
    L("tac-pin", "tactics", "Pins", ["pin"], 0.15, [
        "A pin is an attack through one piece onto something bigger behind it. The piece in front can't move "
        "without exposing what's behind.",
        "A piece pinned to the king can't move at all: it's the law. Attack a pinned piece again, and it falls.",
        "Bishops, rooks and queens pin. Watch the lines from their long-range pieces to your king and queen.",
    ], "Is any of my pieces on a line between their bishop, rook or queen and my king or queen?", ["pin"]),
    L("tac-skewer", "tactics", "Skewers", ["skewer"], 0.15, [
        "A skewer is a pin turned around: the big piece is in front. It has to move, and the piece behind it is taken.",
        "It happens most with checks: their rook checks your king, the king steps aside, and your rook behind is lost.",
        "Keep your king and your valuable pieces off the same straight line or diagonal.",
    ], "Are my king and another piece on one line their rook, bishop or queen could use?", ["skewer"]),
    L("tac-discovered", "tactics", "Discovered attacks", ["discovered"], 0.15, [
        "A discovered attack: a piece moves out of the way and uncovers an attack from the piece behind it.",
        "It's two attacks at once, the moved piece and the one behind, and the moved piece can do anything, even "
        "attack something else.",
        "When their bishop, rook or queen has one of their own pieces in front of it, aimed at yours, be careful.",
    ], "Is there one of their pieces standing in front of their bishop, rook or queen, aimed at mine?", ["discoveredAttack"]),
    L("tac-develop", "tactics", "Opening: get your pieces out", ["development"], 0.4, [
        "In the opening the race is to bring your pieces into the game. A piece at home doesn't fight.",
        "Knights and bishops first, then castle, then the rooks. Move each piece once, not the same one twice.",
        "Don't bring the queen out early: they bring out a piece *and* attack her, and you've lost time.",
    ], "In the first ten moves: does this move bring out a new piece?", [], ("Your repertoire", "repertoire")),
    L("tac-centre", "tactics", "Opening: take the centre", ["centre"], 0.2, [
        "The four centre squares (d4, e4, d5, e5) are the high ground: pieces there reach everything.",
        "Start with a centre pawn (e4 or d4 as White, e5, d5 or c5 as Black), then put knights and bishops where "
        "they aim at the centre.",
        "Early edge pawn moves (a, b, g, h pawns) let them take the centre for free.",
    ], "Early on: does my move fight for the centre?", ["opening"], ("Your repertoire", "repertoire")),
    L("tac-castle", "tactics", "Castle early", ["king_safety"], 0.2, [
        "A king left in the middle gets attacked as soon as the centre opens.",
        "Castle in the first ten moves, usually on the king's side. It hides the king and brings a rook out in one move.",
        "Moving your king or rook before castling loses the right to castle for the whole game.",
    ], "Have I castled? If not, is anything stopping me?", ["exposedKing"]),
    L("tac-mate2", "tactics", "Checkmate in two", ["mate_finish"], 0.05, [
        "Many checkmates need two moves: a check that forces the king somewhere, then the mate.",
        "Look at checks that leave the king only one square, then ask what attacks that square.",
    ], "Their king is short of squares: which check forces it where I can mate it?", ["mateIn2", "smotheredMate"]),
    L("tac-tricks", "tactics", "Tricks a few moves deep", ["tactics"], 0.3, [
        "Some mistakes don't lose anything straight away: two or three moves later the material is gone.",
        "That's where calculation starts: after your move, look at their most forcing answers (checks, captures, "
        "threats), then your best reply, then theirs.",
        "If you can't see the end, choose the safer move.",
    ], "Forcing moves first: checks, captures, threats, for both sides.", ["attraction", "deflection"],
      ("See it in your head", "calc")),

    # ---------- Fewer mistakes: about 1,200 to 1,600 ----------
    L("club-shelter", "club", "Pawns in front of your king", ["king_safety"], 0.15, [
        "After castling, the three pawns in front of your king are its walls.",
        "Every step one of them takes opens a door: g3 or h3 can be fine, but pushing f, g and h pawns while their "
        "queen is on the board invites an attack.",
        "Push them only with a clear reason, and never two of them without one.",
    ], "Is this pawn part of my king's shelter? Do I really need to move it?", ["kingsideAttack", "exposedKing"]),
    L("club-defender", "club", "Remove the defender", ["defender"], 0.1, [
        "The other side of 'don't move the guard': find their guard and take it, or chase it away.",
        "If one of their pieces is defended only once, capture or attack the defender, and the piece falls.",
    ], "Which of their pieces is defended only once, and can I remove that defender?", ["capturingDefender", "deflection"]),
    L("club-active", "club", "Active pieces", ["activity"], 0.3, [
        "A piece's strength is how many useful squares it reaches. A knight on the edge reaches half as many as one "
        "in the middle.",
        "Rooks want open files (no pawns on them). Bishops want long, open diagonals.",
        "When nothing is happening, improve your worst piece.",
    ], "Which of my pieces does least? Can I give it a better square?", []),
    L("club-passed", "club", "Passed pawns", ["passed"], 0.15, [
        "A passed pawn has no enemy pawns in front of it or on the files next to it: only pieces can stop it.",
        "Yours: push it, with your pieces behind it. Theirs: stop it early, with a piece directly in front (a knight "
        "or king is the best blocker).",
        "The closer it gets, the more it's worth: a pawn on the seventh rank can be worth a whole rook.",
    ], "Does anyone have a passed pawn? Who's in front of it?", ["advancedPawn", "promotion"]),
    L("club-king", "club", "The king in the endgame", ["active_king"], 0.1, [
        "In the middlegame the king hides. In the endgame, with the queens gone, it becomes a strong piece.",
        "Bring it towards the centre early in the endgame: it supports your pawns and stops theirs.",
    ], "Queens off? Then my king walks to the middle.", ["pawnEndgame"], ("Pawn endings", "endgame/pawn")),
    L("club-pawns", "club", "Pawn weaknesses", ["pawns"], 0.15, [
        "Pawns can't move backwards, so pawn mistakes last the whole game.",
        "A doubled pawn (two on one file) and an isolated pawn (no pawn of yours on the files next to it) can't be "
        "guarded by another pawn: they need pieces to defend them.",
        "When you have a choice of how to take back, take towards the centre and keep your pawns together.",
    ], "Does this capture or pawn move leave me a pawn that no pawn can guard?", []),
    L("club-rook", "club", "Rook endgames", [], 0.0, [
        "Rook endings are the most common endings in chess.",
        "Rooks belong behind passed pawns, yours or theirs. An active rook is worth more than a pawn.",
    ], "Is my rook active, and behind the passed pawn?", ["rookEndgame"], ("Two rooks mate", "endgame/tworooks")),
    L("club-clock", "club", "Slow down when it matters", [], 0.0, [
        "Most big mistakes are played fast. The clock isn't the enemy: rushing at the critical moment is.",
        "Spend your time when something changes: a capture, a check, an attack. Play quickly when nothing does.",
    ], "Something just changed? Then I count to five and check before I move.", [], ("Slow-down drill", "clockdrill")),

    # ---------- Precision: about 1,600 to 2,000 ----------
    L("pre-calc", "precise", "See it in your head", ["tactics"], 0.15, [
        "Stronger players don't move until they've seen the end of the line.",
        "Look at the position after their best answer, then after your reply. If the board in your head blurs, go "
        "back one move and check again.",
    ], "Can I see the position three moves from now, clearly?", ["clearance", "interference"], ("See it in your head", "calc")),
    L("pre-intermezzo", "precise", "The in-between move", [], 0.0, [
        "Before taking back the obvious recapture, look for a check or a threat first: an in-between move.",
        "It wins time, changes what's attacked, and often wins material.",
    ], "Before the obvious move: is there a check or bigger threat first?", ["intermezzo"]),
    L("pre-quiet", "precise", "The quiet move", [], 0.0, [
        "Not every winning move is a check or a capture. Sometimes a calm move sets up a threat they can't stop.",
    ], "No forcing move works? Which quiet move creates two threats?", ["quietMove"]),
    L("pre-xray", "precise", "Clearance and X-rays", [], 0.0, [
        "Sometimes your own piece is in the way: move it with a threat, and a line opens for another.",
        "An X-ray is an attack through a piece: when that piece moves or is taken, the attack lands.",
    ], "Is one of my pieces blocking another's line?", ["clearance", "xRayAttack"]),
    L("pre-trapped", "precise", "Trapped pieces", [], 0.0, [
        "A piece with no safe squares can be won by simply attacking it.",
        "Bishops that grab a pawn deep in their side, and knights on the edge, get trapped most often.",
    ], "Where can this piece go next if it's attacked?", ["trappedPiece"]),
    L("pre-zugzwang", "precise", "Zugzwang", [], 0.0, [
        "In endgames, having to move can be a disadvantage: every move makes things worse.",
        "Kings facing each other with one square between (the opposition) is where it starts.",
    ], "In the endgame: what if it were their move here?", ["zugzwang", "pawnEndgame"]),
    L("pre-minor", "precise", "Bishop and knight endings", [], 0.0, [
        "Bishops love open boards and pawns on both sides; knights love closed positions and fixed pawns.",
    ], "Which minor piece does this pawn structure favour?", ["bishopEndgame", "knightEndgame"]),
    L("pre-hold", "precise", "Hold the draw", [], 0.0, [
        "A lost-looking ending is often a draw with the right defence: king in front of the pawn, and the opposition.",
    ], "Can my king get in front of their pawn?", [], ("Hold the draw", "endgame/holdpawn")),
    L("pre-iqp", "precise", "The isolated queen's pawn", [], 0.0, [
        "A pawn on d4 with no pawns beside it: weak in the endgame, but its owner gets space and attacking chances.",
    ], "Who does this pawn favour: the attacker now, or the defender later?", [],
      coming=NEEDS_ELITE, elite=["iqp", "hanging"]),
    L("pre-structures", "precise", "Your openings' pawn structures", [], 0.0, [
        "Your repertoire leads to the same pawn structures again and again. Knowing their plans is half the game.",
    ], "What does this structure ask me to do?", [],
      coming=NEEDS_ELITE, elite="repertoire"),

    # ---------- Expert: 2,000 and above ----------
    L("exp-attack", "expert", "Attacking the king", [], 0.0, [
        "An attack needs more attackers than there are defenders. Bring pieces first, break open the king second.",
    ], "Do I have more pieces near their king than they have defending it?", ["kingsideAttack"]),
    L("exp-queen", "expert", "Queen endings", [], 0.0, [
        "Queen endings are about checks: the side whose king hides better wins.",
    ], "Where can my king hide from their checks?", ["queenEndgame"], ("Queen against a pawn", "endgame/queenpawn")),
    L("exp-convert", "expert", "Converting an advantage", [], 0.0, [
        "Up material: trade pieces, not pawns, and take away their counterplay before going for more.",
    ], "Ahead: what's their only chance, and can I take it away first?", []),
    L("exp-prophylaxis", "expert", "What do they want?", [], 0.0, [
        "Before your own plan, ask what your opponent wants to do next, and stop it.",
    ], "If it were their move, what would they play?", [],
      coming="Coming later: it needs explanations of quiet plans, which the coach can't check on the board yet."),
    L("exp-plans", "expert", "Plans from strong players' games", [], 0.0, [
        "How 2,400+ players handle the positions your openings give you.",
    ], "What would a strong player do here, and why?", [],
      coming=NEEDS_ELITE, elite=["sicilian", "french", "kid", "italian", "caro", "carlsbad"]),
]
BY_ID = {l["id"]: l for l in LESSONS}


# ---------- your games: which ideas cost you ----------
_TAGS = {"key": None, "tags": None}


def tags(moves=None):
    """Every mistake in your checked games with its reason: {url: [(ply, idea, loss)]} (worked out once per file)."""
    from coach import why
    moves = moves if moves is not None else insights._moves()
    key = (id(moves), sum(len(v) for v in moves.values()))
    if _TAGS["key"] != key:
        out = collections.defaultdict(list)
        for url, rows in moves.items():
            for r in rows:
                if r["loss"] >= MISTAKE:
                    try:
                        out[url].append((r["ply"], why.explain(r)["idea"], r["loss"]))
                    except (ValueError, KeyError, AssertionError):
                        continue
        _TAGS.update(key=key, tags=out)
    return _TAGS["tags"]


def rates(games, tagged):
    """Mistakes a game for each idea, over these games."""
    if not games:
        return {}
    count = collections.Counter(idea for g in games for _, idea, _ in tagged.get(g["url"], []))
    return {idea: n / len(games) for idea, n in count.items()}


def _state():
    try:
        return json.loads(FILE.read_text())
    except (OSError, ValueError):
        return {}


def _save(s):
    FILE.parent.mkdir(parents=True, exist_ok=True)
    FILE.write_text(json.dumps(s))


def _end_time(g):
    return g.get("end_time") or 0


def studied(lid, right, total, today=None):
    """You finished a lesson's practice: remembered with the date, so only the games after it judge the lesson."""
    s = _state()
    now = (today or datetime.datetime.now()).timestamp()
    entry = s.setdefault(lid, {})
    entry.update(studied=now, right=int(right), total=int(total), times=entry.get("times", 0) + 1)
    _save(s)
    return entry


def course(games=None, moves=None, player=None, current=None):
    """Every lesson with its status and your numbers, and the one to do next."""
    player = player or insights._player()
    games = games if games is not None else insights._games()
    moves = moves if moves is not None else insights._moves()
    checked = [g for g in games if g["url"] in moves]
    recent = checked[:WINDOW]
    tagged = tags(moves)
    now_rates = rates(recent, tagged)
    state = _state()
    if current is None:
        from coach import ladder
        lad = ladder.ladder(games, moves, player) if player and recent else None
        current = LEVEL_ORDER[lad["current"]] if lad else "safe"
    top = LEVEL_ORDER.index(current)
    out = []
    for l in LESSONS:
        lvl = LEVEL_ORDER.index(l["level"])
        rate = sum(now_rates.get(i, 0) for i in l["ideas"]) if l["ideas"] else None
        st = state.get(l["id"], {})
        after = [g for g in checked if st.get("studied") and _end_time(g) > st["studied"]]
        after_rate = sum(rates(after[:WINDOW], tagged).get(i, 0) for i in l["ideas"]) if after and l["ideas"] else None
        if l["coming"] and not _structures(l):
            status = "coming"
        elif st.get("studied") and l["ideas"] and len(after) >= AFTER and after_rate <= l["goal"]:
            status = "passed"
        elif st.get("studied") and not l["ideas"]:
            status = "passed"  # nothing to measure in your games: done when practised
        elif st.get("studied"):
            status = "watching" if len(after) < AFTER else "again"
        elif lvl > top:
            status = "later"
        elif rate is not None and recent and rate <= l["goal"] * FINE:
            status = "fine"
        else:
            status = "open"
        out.append({"id": l["id"], "level": l["level"], "title": l["title"], "status": status, "goal": l["goal"],
                    "rate": None if rate is None else round(rate, 2), "ideas": l["ideas"],
                    "after": len(after), "after_rate": None if after_rate is None else round(after_rate, 2),
                    "train": l["train"], "coming": l["coming"], "habit": l["habit"]})
    nxt = _next(out, top)
    if nxt:
        nxt["next"] = True
    return {"player": player, "games": len(recent), "level": current, "levels": LEVEL_NAME,
            "lessons": out, "next": nxt["id"] if nxt else None}


def _next(rows, top):
    """The lesson to do now: the one whose mistake costs you most against its goal, at your level or below; else the
    first one not done in order."""
    able = [r for r in rows if r["status"] in ("open", "again") and LEVEL_ORDER.index(r["level"]) <= top]
    hurting = [r for r in able if r["rate"] is not None and r["rate"] > r["goal"]]
    if hurting:
        return max(hurting, key=lambda r: (r["rate"] / max(r["goal"], 0.05), -LESSONS.index(BY_ID[r["id"]])))
    return able[0] if able else None


def reason(row):
    """Why this lesson, in one sentence from your numbers."""
    if row["status"] == "fine":
        return f"You already do this well: {row['rate']} a game in your last {WINDOW} games ({_counted(row)})."
    if row["status"] == "watching":
        return f"Studied. Now your games decide: {row['after']} of {AFTER} games played since."
    if row["status"] == "again":
        return (f"Studied, but it still happens: {row['after_rate']} a game since, the goal is {row['goal']}. "
                f"One more time.")
    if row["status"] == "passed":
        return "Done: the mistake dropped in the games you played after it."
    if row["rate"]:
        return f"In your last {WINDOW} games: {row['rate']} a game ({_counted(row)}). The goal is {row['goal'] or 'none at all'}."
    return ""


def _counted(row):
    from coach.why import COUNTED
    return " or ".join(COUNTED[i] for i in row["ideas"] if i in COUNTED)


def examples(lid, moves=None, n=3):
    """Your own moves with this lesson's mistake: the clearest ones (slow games, biggest loss), one per game."""
    l = BY_ID[lid]
    moves = moves if moves is not None else insights._moves()
    tagged = tags(moves)
    found = []
    for url, rows in moves.items():
        ideas = {ply: idea for ply, idea, _ in tagged.get(url, [])}
        for r in rows:
            if ideas.get(r["ply"]) in l["ideas"]:
                found.append(r)
    found.sort(key=lambda r: (r["time_class"] == "bullet", -r["loss"]))
    seen, out = set(), []
    for r in found:
        if r["url"] not in seen:
            seen.add(r["url"])
            out.append(r)
        if len(out) == n:
            break
    return out


def lesson(lid, engine, rating=None, rng=None):
    """One lesson ready to teach: the text, the habit, your own positions as practice (each with its reason), and
    Lichess puzzles on the same idea at your level."""
    import random

    from coach import drills, plan, why
    l = BY_ID[lid]
    rng = rng or random.Random(lid + datetime.date.today().isoformat())
    own = []
    for r in examples(lid, n=2):
        d = drills.drill(engine, r.get("pattern") or "", r)
        d["why"] = why.explain(r, engine)["say"]
        d["hint"] = l["habit"]
        own.append(d)
    puzzles = []
    for theme in l["themes"][:2]:
        puzzles += plan._puzzles(theme, rating, rng)[:2 if len(l["themes"]) > 1 else 3]
    for p in puzzles:
        p["hint"] = l["habit"] + " " + p.get("hint", "")
    from coach import elite
    lib, teach = elite.library(), list(l["teach"])
    for key in _structures(l):
        st = lib[key]
        side = "White" if st["owner"] == "white" else "Black"
        teach.append(f"{st['name']}. For {side}: {st['plan']['owner']} For the other side: {st['plan']['other']}")
        puzzles += st["drills"][:4]
    row = next(r for r in course()["lessons"] if r["id"] == lid)
    return {**l, "kind": "course", "coach": "viktor",
            "status": row["status"], "reason": reason(row), "rate": row["rate"],
            "teach": teach, "intro": teach[0], "drills": own + puzzles}


def _structures(l):
    """The pawn structures a lesson practises that the strong players' library has, or []."""
    if not l.get("elite"):
        return []
    from coach import elite
    lib = elite.library()
    keys = l["elite"]
    if keys == "repertoire":
        try:
            from coach import repertoire
            names = [x["name"] for x in json.loads(repertoire.FILE.read_text())]
        except (OSError, ValueError, KeyError):
            names = []
        keys = [k for n in names for word, k in REPERTOIRE_STRUCTURES.items() if word in n] or ["italian", "caro", "carlsbad"]
    return [k for k in dict.fromkeys(keys) if lib.get(k, {}).get("drills")]


def lesson_for(idea):
    """The first lesson that teaches this idea (the review links each mistake to it), or None."""
    return next((l for l in LESSONS if idea in l["ideas"] and not l["coming"]), None)
