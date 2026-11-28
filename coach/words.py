"""Chess words, layer 1 (storyline step 3.4, docs/STORYLINE.md section 6): the 33 words strong players use, each in
one plain line, learned one at a time (owner, 28 Nov):
- a coach introduces a word, with a reason (your game just showed a fork) or sometimes just because;
- the first time the player meets a word it has a small dotted line: hover or tap shows its meaning;
- after that it's normal text, and the coaches simply use it. data/words.json keeps the words met.
All of them are on the Chess words page, part of the library (Your plan).

Layers 2 (club, ~60) and 3 (advanced, ~80) come with the Book. data/words.json keeps which words the player looked
up, so Viktor can point at the whole list once they've started using it.
"""
import datetime
import json
import threading
import time

from coach.paths import DATA

FILE = DATA / "words.json"
_LOCK = threading.Lock()  # two words met at once both arrive: one read-change-write at a time (28 Nov)
LAYER = 1
LOOKED_UP = 3  # after this many different words, Viktor points at the whole list (coach/nudge.py, kind "words")
JUST_SAYING = 3  # a word without a reason: every few days (owner, 29 Nov: the words should actually be heard)
NEW_PER_PAGE = 2  # the app underlines at most this many new words on one page (coach/ui/club.js): never busy

# (word, its plain meaning, the forms underlined in the app's text; empty: only on the Chess words page, because the
# word is too everyday to underline, like "mistake" or "the centre")
WORDS = [
    ("Notation", "How moves are written: piece letter + square. Nf3 = knight to f3; x = takes; O-O = castles.", []),
    ("Candidate moves", "The 2–3 moves worth thinking about before you choose.", ["candidate moves"]),
    ("Hanging piece", "A piece that can be taken for free.", ["hanging piece", "hanging"]),
    ("Blunder, mistake, inaccuracy", "Big, medium and small slips, measured by the engine.",
     ["blunder", "blunders", "inaccuracy", "inaccuracies"]),
    ("Fork", "One piece attacks two at once.", ["fork", "forks", "forked"]),
    ("Pin", "A piece can't move without exposing a bigger one behind it.", ["pin", "pins", "pinned"]),
    ("Skewer", "A pin in reverse: the big piece is in front and must move.", ["skewer", "skewers"]),
    ("Discovered attack", "Moving one piece uncovers an attack by another.", ["discovered attack", "discovered check"]),
    ("Double attack", "Two threats at once; they can only stop one.", ["double attack"]),
    ("In-between move (zwischenzug)", "A surprise move played before the expected recapture.",
     ["in-between move", "zwischenzug"]),
    ("Tempo", "One move of time; \"gaining a tempo\" means making them waste one.", ["tempo", "tempi"]),
    ("Development", "Getting pieces off the back row and into play.", ["development"]),
    ("The centre", "The four middle squares; whoever controls them usually has more space.", []),
    ("Fianchetto", "A bishop on the long diagonal after a pawn steps forward (g3 and Bg2).", ["fianchetto"]),
    ("Gambit", "A pawn given early for speed or attack.", ["gambit"]),
    ("Theory, book move", "Moves well known from master games.", ["book move", "opening theory"]),
    ("Novelty", "A move never played before in that position.", ["novelty"]),
    ("Transposition", "Different move orders reaching the same position.", ["transposition", "transposes"]),
    ("Open file", "A column with no pawns: a highway for rooks.", ["open file", "open files"]),
    ("Outpost", "A safe square in their half where a piece can't be chased by pawns.", ["outpost", "outposts"]),
    ("Weak square", "A square the opponent's pawns can no longer guard.", ["weak square", "weak squares"]),
    ("Pawn structure", "The shape of the pawns; it decides the plans.", ["pawn structure"]),
    ("Isolated pawn", "A pawn with no friendly pawns beside it.", ["isolated pawn"]),
    ("Passed pawn", "A pawn no enemy pawn can stop on its way to queen.", ["passed pawn", "passed pawns"]),
    ("Initiative", "Making threats so they're busy answering, not planning.", ["initiative"]),
    ("Prophylaxis", "Stopping their plan before it starts.", ["prophylaxis"]),
    ("Compensation", "Something worth the material you gave up.", ["compensation"]),
    ("Back-rank mate", "Mate on the back row, the king trapped by its own pawns.", ["back-rank mate", "back rank"]),
    ("Opposition", "Kings facing each other with one square between; whoever has to move gives way.", ["opposition"]),
    ("Zugzwang", "Any move makes it worse, but you must move.", ["zugzwang"]),
    ("Stalemate", "No legal move but not in check: a draw.", ["stalemate", "stalemated"]),
    ("Perpetual check", "Checks forever: a draw.", ["perpetual check", "perpetual"]),
    ("Tablebase", "A perfect answer book for endgames with few pieces.", ["tablebase", "tablebases"]),
]


def page():
    """The Chess words page and the app's underlining: {layer, words: [{word, meaning, forms}], looked, met}."""
    d = _load()
    return {"layer": LAYER, "words": [{"word": w, "meaning": m, "forms": f} for w, m, f in WORDS],
            "looked": sorted(d.get("looked", {})), "met": sorted(d.get("met", {})), "per_page": NEW_PER_PAGE}


def _load():
    try:
        return json.loads(FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def looked_up(word, day=None):
    """The player tapped (or hovered) a word for its meaning."""
    return _mark("looked", word, day)


def count_looked():
    return len(_load().get("looked", {}))


def _mark(key, word, day=None):
    if word not in {w for w, _, _ in WORDS}:
        return False
    with _LOCK:
        d = _load()
        d[key] = {**d.get(key, {}), word: (day or datetime.date.today()).isoformat()}
        try:
            FILE.parent.mkdir(parents=True, exist_ok=True)
            FILE.write_text(json.dumps(d), encoding="utf-8")
        except OSError:
            return False
    return True


def met(word, day=None):
    """The player has met this word (it was underlined in front of them): from now on it's ordinary text."""
    return _mark("met", word, day)


def introduced(word, day=None):
    """A coach introduced this word."""
    return _mark("introduced", word, day)


def introduced_today(day=None):
    return (day or datetime.date.today()).isoformat() in _load().get("introduced", {}).values()


TACTICS = {"Candidate moves", "Hanging piece", "Blunder, mistake, inaccuracy", "Fork", "Pin", "Skewer",
           "Discovered attack", "Double attack", "In-between move (zwischenzug)", "Back-rank mate"}  # Maya's; the rest Viktor's
VALUE = {1: 1, 2: 3, 3: 3, 4: 5, 5: 9, 6: 100}  # pawn .. king (python-chess piece types)


def forked(r):
    """Their reply to this move attacks two of the player's pieces worth a knight or more (or the king) at once."""
    import chess
    try:
        b = chess.Board(r["fen"])
        me = b.turn
        b.push_san(r["move"])
        reply = chess.Move.from_uci((r.get("reply_pv") or [""])[0])
        b.push(reply)
        hit = []
        for s in b.attacks(reply.to_square):
            p = b.piece_at(s)
            if p and p.color == me and VALUE[p.piece_type] >= 3:
                hit.append(s)
        return len(hit) >= 2 and VALUE[b.piece_at(reply.to_square).piece_type] < 100
    except Exception:
        return False


def introductions(home, games, player, day):
    """[(word, coach, line)]: the words a coach could introduce today. First those the player's newest game just
    showed (the reason), else, at most once a week, the next word in the list (just because). Never a word met before."""
    from coach import insights
    d = _load()
    known = set(d.get("met", {})) | set(d.get("introduced", {}))
    out = []
    last = home.get("last_game") or {}
    if games and last.get("id") and time.time() - (last.get("end_time") or 0) < 3 * 86400:
        g = next((x for x in games if insights.game_id(x["url"]) == str(last["id"])), None)
        rows = insights._moves().get(g["url"], []) if g else []
        opp = last.get("opponent") or "them"

        def said(w):
            return w in known or w in [o[0] for o in out]
        for r in rows:
            if not said("Fork") and forked(r):
                out.append(("Fork", "maya", f"Against {opp}, one of their pieces attacked two of yours at once. "
                            "That's called a fork: one piece, two targets."))
            if not said("Hanging piece") and r.get("pattern") == "left a piece hanging":
                out.append(("Hanging piece", "maya", f"Against {opp} you left a piece where it could be taken for "
                            "free. Players call that a hanging piece."))
            if not said("Stalemate") and r.get("pattern") == "stalemated a won game":
                out.append(("Stalemate", "viktor", f"You were winning against {opp}, but their king had no legal "
                            "move and wasn't in check. That's stalemate, and it's only a draw."))
            if not said("Blunder, mistake, inaccuracy") and r.get("pattern"):
                out.append(("Blunder, mistake, inaccuracy", "maya", f"Your biggest slip against {opp} is what "
                            "engines call a blunder: one move that throws a lot away."))
    if out:
        return out
    recent = (day - datetime.timedelta(days=JUST_SAYING)).isoformat()
    if any(v > recent for v in d.get("introduced", {}).values()):
        return []
    for w, m, forms in WORDS:
        if w not in known and forms:
            coach = "maya" if w in TACTICS else "viktor"
            return [(w, coach, f"A chess word for you: {forms[0]}. {m}")]
    return []
