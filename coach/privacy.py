"""Opponents' names never go to the AI company (owner, 28 Nov 2026).

Before anything is sent to the AI (Groq or Gemini), every opponent's chess.com name becomes "Opponent A",
"Opponent B"... and in the answer the real names are put back, so the player still reads "Against sreejit…". The AI
only ever sees the letters. A name the player types (even misspelled: "rematch sreejt") is swapped too, with the same
"close name" rule the rematch already uses (talk.find_game), so asking by name keeps working.

The player's own name is not hidden (it's their own data, and the coach greets them by it).
"""
import difflib
import re

# everyday words in a chat with the coach: never mistaken for a misspelled name
COMMON = set("""a about after again against all also am an and any are as ask at back bad be because been before
best better black blunder board but by can check checkmate coach could day did do does draw end ended endgame even
every fork from game games gave get give go good got had has have he help her here him his how i if in into is it its
just know last least let like line lose losing loss lost made make match mate me mistake more most move moves much my
need never next no not now of off on one only open opening or other our out over piece pieces play played player
playing please position practice queen rematch resign resigned review right same say see she should show so some
start still take than thank thanks that the their them then there these they thing think this time to today too try
up us very want was we well were what when where which who why will win with won would yes yesterday you your
king rook bishop knight pawn chess castle castling attack defence defense tactic tactics gambit pin skewer""".split())

ALIAS = re.compile(r"\bopponent ([A-Z]{1,2})\b", re.I)


def _squash(t):
    return "".join(c for c in str(t).lower() if c.isalnum())


def _label(i):
    """A, B, ... Z, AA, AB ..."""
    return chr(65 + i) if i < 26 else chr(65 + i // 26 - 1) + chr(65 + i % 26)


class Aliases:
    """The names to hide, most relevant first (the last game's opponent is Opponent A)."""

    def __init__(self, names, fuzzy=None):
        self.alias, self.real = {}, {}
        for n in names:
            n = str(n or "").strip()
            if n and n.lower() not in self.alias:
                a = f"Opponent {_label(len(self.alias))}"
                self.alias[n.lower()], self.real[a.lower()] = a, n
        # misspellings are matched only against these (the names in the facts), to keep false matches rare
        self.fuzzy = [str(n) for n in (fuzzy if fuzzy is not None else names) if n]
        # in free text only names that can't be an everyday word ("king" stays "king"; its opponent field is still hidden)
        names_sorted = sorted((n for n in self.alias if n not in COMMON and len(n) >= 3), key=len, reverse=True)
        self._exact = re.compile("|".join(rf"(?<![\w-]){re.escape(n)}(?![\w-])" for n in names_sorted), re.I) \
            if names_sorted else None

    def hide(self, text):
        """Every exact name (any capitals) becomes its alias."""
        if not self._exact or not text:
            return text
        return self._exact.sub(lambda m: self.alias[m.group(0).lower()], str(text))

    def hide_facts(self, facts):
        """The facts as JSON text for the AI: every "opponent" field by its alias, then any name left in the text."""
        def walk(x):
            if isinstance(x, dict):
                return {k: (self.alias.get(str(v).lower(), v) if k == "opponent" and isinstance(v, str) else walk(v))
                        for k, v in x.items()}
            if isinstance(x, list):
                return [walk(v) for v in x]
            return x
        import json
        return self.hide(json.dumps(walk(facts)))

    def _near(self, span):
        """The one opponent a typed word (or two) means, or None."""
        s = _squash(span)
        if len(s) < 4 or s in COMMON:
            return None
        names = {_squash(n): n for n in self.fuzzy}
        if s in names:
            return names[s]
        starts = [n for q, n in names.items() if q.startswith(s)]
        if len(starts) == 1:
            return starts[0]
        if len(s) >= 5:
            near = difflib.get_close_matches(s, list(names), n=2, cutoff=0.85)
            if len(near) == 1:
                return names[near[0]]

            def start_like(q):  # a typo in the start of a long name: "sreejt" for SreejitDebnath
                return max(difflib.SequenceMatcher(None, s, q[:k]).ratio() for k in range(len(s) - 1, len(s) + 3))
            near = [n for q, n in names.items() if start_like(q) >= 0.85]
            if len(near) == 1:
                return near[0]
        return None

    def hide_said(self, text):
        """What the player typed or said: exact names, then a close name ("sreejt", "sreejit debnath")."""
        text = self.hide(text)
        if not text or not self.fuzzy:
            return text
        words = list(re.finditer(r"[\w-]+", text))
        out, i, last = [], 0, 0
        while i < len(words):
            w = words[i]
            if w.group(0).lower() == "opponent":  # already an alias ("Opponent A"): leave it and its letter
                i += 2
                continue
            hit, end = None, w.end()
            if i + 1 < len(words) and text[w.end():words[i + 1].start()].strip() == "":  # two words: "sreejit debnath"
                hit = self._near(w.group(0) + words[i + 1].group(0))
                end = words[i + 1].end() if hit else end
                i += 1 if hit else 0
            if not hit:
                hit = self._near(w.group(0))
            if hit and hit.lower() in self.alias:
                out.append(text[last:w.start()] + self.alias[hit.lower()])
                last = end
            i += 1
        return "".join(out) + text[last:]

    def show(self, obj):
        """The AI's answer with the real names back in (strings inside dicts and lists too)."""
        if isinstance(obj, str):
            return ALIAS.sub(lambda m: self.real.get(f"opponent {m.group(1).lower()}", m.group(0)), obj)
        if isinstance(obj, dict):
            return {self.show(k): self.show(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self.show(v) for v in obj]
        return obj


def for_games(games, home=None):
    """Aliases for the opponents the AI's facts would name: the recent games, then every other checked game (an old
    opponent the player mentions is hidden too)."""
    recent = [g.get("opponent") for g in games or [] if g.get("opponent")]
    last = ((home or {}).get("last_game") or {}).get("opponent")
    try:
        from coach import insights
        every = [g.get("opponent") for g in insights.games_list() if g.get("opponent")]
    except Exception:
        every = []
    return Aliases(([last] if last else []) + recent + every, fuzzy=([last] if last else []) + recent)
