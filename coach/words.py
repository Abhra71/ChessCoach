"""Chess words, layer 1 (storyline step 3.4, docs/STORYLINE.md section 6): the 33 words strong players use, each in
one plain line. In the app the first time a word appears on a page it's underlined; a tap (not a hover: it must work
on touch too) shows its meaning. All of them are on the Chess words page, part of the library (Your plan).

Layers 2 (club, ~60) and 3 (advanced, ~80) come with the Book. data/words.json keeps which words the player looked
up, so Viktor can point at the whole list once they've started using it.
"""
import datetime
import json

from coach.paths import DATA

FILE = DATA / "words.json"
LAYER = 1
LOOKED_UP = 3  # after this many different words, Viktor points at the whole list (coach/nudge.py, kind "words")

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
    """The Chess words page and the app's underlining: {layer, words: [{word, meaning, forms}], looked}."""
    return {"layer": LAYER, "words": [{"word": w, "meaning": m, "forms": f} for w, m, f in WORDS],
            "looked": sorted(_load().get("looked", {}))}


def _load():
    try:
        return json.loads(FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def looked_up(word, day=None):
    """The player tapped a word for its meaning."""
    if word not in {w for w, _, _ in WORDS}:
        return False
    d = _load()
    d["looked"] = {**d.get("looked", {}), word: (day or datetime.date.today()).isoformat()}
    try:
        FILE.parent.mkdir(parents=True, exist_ok=True)
        FILE.write_text(json.dumps(d), encoding="utf-8")
    except OSError:
        return False
    return True


def count_looked():
    return len(_load().get("looked", {}))
