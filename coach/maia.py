"""The human-move model (0.11): Maia, which plays like a human of a given rating.

Maia (University of Toronto / CSSLab, GPL-3.0) is nine small neural networks, one per rating from 1,100 to 1,900, each
trained on millions of real Lichess games at that rating. Run by Leela (lc0, GPL-3.0) with one node, it doesn't
search: it answers "what would a 1,300 player play here?", mistakes included, with a probability for every move.
Called "the human-move model" in the app, so it's never confused with Maya the coach.

Uses: the rematch and sparring opponent plays like a person of their level; the review says what players at your
level play and what the next level plays. Off unless the player switches it on in Settings (it runs on the PC).
One Leela process per rating (switching networks in one process keeps the old answers in its cache, 14 Oct test).
"""
import re
import subprocess
import sys
import threading
from collections import OrderedDict

import chess
import chess.engine

from coach.paths import APP

LC0 = APP / "engine" / "lc0" / "lc0.exe"
NETS = APP / "engine" / "maia"
RATINGS = list(range(1100, 2000, 100))
OPEN_MAX = 3  # Leela processes kept open at once; the oldest closes first
FLOOR = 0.5  # moves under 0.5% are never played (Maia's long tail is noise)
_engines = OrderedDict()
LOCK = threading.Lock()
_MOVE = re.compile(r"(\S+)\s.*\(P:\s*([\d.]+)%\)")


def available():
    return LC0.exists() and all((NETS / f"maia-{r}.pb.gz").exists() for r in RATINGS)


def enabled():
    from coach import settings
    return available() and bool(settings.load().get("human_moves"))


def nearest(rating):
    """The Maia closest to a rating (1,100 below, 1,900 above)."""
    return min(RATINGS, key=lambda r: abs(r - (rating or 1100)))


def _engine(r):
    """The Leela process for one rating (opened on first use; call inside LOCK)."""
    if r in _engines:
        _engines.move_to_end(r)
        return _engines[r]
    while len(_engines) >= OPEN_MAX:
        _, old = _engines.popitem(last=False)
        try:
            old.quit()
        except chess.engine.EngineError:
            pass
    quiet = {"creationflags": subprocess.CREATE_NO_WINDOW} if sys.platform == "win32" else {}
    eng = chess.engine.SimpleEngine.popen_uci([str(LC0), f"--weights={NETS / f'maia-{r}.pb.gz'}"],
                                              stderr=subprocess.DEVNULL, **quiet)
    eng.configure({"VerboseMoveStats": True})
    _engines[r] = eng
    return eng


def close():
    with LOCK:
        while _engines:
            try:
                _engines.popitem()[1].quit()
            except chess.engine.EngineError:
                pass


# Leela's open engines keep threads that Python waits for at exit: close them first (14 Oct test: exit hung)
threading._register_atexit(close)


def policy(board, rating):
    """{move: chance in %} that a player of about this rating plays each legal move."""
    r = nearest(rating)
    out = {}
    with LOCK:
        with _engine(r).analysis(board, chess.engine.Limit(nodes=1), info=chess.engine.INFO_ALL) as an:
            for info in an:
                s = info.get("string")
                m = _MOVE.match(s) if s and not s.startswith("node") else None
                if m:
                    try:
                        move = chess.Move.from_uci(m.group(1))
                    except ValueError:
                        continue
                    if move in board.legal_moves:
                        out[move] = float(m.group(2))
    return out


def pick(board, rating, rng):
    """A move as a player of this rating might play it: drawn by Maia's own chances, so it's human, not perfect."""
    p = {m: v for m, v in policy(board, rating).items() if v >= FLOOR}
    if not p:
        return None
    moves = list(p)
    return rng.choices(moves, weights=[p[m] for m in moves])[0]


def compare(fen, played, best, rating):
    """What players at your level play here, and what stronger players play: a sentence for the review, or None.
    played, best: SAN of the move you played and the engine's best."""
    board = chess.Board(fen)
    mine, strong = nearest(rating), min(nearest(rating) + 400, RATINGS[-1])
    try:
        you, them = policy(board, mine), policy(board, strong)
    except (chess.engine.EngineError, OSError):
        return None
    if not you or not them:
        return None
    pm, bm = board.parse_san(played), board.parse_san(best)
    share = lambda p, m: round(p.get(m, 0))
    top_strong = max(them, key=them.get)
    ahead = (rating or 0) < RATINGS[0] - 100  # below Maia's first level: speak of the levels ahead, not "yours"
    level = f"At {mine:,}, a level ahead of you," if ahead else f"At about {mine:,},"
    you_pc, them_pc = share(you, pm), share(them, pm)
    out = f"{level} almost no one plays {played} here" if you_pc < 1 else f"{level} {you_pc}% of players play {played} here"
    if strong == mine:
        return out + "."
    if top_strong == pm:
        return out + f", and at {strong:,} it's the most played move ({them_pc}%): a natural mistake, so it's worth knowing."
    if you_pc >= 1:
        out += f"; at {strong:,}, {'fewer do' if them_pc < you_pc else 'about as many do' if them_pc == you_pc else 'more do'} ({them_pc}%)"
    if you_pc >= 1:
        out += f", and the most played there is {board.san(top_strong)} ({share(them, top_strong)}%)"
    else:  # 19 Oct: not "here; and the most played at 1,500 is"
        out += f". At {strong:,}, the most played move is {board.san(top_strong)} ({share(them, top_strong)}%)"
    if top_strong != bm and share(them, bm):
        out += f". The best, {best}, is played by {share(them, bm)}%"
    return out + "."
