"""The number check (run with Knightwise open: python tools/number_check.py): every statistic the app shows, recounted from the raw files and compared with what the app says.
Only coach.patterns.classify (one move's label) is borrowed; every sum, average, streak and window is counted here."""
import collections
import glob
import json
import os
import sys
import time
import urllib.request

import chess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from coach.patterns import classify  # noqa: E402

DATA = os.environ.get("KNIGHTWISE_DATA") or os.path.join(os.environ["TEMP"], "knightwise-test", "data")  # the test copy by default
API = "http://127.0.0.1:8765"
get = lambda p: json.load(urllib.request.urlopen(API + p, timeout=180))
LOSING = ("left a piece hanging", "walked into a fork or trick")
DRAWS = ("agreed", "repetition", "stalemate", "insufficient", "50move", "timevsinsufficient")
bad, ok = [], 0


def check(name, mine, app, tol=0.011):
    global ok
    same = (abs(mine - app) <= tol) if isinstance(mine, (int, float)) and isinstance(app, (int, float)) else mine == app
    if same:
        ok += 1
    else:
        bad.append(f"{name}: recount {mine!r}, app {app!r}")


player = open(os.path.join(DATA, "player.txt")).read().strip().lower()
raw, seen_urls = [], set()
for f in sorted(glob.glob(os.path.join(DATA, "games-*.json"))):
    for g in json.load(open(f))["games"]:
        if g["url"] not in seen_urls:
            seen_urls.add(g["url"])
            raw.append(g)
games = sorted([g for g in raw if g.get("rules") == "chess"], key=lambda g: -g["end_time"])
rows = collections.defaultdict(list)
for line in open(os.path.join(DATA, "moves.jsonl")):
    r = json.loads(line)
    r["pattern"] = classify(r)
    rows[r["url"]].append(r)
checked = [g for g in games if g["url"] in rows]
side = lambda g: ("white", "black") if g["white"]["username"].lower() == player else ("black", "white")


def result(g):
    me = side(g)[0]
    code = g[me]["result"]
    return "win" if code == "win" else "draw" if code in DRAWS else "loss"


print(f"files: {len(raw)} games, {len(games)} standard chess, {len(checked)} checked")
not_checked = [g["url"] for g in games if g["url"] not in rows]
print("not checked:", not_checked)

home = get("/api/home")
check("games checked", len(checked), home["games"])
check("results", dict(collections.Counter(result(g) for g in checked)), home["results"])
rapid = [g for g in games if g["time_class"] == "rapid"]
check("rapid rating", rapid[0][side(rapid[0])[0]]["rating"], home["rating"])
old = next((g for g in rapid if g["end_time"] < time.time() - 30 * 86400), None)
check("rapid rating change, 30 days", rapid[0][side(rapid[0])[0]]["rating"] - old[side(old)[0]]["rating"], home["rating_change"])
for tc in ("bullet", "blitz", "rapid", "daily"):
    mine = [g for g in games if g["time_class"] == tc]
    if mine:
        print(f"  latest {tc} rating: {mine[0][side(mine[0])[0]]['rating']} ({len(mine)} games)")

counts = collections.Counter(r["pattern"] for g in checked for r in rows[g["url"]] if r["pattern"] not in (None, "other"))
focus = counts.most_common(1)[0][0]
check("focus habit", focus, home["focus"]["pattern"])
check("focus times", counts[focus], home["focus"]["times"])
check("focus games", sum(1 for g in checked if any(r["pattern"] == focus for r in rows[g["url"]])), home["focus"]["games"])
last20 = checked[:20]
for p in home["patterns"]:
    n = counts[p["pattern"]]
    check(f"tile {p['pattern']} times", n, p["times"])
    check(f"tile {p['pattern']} per game", round(n / len(checked), 2), p["per_game"])
    check(f"tile {p['pattern']} last 20", round(sum(1 for g in last20 for r in rows[g["url"]] if r["pattern"] == p["pattern"]) / 20, 2), p["recent"])

lost = [sum(1 for r in rows[g["url"]] if r["pattern"] in LOSING) for g in checked]  # newest first
check("pieces a game, all", round(sum(lost) / len(lost), 2), home["pieces_per_game"])
check("pieces a game, last 20", round(sum(lost[:20]) / 20, 2), home["pieces_last20"])
w = home["trend_window"]
trend = [round(sum(lost[i:i + w]) / w, 2) for i in range(0, len(lost) - w + 1, w)][::-1]  # full windows, from the newest
check("graph, last point = last 10 games", trend[-1], home["trend"][-1])
check("graph points", len(trend), len(home["trend"]))
print("  graph (recount, oldest first):", trend)
print("  graph (app):                   ", home["trend"])

now = time.time()
for name, a, b in (("this", now - 7 * 86400, now), ("last", now - 14 * 86400, now - 7 * 86400)):
    gs = [g for g in checked if a <= g["end_time"] < b]
    check(f"week {name}: games", len(gs), home["week"][name]["games"])
    check(f"week {name}: pieces", sum(lost[checked.index(g)] for g in gs), home["week"][name]["pieces"])

# the Games page: each row
glist = {r["id"]: r for r in get("/api/games")}
check("games page rows", len(games), len(glist))
for g in checked:
    gid = g["url"].rstrip("/").split("/")[-1]
    r = glist.get(gid)
    if not r:
        bad.append(f"game {gid} missing from the Games page")
        continue
    check(f"game {gid} result", result(g), r["result"])
    check(f"game {gid} pieces", sum(1 for x in rows[g["url"]] if x["pattern"] in LOSING), r["pieces_lost"])
    check(f"game {gid} opponent rating", g[side(g)[1]]["rating"], r["opponent_rating"])

# Your level: each skill over the last 20 games
lad = get("/api/ladder")
check("level: games counted", min(20, len(checked)), lad["games"])
SKILL = {"hang": "left a piece hanging", "free": "missed a free capture", "mated": "walked into checkmate",
         "finish": "missed a checkmate", "fork": "walked into a fork or trick", "stalemate": "stalemated a won game"}
course = get("/api/course")

# Progress: badges (games in a row without the mistake), the clock
prog = get("/api/progress")
BADGE = {"safe": ("left a piece hanging",), "forkproof": ("walked into a fork or trick",), "matesafe": ("walked into checkmate",)}
for b in prog["badges"]:
    if b["id"] in BADGE:
        clean = [not any(r["pattern"] in BADGE[b["id"]] for r in rows[g["url"]]) for g in checked]  # newest first
        cur = next((i for i, c in enumerate(clean) if not c), len(clean))
        best, run = 0, 0
        for c in reversed(clean):
            run = run + 1 if c else 0
            best = max(best, run)
        check(f"badge {b['id']} current streak", cur, b["current"])
        check(f"badge {b['id']} best streak", best, b["best"])
    else:
        print(f"  badge {b['id']} ({b['what']}): current {b.get('current')}, best {b.get('best')} (not recounted)")
c = prog["clock"]
last30 = checked[:c["games"]]
check("clock: losses", sum(1 for g in last30 if result(g) == "loss"), c["losses"])
check("clock: lost on time", sum(1 for g in last30 if result(g) == "loss" and g[side(g)[0]]["result"] == "timeout"), c["on_time"])

# You vs you
vy = home.get("you_vs_you")
if vy:
    print("  you vs you:", vy)

# the labels themselves: does a "hanging" piece really get taken, is a "free capture" really free?
VAL = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}


def see(board, move):
    """Static exchange: what the side to move gains by this capture, both sides recapturing with their cheapest."""
    target = move.to_square
    gain = [VAL[board.piece_at(target).piece_type] if board.piece_at(target) else 0]
    b = board.copy(stack=False)
    piece = VAL[b.piece_at(move.from_square).piece_type]
    b.push(move)
    while True:
        attackers = [s for s in b.attackers(b.turn, target)]
        if not attackers:
            break
        s = min(attackers, key=lambda s: VAL[b.piece_at(s).piece_type])
        gain.append(piece - gain[-1])
        piece = VAL[b.piece_at(s).piece_type]
        try:
            b.push(chess.Move(s, target, promotion=chess.QUEEN if b.piece_at(s).piece_type == chess.PAWN and chess.square_rank(target) in (0, 7) else None))
        except Exception:
            break
    for i in range(len(gain) - 1, 0, -1):
        gain[i - 1] = -max(-gain[i - 1], gain[i])
    return gain[0]


import random  # noqa: E402
rng = random.Random(7)
hang = [r for g in checked for r in rows[g["url"]] if r["pattern"] == "left a piece hanging"]
free = [r for g in checked for r in rows[g["url"]] if r["pattern"] == "missed a free capture"]
hang_ok, hang_odd = 0, []
for r in rng.sample(hang, min(25, len(hang))):
    b = chess.Board(r["fen"]); b.push_san(r["move"])
    best = max((see(b, m) for m in b.legal_moves if b.is_capture(m) and not b.is_en_passant(m)), default=0)
    if best >= 2:
        hang_ok += 1
    else:
        hang_odd.append((r["url"].split("/")[-1], r["ply"], r["move"], r["reply_pv"][:2], best))
free_ok, free_odd = 0, []
for r in rng.sample(free, min(25, len(free))):
    b = chess.Board(r["fen"]); m = b.parse_san(r["best"])
    s = see(b, m)
    if s >= 2:
        free_ok += 1
    else:
        free_odd.append((r["url"].split("/")[-1], r["ply"], r["best"], s))
print(f"\nlabels: 'hanging' {hang_ok}/{min(25, len(hang))} really lose 2+ points to a capture at once; odd ones: {hang_odd}")
print(f"labels: 'free capture' {free_ok}/{min(25, len(free))} really win 2+ points; odd ones: {free_odd}")
print(f"\n{ok} numbers match, {len(bad)} don't:")
for b in bad:
    print("  -", b)

# Level and course: the teacher's reasons (why.explain), every mistake of 10 points or more, over the last 20 games
from coach import why  # noqa: E402
bad2, ok2 = [], 0
ideas = {}
for g in last20:
    for r in rows[g["url"]]:
        if r["loss"] >= 10:
            try:
                ideas.setdefault(g["url"], []).append(why.explain(r)["idea"])
            except (ValueError, KeyError, AssertionError):
                pass
rate = lambda ids: round(sum(1 for g in last20 for i in ideas.get(g["url"], []) if i in ids) / len(last20), 2)
for l in course["lessons"]:
    if l.get("rate") is not None and l.get("ideas"):
        mine = rate(l["ideas"])
        if abs(mine - l["rate"]) <= 0.011: ok2 += 1
        else: bad2.append(f"course {l['id']}: recount {mine}, app {l['rate']}")
print(f"\ncourse (teacher's reasons): {ok2} match, {len(bad2)} don't", bad2)
hang_home = round(sum(1 for g in last20 for r in rows[g['url']] if r['pattern'] == 'left a piece hanging') / 20, 2)
hang_level = next(s["value"] for lv in lad["levels"] for s in lv["skills"] if s["id"] == "hang")
print(f"one skill, two numbers: Home's hanging tile {hang_home} a game (last 20, big mistakes only) vs Level's 'Keep every piece safe' {hang_level}")
