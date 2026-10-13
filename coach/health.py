"""The chess.com self-check: is everything Knightwise depends on still there?

chess.com changes its site without telling anyone (13 Oct 2026: live games moved from /game/live/<id> to
/game/<id> and /live/game/<id>, and the review silently stopped appearing). Every dependency is checked where it
is used: the extension reports what it finds on chess.com's pages, the app checks the public API on every download.
A broken check pauses only that feature, with an honest line about it; Settings shows the whole picture.

Kept in data/health.json: check -> {ok, detail, at, last_ok}.
"""
import json
import time

from coach.paths import DATA

FILE = DATA / "health.json"

# check -> (what it is, what the player is told while it's broken). The extension's list of the same names is in
# extension/contract.js: keep the two in step.
CHECKS = {
    "game-address": ("chess.com's game page address",
                     "chess.com changed its game page address, so reviews don't open there. Open them in Knightwise."),
    "board": ("chess.com's board on a game page",
              "chess.com changed its board, so the arrows can't be drawn. The review is in Knightwise."),
    "pieces": ("the pieces on chess.com's board",
               "chess.com changed how it shows the pieces, so the arrows can't be placed. The review is in Knightwise."),
    "player-names": ("the players' names on a game page",
                     "chess.com changed its game page, so Knightwise can't confirm it's your game. The review is in Knightwise."),
    "move-list": ("the move list on a game page",
                  "chess.com changed its move list, so clicking a moment doesn't jump there. Step to it with the arrows."),
    "api-archives": ("chess.com's list of your monthly games",
                     "chess.com's game service changed or is down, so new games can't be downloaded. Your old games are safe."),
    "api-games": ("the details of each game from chess.com",
                  "chess.com changed the details it sends for each game, so new games can't be checked yet."),
}
GAME_FIELDS = ("url", "pgn", "end_time", "time_class", "rules")
SIDE_FIELDS = ("username", "rating", "result")


def _load():
    try:
        return json.loads(FILE.read_text())
    except (OSError, ValueError):
        return {}


def record(check, ok, detail="", now=None):
    """Note what a check found. Only known checks are kept (the extension can't fill the file with anything)."""
    if check not in CHECKS:
        return False
    now = now or time.time()
    h = _load()
    entry = h.get(check, {})
    entry.update(ok=bool(ok), detail=str(detail)[:200], at=now)
    if ok:
        entry["last_ok"] = now
    h[check] = entry
    FILE.parent.mkdir(parents=True, exist_ok=True)
    FILE.write_text(json.dumps(h))
    return True


def summary():
    """For Settings and the extension pop-up: all working (and when that was last seen), or what broke."""
    h = _load()
    broken = [{"check": c, "what": CHECKS[c][0], "says": CHECKS[c][1], "detail": e.get("detail", ""), "since": e["at"]}
              for c, e in h.items() if c in CHECKS and not e.get("ok")]
    oks = [e["last_ok"] for e in h.values() if e.get("last_ok")]
    return {"ok": not broken, "broken": broken, "verified": max(oks) if oks else None,
            "seen": sorted(c for c in h if c in CHECKS)}


def says(check):
    """The honest line for a broken check, or None while it works."""
    e = _load().get(check)
    return CHECKS[check][1] if e and not e.get("ok") else None


def missing_fields(payload):
    """What a month of games from chess.com's API lacks, compared with what Knightwise reads. [] when complete."""
    if not isinstance(payload, dict) or not isinstance(payload.get("games"), list):
        return ["games"]
    missing = set()
    for g in payload["games"]:
        missing |= {f for f in GAME_FIELDS if f not in g}
        for side in ("white", "black"):
            if not isinstance(g.get(side), dict):
                missing.add(side)
            else:
                missing |= {f"{side}.{f}" for f in SIDE_FIELDS if f not in g[side]}
    return sorted(missing)
