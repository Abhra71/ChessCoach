"""The coach running quietly in the background.

- First start: a welcome page asks for the chess.com username, then shows progress while the games are checked.
- Every 10 minutes: download new games, check them, rebuild the review and practice pages.
- When a new game has been checked: a small Windows notification.
- A local web server on http://127.0.0.1:8765 (this computer only) that serves the pages, the guided set-up of the
  browser extension, and tells the extension the key moments of a finished game.

Run:  python -m coach.service   (the installed app, Knightwise.exe, runs this behind its tray icon)
"""
import io
import json
import logging
import os
import subprocess
import threading
import time
import urllib.error
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from logging.handlers import RotatingFileHandler
from pathlib import Path

import chess
import chess.pgn

from coach import analyze, drills, fetch, health, memory, puzzles, review, settings
from coach.paths import BUNDLED_EXTENSION, DATA, EXTENSION, FROZEN, LOGBOOK, NAME, PACKAGE, TEMPLATES, VERSION
from coach.patterns import classify
from coach.review import explain, move_number

PORT = int(os.environ.get("KNIGHTWISE_PORT", "8765"))  # another port only for a second copy while developing
URL = f"http://127.0.0.1:{PORT}"
EVERY = 300  # seconds between checks for new games: fresh, and gentle on chess.com (23 Oct)
MOMENTS = 3  # key moments shown per game
FEEDBACK_TO = "nanotech.mark.robots@gmail.com"  # where feedback goes (the user's choice, 19 Oct)
# notifications say "Knightwise": the Store app's own id, or the id the installer gives the Start menu shortcut
APP_ID = f"{PACKAGE}!Knightwise" if PACKAGE else "Abhra71.Knightwise"

log = logging.getLogger("coach")


def game_id(url):
    return url.rstrip("/").split("/")[-1]


class Moments:
    """Key moments per game, read from data/moves.jsonl (reloaded when the file changes)."""

    def __init__(self):
        self.mtime = None
        self.by_game = {}
        self.lock = threading.Lock()

    def get(self, gid):
        with self.lock:
            path = DATA / "moves.jsonl"
            mtime = path.stat().st_mtime if path.exists() else None
            if mtime != self.mtime:
                self.by_game = self.load(path) if mtime else {}
                self.mtime = mtime
            return self.by_game.get(gid)

    @staticmethod
    def load(path):
        games = {}
        for line in open(path):
            r = json.loads(line)
            games.setdefault(game_id(r["url"]), []).append(r)
        return games


GRADES = ((30, "Blunder"), (15, "Mistake"), (7, "Inaccuracy"))  # win chance lost by the move, in percent


def grade(loss):
    return next((name for least, name in GRADES if loss >= least), "Good")


def moment(r, played=None):
    """One key moment as the extension needs it: where, which arrows, what to say.
    played: every move of the real game, in order, as chess.Move, so the review never passes off the engine's
    best reply as the move the opponent actually made."""
    pattern = classify(r)
    board = chess.Board(r["fen"])
    mine, best = board.parse_san(r["move"]), board.parse_san(r["best"])
    after = board.copy()
    after.push(mine)
    best_reply = chess.Move.from_uci(r["reply_pv"][0]) if r["reply_pv"] else None
    real = played[r["ply"]] if played and len(played) > r["ply"] else None  # their real answer, if the game went on
    reason = _reason(r)
    why, lesson = reason["say"], reason.get("lesson")
    say = why
    if real and best_reply and real != best_reply:
        say += f" In the game they missed it and played {after.san(real)}."
    return {
        "steps": walk(r, mine, best, best_reply, real, after, why, reason.get("better")),
        "idea": reason["idea"], "lesson": lesson, "humans": _humans(r), "hard": _hard(r, board, best),
        "ply": r["ply"], "move_number": move_number(r), "color": r["color"],
        "placement": r["fen"].split()[0],  # the board just before the player's move
        "after_placement": _after(r["fen"], mine),
        "move": r["move"], "move_uci": mine.uci(), "grade": grade(r["loss"]),
        "best": r["best"], "best_uci": best.uci(),
        "reply_uci": best_reply.uci() if best_reply else None,  # the engine's best answer: "Their best reply"
        "reply_san": after.san(best_reply) if best_reply else None,
        "real_reply_uci": real.uci() if real else None,  # what they really played
        "real_reply_san": after.san(real) if real else None,
        "reply_missed": bool(real and best_reply and real != best_reply),
        "pattern": pattern if pattern not in (None, "other") else _idea_name(reason.get("idea")),
        "say": say,
        "loss": r["loss"],
    }


def _humans(r):
    """What players at your level, and stronger, play here (the human-move model, when it's switched on), or None."""
    from coach import maia
    if r["move"] == r["best"] or not maia.enabled():
        return None
    try:
        from coach import insights
        return maia.compare(r["fen"], r["move"], r["best"], insights.home().get("rating"))
    except Exception:  # never lose the review over it
        log.exception("maia")
        return None


def _hard(r, board, best):
    """How hard was the better move to find? How many players at your level play it (the human-move model), in
    words, or None. Kind on purpose: missing a move few players find is normal (1.0)."""
    from coach import maia
    if r["move"] == r["best"] or not maia.enabled():
        return None
    try:
        from coach import insights
        return maia.hard_words(maia.find_rate(board, best, insights.home().get("rating")))
    except Exception:  # never lose the review over it
        log.exception("maia")
        return None


def _idea_name(idea):
    from coach.why import IDEAS
    return IDEAS.get(idea) if idea and idea != "deeper" else "a big mistake"


def _reason(r):
    """Why this move was a mistake (coach/why.py, with the engine for reasons a few moves deep) and the course lesson
    that teaches it. Falls back to the older pattern sentence if anything goes wrong."""
    from coach import course, live_engine, why as why_
    try:
        with live_engine.LOCK:
            e = why_.explain(r, live_engine.get())
    except Exception:  # never lose the review over an explanation
        log.exception("why")
        pattern = classify(r)
        return {"idea": None, "say": explain(pattern, r) if pattern else f"Better was {r['best']}.", "better": None}
    l = course.lesson_for(e["idea"])
    return {**e, "lesson": {"id": l["id"], "title": l["title"]} if l else None}


def walk(r, mine, best, best_reply, real, after, why, better=None):
    """One key moment told one step at a time (debrief points 17, 18, 42): You played, Better, They replied, Their
    better. Each step says which board it's on ("before" or "after" your move) and its arrows."""
    g = grade(r["loss"])
    a = "an" if g[0] in "AEIOU" else "a"
    steps = [{"kind": "mine", "title": "You played", "san": r["move"], "board": "before",
              "text": f"You played {r['move']}, {a} {g.lower()}.", "arrows": [[mine.uci(), "mine"]]}]
    about_best = why.startswith(f"Better was {r['best']}") or why.startswith(r["best"] + " ")
    if about_best:  # the reason is what the better move does: say it at the Better step, not after their reply
        why, better = "", why[len(f"Better was {r['best']}"):].lstrip(":. ") if why.startswith("Better was") else why
    if best != mine:
        steps.append({"kind": "better", "title": "Better", "san": r["best"], "board": "before",
                      "text": f"Better was {r['best']}. " + (better if better and better.split()[0] == r["best"]  # "b4 forks…", not "B4"
                                                  else better[0].upper() + better[1:] if better else
                              f"It kept about {round(r['loss'])}% more of your chance to win."),
                      "arrows": [[best.uci(), "better"], [mine.uci(), "mine"]]})
    else:
        steps.append({"kind": "better", "title": "Better", "san": None, "board": "before",
                      "text": "That was already the best move here.", "arrows": [[mine.uci(), "mine"]]})
    if real and real == best_reply:
        steps.append({"kind": "real", "title": "They replied", "san": after.san(real), "board": "after",
                      "text": f"They replied {after.san(real)}, their best answer. {why}", "arrows": [[real.uci(), "real"]]})
    elif real:
        steps.append({"kind": "real", "title": "They replied", "san": after.san(real), "board": "after",
                      "text": f"They replied {after.san(real)}." + (" They missed something better." if best_reply else ""),
                      "arrows": [[real.uci(), "real"]]})
        if best_reply:
            steps.append({"kind": "reply", "title": "Their better", "san": after.san(best_reply), "board": "after",
                          "text": f"Their best was {after.san(best_reply)}. {why} You got away with it this time.",
                          "arrows": [[best_reply.uci(), "reply"], [real.uci(), "real"]]})
    elif best_reply:  # the game ended after your move (they resigned, or time ran out)
        steps.append({"kind": "reply", "title": "Their best reply", "san": after.san(best_reply), "board": "after",
                      "text": f"The game ended here. Their best reply would have been {after.san(best_reply)}. {why}",
                      "arrows": [[best_reply.uci(), "reply"]]})
    for st in steps:
        st["text"] = " ".join(st["text"].split())
    return steps


def played_moves(gid):
    """Every move of one archived game, in order (empty if the game isn't known)."""
    from coach import insights
    g = next((g for g in insights._games() if game_id(g["url"]) == str(gid)), None)
    if not g:
        return []
    game = chess.pgn.read_game(io.StringIO(g["pgn"]))
    return list(game.mainline_moves()) if game else []


def _after(fen, move):
    board = chess.Board(fen)
    board.push(move)
    return board.fen().split()[0]


def key_moments(rows, gid=None):
    """The few moves that cost the most in one game, in game order."""
    played = played_moves(gid) if gid else None
    return [moment(r, played) for r in review.biggest(rows, MOMENTS)]


MOMENT_CACHE = Moments()
UI = TEMPLATES / "ui"
SHOW = None  # set by the desktop app: show the window at a screen


def feedback_key():
    """The Web3Forms access key that emails feedback to FEEDBACK_TO (coach/feedback.key; packed in the build, never in
    the repo). Web3Forms keys are public by design: one can only send to the inbox it was made for."""
    try:
        return (Path(__file__).parent / "feedback.key").read_text(encoding="utf-8").strip()[:80] or None
    except OSError:
        return None


SENDS_A_DAY = 4  # one-click sends from one PC a day: the free form plan is ~250 a month for everyone, and no flooding


def feedback_send_allowed(today=None):
    """Counts this PC's one-click sends today (data/feedback-sent.json); True and counted when under the limit."""
    today = today or time.strftime("%Y-%m-%d")
    path = DATA / "feedback-sent.json"
    try:
        seen = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        seen = {}
    n = seen.get("n", 0) if seen.get("date") == today else 0
    if n >= SENDS_A_DAY:
        return False
    DATA.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"date": today, "n": n + 1}), encoding="utf-8")
    return True


def feedback_mail(text):
    """The ready email for feedback: to FEEDBACK_TO, with the subject and the player's words (kept short enough
    for every mail app's address limit)."""
    from urllib.parse import quote
    return f"mailto:{FEEDBACK_TO}?subject={quote(f'Knightwise feedback ({VERSION})')}&body={quote(text[:1800])}"


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"

    def allowed(self):
        """Who may talk to Knightwise: its own window, and the Knightwise extension. Other websites can't read
        anything (no cross-site header) or change anything (Origin check), and a site that points its own name
        at this computer is refused by the Host check."""
        host = (self.headers.get("Host") or "").lower()
        if host not in (f"127.0.0.1:{PORT}", f"localhost:{PORT}"):
            return False
        origin = self.headers.get("Origin")
        return origin in (None, URL) or origin.startswith("chrome-extension://")

    def do_GET(self):
        if not self.allowed():
            return self.send(403, "forbidden", "text/plain")
        path = self.path.split("?")[0].rstrip("/")
        if path.startswith("/api/game/"):
            rows = MOMENT_CACHE.get(path.rsplit("/", 1)[-1])
            # unknown game = not finished and checked yet: say nothing (fair play)
            body = {"known": rows is not None, "moments": key_moments(rows, path.rsplit("/", 1)[-1]) if rows else [],
                    "players": players_of(path.rsplit("/", 1)[-1]) if rows is not None else []}
            if rows:  # a finished, checked game only: the clock coach and the rematch
                from coach import insights, nudge
                nudge.seen(f"games/{path.rsplit('/', 1)[-1]}")  # reviewed on chess.com: not "new" any more
                body.update(insights.extras_for(path.rsplit("/", 1)[-1]))
                try:  # every move, so the coach follows chess.com's own arrows too (22 Oct test)
                    d = insights.game_detail(path.rsplit("/", 1)[-1])
                    body["moves"] = [{"placement": d["positions"][m["ply"]]["fen"].split()[0], "ply": m["ply"],
                                      "number": d["move_numbers"][m["ply"] - 1], "text": m["text"], "label": m["label"],
                                      "arrows": m["arrows"]} for m in d.get("narration") or []]
                except Exception:
                    log.exception("moves for the extension")
            return self.send(200, json.dumps(body), "application/json")
        if path == "/api/status":
            return self.send(200, json.dumps(status()), "application/json")
        if path == "/api/tags":  # chess.com's archive: a Knightwise tag per finished, checked game (?ids=1,2,3)
            from urllib.parse import parse_qs, urlsplit
            ids = [i for i in parse_qs(urlsplit(self.path).query).get("ids", [""])[0].split(",") if i.isdigit()][:100]
            tags = {i: t for i in ids if (t := game_tag(MOMENT_CACHE.get(i))) is not None}
            return self.send(200, json.dumps(tags), "application/json")
        if path == "/api/extension-stamp":  # changes whenever the extension's files change (it then reloads itself)
            return self.send(200, json.dumps({"stamp": extension_stamp()}), "application/json")
        if path == "/api/heard":  # what the coaches heard, as text on this PC (Settings)
            from coach import heard
            return self.send(200, json.dumps({"count": heard.count(), "recent": heard.recent()}), "application/json")
        if path == "/api/fixes":  # the fix file from GitHub: new chess.com names, paused features (flagship 6)
            from coach import fixes
            return self.send(200, json.dumps(fixes.current()), "application/json")
        if path == "/api/coach":  # what the coach of a chess.com section says (the extension shows it)
            return self.send(200, json.dumps(coach_says(self.path)), "application/json")
        if path == "/api/seen":  # a page the player opened in the app: nothing "new" about it any more (23 Oct)
            from coach import nudge
            from urllib.parse import parse_qs, urlsplit
            from urllib.parse import unquote
            nudge.seen(unquote(parse_qs(urlsplit(self.path).query).get("route", [""])[0]))
            return self.send(200, "{}", "application/json")
        if path == "/api/hello":  # the browser extension says it is installed and can reach the coach
            STATE["extension_seen"] = time.strftime("%Y-%m-%d %H:%M")
            from coach import nudge
            nudge.seen("extension")  # remembered: the tour never asks someone who has it to set it up (30 Oct)
            STATE.setdefault("extension_in", {})[browser_of(self.headers.get("User-Agent"))] = STATE["extension_seen"]
            STATE.setdefault("extension_at", {})[browser_of(self.headers.get("User-Agent"))] = time.time()  # finding 11
            return self.send(200, "{}", "application/json")
        if path == "/api/listen/warm":  # the player pressed Talk: load the listening model while they speak
            from coach import hearing
            if hearing.available():
                threading.Thread(target=hearing._whisper, daemon=True).start()
            return self.send(200, "{}", "application/json")
        if path == "/api/stats":  # the numbers, and today's answer per position so a page can pick up where you were
            return self.send(200, json.dumps({**memory.practice_stats(), "today": memory.today()}), "application/json")
        from coach import insights
        if path == "/api/home":
            return self.send(200, json.dumps({**insights.home(), "today_done": today_done()}), "application/json")
        if path == "/api/games":
            return self.send(200, json.dumps(insights.games_list()), "application/json")
        if path.startswith("/api/games/"):
            detail = insights.game_detail(path.rsplit("/", 1)[-1])
            if detail:
                from coach import nudge
                nudge.seen(f"games/{path.rsplit('/', 1)[-1]}")  # looked at: no "new game in" for it
            return self.send(200 if detail else 404, json.dumps(detail or {"message": "Game not found."}), "application/json")
        if path == "/api/warmup":  # chess.com home: three positions from today's practice, before you play
            from coach import drills
            return self.send(200, json.dumps(drills.warmup()), "application/json")
        if path == "/api/practice-set":
            from coach import brief
            today = time.strftime("%Y-%m-%d")
            if STATE.get("practice_day") not in (None, today):  # a new day: today's set now, not at the next check
                if UPDATE_LOCK.acquire(blocking=False):
                    try:
                        from coach import drills
                        drills.build()
                        STATE["practice_day"] = today
                    except Exception as e:
                        log.warning("practice at midnight: %s", e)
                    finally:
                        UPDATE_LOCK.release()
                else:  # a check is running: it builds today's set when it ends; the page asks again
                    WAKE.set()
            practice = DATA / "drills.json"
            stock = json.loads(practice.read_text()) if practice.exists() else []
            return self.send(200, json.dumps(brief.add(stock)), "application/json")
        if path == "/api/settings":
            return self.send(200, json.dumps(settings.public()), "application/json")
        if path == "/api/ai-usage":  # the usage panel: today's AI use per key, what's left, who is resting
            from coach import ai
            cfg, use = settings.load(), ai.usage()
            slots = [{"slot": s, "provider": cfg[s]["provider"], "name": settings.PROVIDERS[cfg[s]["provider"]]["name"],
                      **use[cfg[s]["provider"]]} for s in settings.SLOTS if settings.get_key(s)]
            return self.send(200, json.dumps({"slots": slots}), "application/json")
        if path in ("", "/app", "/welcome"):  # the desktop app (it shows the welcome screen itself when needed)
            return self.send(200, (UI / "index.html").read_bytes(), "text/html; charset=utf-8")
        if path == "/api/plan":  # "Your plan": one opening, tactic, idea, endgame, and the new thing if it's needed now
            from coach import live_engine, plan
            with live_engine.LOCK:
                out_home = insights.home()
                out = plan.plan(home=out_home, engine=live_engine.get())
            from coach import brief, daylock
            for kind, item in list((out.get("items") or {}).items()) + [("novelty", out.get("novelty"))]:
                if item and item.get("drills") and "state" not in item:  # a started one keeps its own positions  # the day's positions stay the same until midnight
                    item["drills"] = daylock.keep(f"plan:{kind}:{item.get('id') or item.get('title')}", item["drills"])
                    brief.add(item["drills"])
            import random
            from datetime import date
            done_cards = []  # finished topics as cards in the Done row, newest first, ready to play again (23 Oct test)
            for x in reversed(out.get("done_items") or []):
                again = plan.replay(x["id"], out_home, random.Random(date.today().isoformat() + x["id"])) if len(done_cards) < 12 else None
                if again and again.get("drills"):
                    again["drills"] = daylock.keep(f"replay:{x['id']}:{again.get('side', '')}", again["drills"])
                    brief.add(again["drills"])
                    done_cards.append({**again, "title": x["title"]})
            out["done_cards"] = done_cards
            return self.send(200, json.dumps(out), "application/json")
        if path == "/api/plan/replay":  # a done plan topic, to play again (the same positions all day)
            import random
            from datetime import date
            from urllib.parse import parse_qs, urlsplit
            from coach import brief, daylock, plan
            q = parse_qs(urlsplit(self.path).query)
            item_id, side = (q.get("id") or [""])[0], (q.get("side") or [None])[0]
            started = plan.in_progress().get(item_id)
            if started and (not side or started.get("side") in (None, side)):  # carry on with the same positions
                return self.send(200, json.dumps(started), "application/json")
            item = plan.replay(item_id, insights.home(), random.Random(date.today().isoformat() + item_id), side) if item_id else None
            if not item or not item.get("drills"):
                return self.send(404, json.dumps({"message": "Not found."}), "application/json")
            item["drills"] = daylock.keep(f"replay:{item_id}:{item.get('side', '')}", item["drills"])
            brief.add(item["drills"])
            return self.send(200, json.dumps(item), "application/json")
        if path == "/api/plan/library":  # Explore: everything in the Lichess library, or what matches the words typed
            from urllib.parse import parse_qs, urlsplit
            from coach import plan
            q = parse_qs(urlsplit(self.path).query)
            words, fam = (q.get("q") or [""])[0][:80], (q.get("family") or [""])[0][:80]
            out = {"results": plan.family_lines(fam)} if fam else {"results": plan.search(words)} if words.strip()                 else plan.library()
            return self.send(200, json.dumps(out), "application/json")
        if path.startswith("/api/film/"):  # your game as a short 3D film: its script (1.0)
            from coach import film
            gid = path.rsplit("/", 1)[-1]
            month = gid in ("month", "week")  # "week" was its first name
            pick = film.month_game() if month else gid
            out = film.script(pick, "Your game of the month") if month and pick else film.script(pick) if pick else None
            return self.send(200 if out else 404, json.dumps(out or {"message": "No game to film yet."}), "application/json")
        if path == "/api/report":  # your week or month in facts, for a coach or as Wrapped (1.0)
            from urllib.parse import parse_qs, urlsplit
            from coach import report
            days = 30 if (parse_qs(urlsplit(self.path).query).get("days") or ["7"])[0] == "30" else 7
            return self.send(200, json.dumps(report.report(days)), "application/json")
        if path.startswith("/api/bridge/"):  # the end of a game review: this game's mistake, linked to its training
            from coach import bridge
            return self.send(200, json.dumps(bridge.for_game(path.rsplit("/", 1)[-1]) or {}), "application/json")
        if path == "/api/blindfold":  # blindfold by voice: the next game to follow in your head (1.0)
            from coach import blindfold
            out = blindfold.item()
            return self.send(200 if out else 404, json.dumps(out or {"message": "Blindfold needs a few of your games first."}), "application/json")
        if path == "/api/guess":  # Guess the human move, the weekly challenge (1.0)
            from coach import guess
            return self.send(200, json.dumps(guess.challenge()), "application/json")
        if path == "/api/endgames":  # the endgame trainer: the endings, and how often you've solved each (0.7)
            from coach import endgames
            return self.send(200, json.dumps(endgames.listing()), "application/json")
        if path.startswith("/api/endgame/"):  # a fresh position for one ending, checked by the tablebase
            from coach import endgames
            start = endgames.start(path.rsplit("/", 1)[-1])
            return self.send(200 if start else 404, json.dumps(start or {"message": "No such ending."}), "application/json")
        if path == "/api/clockdrill":  # the clock coach's drill: your rushed mistakes, with the slow-down checklist
            from coach import brief, clock, drills, live_engine, plan
            rows = clock.rushed(insights._games(), insights._moves(), insights._player() or "")
            with live_engine.LOCK:
                items = [{**drills.drill(live_engine.get(), r["pattern"], r),
                          "where": f"From your game: you played this in {clock.say_time(r['seconds'])}"} for r in rows]
            idea = next(i for i in plan.IDEAS if i["id"] == "idea:slow-down")
            from coach import daylock
            items = daylock.keep("clockdrill", items)  # the same positions all day
            lesson = {**idea, "id": "idea:rushed", "kind": "idea", "coach": "viktor", "drills": brief.add(items),
                      "title": "Slow down when it matters",
                      "intro": "Each of these you played in a rush, and it cost you. This time, tick the checks first: the board waits for you."}
            return self.send(200, json.dumps(lesson), "application/json")
        if path.startswith("/api/prep/"):  # prep before a game: how a player plays, from their public games (0.8)
            from coach import prep
            user = path.rsplit("/", 1)[-1].lower()
            if not user or len(user) > 30 or not all(c.isalnum() or c in "-_" for c in user):
                return self.send(400, json.dumps({"message": "That doesn't look like a chess.com username."}), "application/json")
            try:
                out = prep.cached(user)
                if out:
                    prep.remember(user)  # for the Homework done badge
            except urllib.error.HTTPError as e:
                return self.send(404, json.dumps({"message": "No chess.com player with that name." if e.code == 404
                                                  else "chess.com didn't answer. Try again."}), "application/json")
            except OSError:
                return self.send(503, json.dumps({"message": "Couldn't reach chess.com. Are you online?"}), "application/json")
            return self.send(200 if out else 404, json.dumps(out or {"message": "They have no public games in the last 3 months."}), "application/json")
        if path == "/api/course":  # the course: every lesson, its status from your games, and the next one (0.10)
            from coach import course
            c = course.course()
            for row in c["lessons"]:
                row["reason"] = course.reason(row)
            return self.send(200, json.dumps(c), "application/json")
        if path.startswith("/api/course/"):  # one lesson: the text, your own positions and puzzles on the same idea
            from coach import brief, course, live_engine
            lid = path.rsplit("/", 1)[-1]
            if lid not in course.BY_ID or (course.BY_ID[lid]["coming"] and not course._structures(course.BY_ID[lid])):
                return self.send(404, json.dumps({"message": "No such lesson yet."}), "application/json")
            with live_engine.LOCK:
                item = course.lesson(lid, live_engine.get(), insights.home().get("rating"))
            from coach import daylock
            item["drills"] = daylock.keep_until_done(f"course:{lid}", item["drills"])  # the same positions until it's finished
            brief.add(item["drills"])
            return self.send(200, json.dumps(item), "application/json")
        if path.startswith("/api/spar/"):  # spar against a player: their openings, then human moves (0.11)
            from coach import spar
            from urllib.parse import parse_qs, urlsplit
            user = path.rsplit("/", 1)[-1].lower()
            side = parse_qs(urlsplit(self.path).query).get("color", ["white"])[0]
            if not user or len(user) > 30 or not all(c.isalnum() or c in "-_" for c in user) or side not in ("white", "black"):
                return self.send(400, json.dumps({"message": "That doesn't look like a chess.com username."}), "application/json")
            try:
                out = spar.start(user, side)
            except OSError:
                return self.send(503, json.dumps({"message": "Couldn't reach chess.com. Are you online?"}), "application/json")
            return self.send(200 if out else 404, json.dumps(out or {"message": "They have no public games to spar against."}), "application/json")
        if path == "/api/calc":  # the calculation trainer: see the whole line before anything moves (0.9)
            from coach import brief, drills
            from coach import memory
            items = drills.calculation(insights.home().get("rating"), time.strftime("%Y-%m-%d"), done_before=memory.seen_before())
            return self.send(200, json.dumps(brief.add(items)), "application/json")
        if path == "/api/repertoire" or path.startswith("/api/repertoire/"):  # your three opening lines (0.8)
            from coach import brief, live_engine, repertoire
            from urllib.parse import parse_qs, urlsplit
            fresh = parse_qs(urlsplit(self.path).query).get("fresh") == ["1"]
            with live_engine.LOCK:
                lines = repertoire.build(live_engine.get(), fresh=fresh)
            if path == "/api/repertoire":
                old = {x["name"]: x["why"] for x in repertoire.stale()}
                return self.send(200, json.dumps([{**{k: l[k] for k in ("id", "name", "side", "against", "style", "kept")},
                                                   "why": repertoire.why(l), "stale": old.get(l["name"]),
                                                   "moves": [s["san"] for s in l.get("steps", [])][:8]} for l in lines]), "application/json")
            i = path.rsplit("/", 1)[-1]
            if not i.isdigit() or int(i) >= len(lines):
                return self.send(404, json.dumps({"message": "No such line."}), "application/json")
            item = repertoire.lesson(lines[int(i)])
            brief.add(item["drills"])
            return self.send(200, json.dumps(item), "application/json")
        if path == "/api/ladder":  # your level: every skill from beginner to 2,000+, on your last 20 games (0.6)
            from coach import course, ladder
            out = ladder.page()
            try:  # a skill taught by a course lesson says whether that lesson is already learnt (23 Oct test)
                lessons = {l["id"]: l["status"] for l in course.course(current=course.LEVEL_ORDER[(out.get("current") or 0) + 1])["lessons"]}
                for lv in out.get("levels") or []:
                    for s in lv["skills"]:
                        route = (s.get("train") or {}).get("route", "")
                        if route.startswith("course/"):
                            s["lesson"] = lessons.get(route.split("/", 1)[1])
            except Exception as e:  # the level page never fails over this
                log.warning("ladder lessons: %s", e)
            return self.send(200, json.dumps(out), "application/json")
        if path.startswith("/api/lesson/"):  # a lesson on one Lichess theme at your level, for the ladder's skills
            from coach import brief, plan, puzzles
            import random as _random
            theme = path.rsplit("/", 1)[-1]
            if theme not in puzzles.KEEP_THEMES or theme not in plan.THEME_NAME:
                return self.send(404, json.dumps({"message": "No such lesson."}), "application/json")
            kind = plan.endgame if theme.endswith("Endgame") else plan.tactic
            item = kind(theme, insights.home().get("rating"), _random.Random(theme + time.strftime("%Y-%m-%d")))
            from coach import daylock
            item["drills"] = daylock.keep(f"lesson:{theme}", item["drills"])  # the same positions all day
            brief.add(item["drills"])
            return self.send(200, json.dumps(item), "application/json")
        if path.startswith("/api/rematch/"):  # Rematch your loss: where it starts (/api/rematch/<game>/<ply>)
            from coach import rematch
            parts = path.split("/")
            start = rematch.setup(parts[3], int(parts[4])) if len(parts) == 5 and parts[4].isdigit() else None
            return self.send(200 if start else 404, json.dumps(start or {"message": "No rematch for this game."}), "application/json")
        if path.startswith("/api/try/"):  # "Try it again": a key moment of a finished, checked game as a puzzle
            from coach import drills, live_engine
            parts = path.split("/")
            gid, ply = parts[-2], parts[-1]
            rows = MOMENT_CACHE.get(gid) or []
            r = next((r for r in rows if str(r.get("ply")) == ply), None)
            if r is None:  # only games the coach checked: never a game that is still running
                return self.send(404, json.dumps({"message": "That moment isn't here."}), "application/json")
            with live_engine.LOCK:
                d = drills.drill(live_engine.get(), classify(r), r)
            from coach import brief
            brief.add([d])
            return self.send(200, json.dumps(d), "application/json")
        if path == "/api/openings":  # your opening tree from your own games
            from coach import tree
            return self.send(200, json.dumps(tree.page()), "application/json")
        if path == "/api/progress":  # the story of your week and your badges
            from coach import progress
            return self.send(200, json.dumps(progress.page()), "application/json")
        if path == "/api/daily":  # today's challenge: your position, today's puzzle, your opening
            from coach import daily, live_engine
            home = insights.home()
            if not home.get("player"):
                return self.send(200, json.dumps({"drills": []}), "application/json")
            with live_engine.LOCK:
                out = daily.challenge(home, insights._games(), live_engine.get())
            from coach import brief
            brief.add(out["drills"])
            return self.send(200, json.dumps(out), "application/json")
        if path.startswith("/ext/"):  # the coaches' drawings, shared with the browser extension
            return self.static(path[len("/ext/"):], root=BUNDLED_EXTENSION)
        if path.startswith("/ui/"):
            return self.static(path[len("/ui/"):])
        if path == "/practice":
            return self.redirect("/#/practice")
        if path == "/setup-arrows":
            return self.redirect("/#/extension")
        pages = {"/review": "review.html", "/review.html": "review.html", "/drills.html": "drills.html"}
        if path in pages and (DATA / pages[path]).exists():
            return self.send(200, (DATA / pages[path]).read_bytes(), "text/html; charset=utf-8")
        self.send(404, "not found", "text/plain")

    def do_POST(self):
        """Answers from our own pages only: JSON from http://127.0.0.1:8765 (other sites can't send JSON here)."""
        if not self.allowed():
            return self.send(403, "forbidden", "text/plain")
        if self.path.startswith("/api/listen") and self.headers.get("Content-Type") == "application/octet-stream":
            return self.listen()
        if self.path.startswith("/api/film/save") and self.headers.get("Content-Type") in (("video/webm",) if FROZEN else ("video/webm", "video/mp4")):  # MP4 is the trailer tool's, never the shipped app's (cloud review)
            return self.save_film()
        if self.headers.get("Content-Type") != "application/json":
            return self.send(403, "forbidden", "text/plain")
        try:
            big = ("/api/save-picture", "/api/copy-picture")  # a picture of your week is bigger
            # a picture of your week, or a plan set with its positions (In progress), is bigger
            limit = 4_000_000 if self.path in big else 2_000_000 if self.path == "/api/plan/progress" else 10_000
            body = json.loads(self.rfile.read(min(int(self.headers.get("Content-Length", 0)), limit)))
        except ValueError:
            return self.send(400, "bad json", "text/plain")
        if not isinstance(body, dict):  # a list or a number: never an answer we expect (23 Oct security check)
            return self.send(400, "bad json", "text/plain")
        path = self.path.split("?")[0].rstrip("/")
        if path == "/api/health":  # the extension's self-check: what it found on a chess.com page
            ok = health.record(str(body.get("check", "")), bool(body.get("ok")), str(body.get("detail", "")))
            if ok and not body.get("ok"):
                log.warning("chess.com self-check failed: %s (%s)", body.get("check"), body.get("detail"))
            return self.send(200 if ok else 400, json.dumps({"ok": ok}), "application/json")
        if path == "/api/practice" and body.get("kind") in ("game", "puzzle", "opening"):
            memory.record_practice(str(body.get("id"))[:200], body["kind"], bool(body.get("right")),
                                   shown=bool(body.get("shown")))
            return self.send(200, json.dumps({**memory.practice_stats(), "today": memory.today()}), "application/json")
        if path == "/api/verdict" and body.get("answer") in ("yes", "some", "no"):
            memory.record_verdict(body["answer"])
            note_in_logbook(f"Your verdict on the review (\"is this me?\"): {body['answer']}")
            return self.send(200, "{}", "application/json")
        if path == "/api/blindfold/done":  # your blindfold answer: the next one longer or shorter
            from coach import blindfold
            return self.send(200, json.dumps(blindfold.done(body.get("right") is True, body.get("peeked") is True)), "application/json")
        if path == "/api/guess/done":  # a finished try at this week's challenge: the best so far
            from coach import guess
            try:
                total = max(0, min(guess.COUNT * 100, int(body.get("total", 0))))
            except (TypeError, ValueError):
                total = 0
            return self.send(200, json.dumps(guess.done(total)), "application/json")
        if path == "/api/endgame/move":  # your move in the endgame trainer, its check, and the best defence
            from coach import endgames
            try:
                out = endgames.play(str(body["id"]), str(body["fen"]), str(body["uci"])[:5], max(0, min(99, int(body.get("made", 0)))),
                                    int(body.get("limit") or 0))
            except (KeyError, ValueError):
                out = None
            return self.send(200 if out else 400, json.dumps(out or {"message": "That move isn't legal here."}), "application/json")
        if path == "/api/spar/move":  # your move when sparring, then theirs
            from coach import spar
            try:
                rating = max(100, min(3000, int(body.get("rating", 800))))
                side = "white" if body.get("color") == "white" else "black"
                out = spar.play(str(body["user"]).lower()[:30], str(body["fen"]), str(body["uci"])[:5], side, rating)
            except (KeyError, ValueError):
                out = None
            if out and out["over"]:
                out["say"] = {"win": "You won! Now you know their openings: play them the same way on chess.com.",
                              "loss": "They won this one. Try again: you'll meet the same first moves.",
                              }.get(out["result"], "A draw. Try again and look for the win.")
            return self.send(200 if out else 400, json.dumps(out or {"message": "That move isn't legal here."}), "application/json")
        if path == "/api/rematch/move":  # your move in a rematch, then the opponent's
            from coach import rematch
            try:
                rating = max(100, min(3000, int(body.get("rating", 800))))
                out = rematch.play(str(body["fen"]), str(body["uci"])[:5], rating, bool(body.get("white")))
            except (KeyError, ValueError):
                out = None
            if out and out["over"]:
                out["say"] = rematch.end_say(out["result"], str(body.get("real", "loss")))
            return self.send(200 if out else 400, json.dumps(out or {"message": "That move isn't legal here."}), "application/json")
        if path == "/api/scout":  # how to beat them: Prep's deeper look, started here, polled (24 Oct). A POST with JSON,
            # so no other website can start engine work with an <img> (cloud review, 24 Oct)
            from coach import scout
            user = str(body.get("user", "")).strip().lower()
            if not user or len(user) > 30 or not all(c.isalnum() or c in "-_" for c in user):
                return self.send(400, json.dumps({"message": "That doesn't look like a chess.com username."}), "application/json")
            out = scout.status(user)
            if out.get("state") == "done":  # the Homework done badge, drawn beside Punish
                try:
                    from coach import insights, prep
                    out["homework"] = prep.beaten(insights._games(), insights._player())
                except Exception:
                    out["homework"] = 0
            return self.send(200, json.dumps(out), "application/json")
        if path == "/api/start-over":  # Settings: "Wrong account? Start over", after a confirm in the page
            if self.headers.get("Origin") != URL:  # only the app's own window, never an extension (cloud review)
                return self.send(403, json.dumps({"message": "Only the Knightwise window can do this."}), "application/json")
            start_over()
            return self.send(200, "{}", "application/json")
        if path == "/api/player":
            ok, message = set_player(str(body.get("username", "")))
            return self.send(200 if ok else 400, json.dumps({"ok": ok, "message": message}), "application/json")
        if path == "/api/daily/done":
            from coach import daily
            return self.send(200, json.dumps(daily.done()), "application/json")
        if path == "/api/course/done":  # a lesson's practice finished: from now on your games judge it
            from coach import course
            lid = str(body.get("id", ""))
            if lid not in course.BY_ID:
                return self.send(404, json.dumps({"message": "No such lesson."}), "application/json")
            course.studied(lid, body.get("right", 0), body.get("total", 0))
            from coach import daylock
            daylock.release(f"course:{lid}")  # finished: the next go gets new positions
            return self.send(200, "{}", "application/json")
        if path == "/api/badges/shown":  # the badge pop-up was seen: never again, here or on chess.com
            from coach import progress
            progress.gold_shown(str(body.get("id", "")))
            return self.send(200, "{}", "application/json")
        if path == "/api/plan/progress":  # a plan set answered part-way: kept for In progress (23 Oct test)
            from coach import plan
            plan.progress(str(body.get("id", ""))[:200], body.get("item"), body.get("state"))
            return self.send(200, "{}", "application/json")
        if path == "/api/plan/mark":  # the player saw or finished a new thing
            from coach import plan
            plan.mark(str(body.get("id", ""))[:200], done=bool(body.get("done")), novelty=bool(body.get("novelty")))
            return self.send(200, "{}", "application/json")
        if path == "/api/chat":  # talking with a coach on chess.com (needs a key; never fails without one)
            from coach import ai, coaches
            turns = body.get("history") if isinstance(body.get("history"), list) else []
            history = [(str(t[0]), str(t[1])) for t in turns[-6:] if isinstance(t, list) and len(t) == 2]
            reply = coaches.chat(str(body.get("coach", "maya")), str(body.get("message", "")), history)
            if not reply["ai"] and ai.ready():
                reply["note"] = "The AI is busy right now, so I'm keeping it short. Ask again in a minute."
            return self.send(200, json.dumps(reply), "application/json")
        if path == "/api/feedback":  # a beta tester's report: kept on this PC (where it's sent is the builder's choice)
            entry = {k: str(body.get(k, ""))[:1500] for k in ("doing", "wrong", "page")}
            reply = str(body.get("reply", "")).strip()[:120]  # optional, so the maker can press Reply (22 Oct)
            reply = reply if "@" in reply and "." in reply.split("@")[-1] and " " not in reply else ""
            entry.update(helped=max(0, min(5, int(body.get("helped") or 0))), version=VERSION, at=time.strftime("%Y-%m-%d %H:%M"))
            DATA.mkdir(parents=True, exist_ok=True)
            with open(DATA / "feedback.jsonl", "a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry) + "\n")
            note_in_logbook(f"Feedback saved ({entry['page']}): {entry['wrong'][:80]}")
            text = (f"What I was doing: {entry['doing'] or '-'}\nWhat went wrong or was confusing: {entry['wrong'] or '-'}\n"
                    f"How much Knightwise helped today (1 to 5): {entry['helped'] or '-'}\n\n"
                    f"Knightwise {VERSION}, page: {entry['page'] or '-'}" + (f"\nReply to: {reply}" if reply else ""))
            key = feedback_key()  # one-click Send (22 Oct: "as easy as just a send button"): the page posts it
            if body.get("email") and key and not feedback_send_allowed():  # at most SENDS_A_DAY from one PC
                key = None
                return self.send(200, json.dumps({"saved": True, "text": text, "key": None, "limit": SENDS_A_DAY}), "application/json")
            if body.get("email") and not key:  # no form key in this build: the player's own email app, ready to send
                webbrowser.open(feedback_mail(text))
            return self.send(200, json.dumps({"saved": True, "text": text, "key": key, "version": VERSION, "reply": reply or None}), "application/json")
        if path == "/api/answer":  # no AI key: a tapped question, answered from the player's own numbers (24 Oct)
            from coach import answers
            where = body.get("where") if isinstance(body.get("where"), dict) else {}
            where = {k: str(v)[:40] for k, v in where.items() if k in ("section", "game", "ply")}
            extra = body.get("extra") if isinstance(body.get("extra"), dict) else {}
            extra = {k: str(v)[:400] for k, v in extra.items() if k in ("hint", "habit", "title", "teaches")}
            qid = str(body.get("id", ""))
            if qid == "":  # just the questions for this page
                return self.send(200, json.dumps({"questions": answers.questions(where.get("section") or "home")}), "application/json")
            return self.send(200, json.dumps(answers.answer(qid, where, extra)), "application/json")
        if path == "/api/talk":  # a spoken turn with a coach: the reply, and one checked thing to do (0.6)
            from coach import talk
            turns = body.get("history") if isinstance(body.get("history"), list) else []
            history = [(str(t[0]), str(t[1])) for t in turns[-6:] if isinstance(t, list) and len(t) == 2]
            where = body.get("where") if isinstance(body.get("where"), dict) else {}
            where = {k: str(v)[:400 if k == "on_screen" else 40] for k, v in where.items()
                     if k in ("section", "game", "step", "chesscom", "ply", "on_screen", "line", "side")}  # on_screen: what the page shows
            t0 = time.time()
            r = talk.reply(str(body.get("coach", "maya")), str(body.get("text", "")), history, where)
            if (r.get("action") or {}).get("web", "").startswith("https://www.chess.com/"):
                webbrowser.open(r["action"]["web"])  # chess.com's page, in their own browser
            # the debug logbook: one line a turn, words only, so a wrong answer can be traced (22 Oct hand test)
            log.info("talk %s at %s: %r -> %s, offer %s, ai=%s, %.1f s: %r", body.get("coach", "maya"), where.get("section"),
                     str(body.get("text", ""))[:120], r.get("action"), r.get("offer"), r.get("ai"), time.time() - t0,
                     r.get("text", "")[:120])
            return self.send(200, json.dumps(r), "application/json")
        if path == "/api/heard/forget":
            from coach import heard
            heard.forget()
            return self.send(200, "{}", "application/json")
        if path == "/api/check-now":
            WAKE.set()
            return self.send(200, "{}", "application/json")
        if path == "/api/open-extensions":
            opened = open_extensions_page(body.get("browser"))
            return self.send(200, json.dumps({"opened": opened}), "application/json")
        if path == "/api/settings":
            return self.send(200, json.dumps(settings.save(body)), "application/json")
        if path == "/api/say":  # one sentence -> WAV, spoken by the coach (Kokoro, on this computer)
            from coach import voice
            if not voice.available():
                return self.send(503, json.dumps({"message": "The voice isn't installed."}), "application/json")
            try:
                audio = voice.say(str(body.get("text", "")), settings.load()["voice_name"] if not body.get("voice")
                                  else str(body["voice"]), slow=body.get("slow") is True)
            except Exception as e:
                log.exception("voice failed")
                return self.send(500, json.dumps({"message": str(e)[:200]}), "application/json")
            return self.send(200, audio, "audio/wav")
        if path == "/api/keys":
            try:
                used = settings.set_key(str(body.get("slot")), str(body.get("provider")), str(body.get("key", "")))
            except ValueError as e:
                return self.send(400, json.dumps({"message": str(e)}), "application/json")
            from coach import ai  # tried at once, so a wrong or used-up key is known now, not in the middle of a question
            ok, message = ai.test_key(str(body.get("slot")))
            switched = used != str(body.get("provider"))
            note = (f"That's a {settings.PROVIDERS[used]['name']} key, so it's saved as one. " if switched else "") + message
            return self.send(200, json.dumps({**settings.public(), "ok": ok, "message": note}), "application/json")
        if path == "/api/keys/test":
            from coach import ai
            ok, message = ai.test_key(str(body.get("slot")))
            return self.send(200, json.dumps({"ok": ok, "message": message}), "application/json")
        if path in ("/api/explain", "/api/ask"):
            return self.coach_ai(path, body)
        if path == "/api/voice/install-listening":
            if not STATE.get("listen_install"):
                threading.Thread(target=install_listening, daemon=True).start()
            return self.send(200, "{}", "application/json")
        if path == "/api/keys/remove":
            try:
                settings.remove_key(str(body.get("slot")))
            except ValueError as e:
                return self.send(400, json.dumps({"message": str(e)}), "application/json")
            return self.send(200, json.dumps(settings.public()), "application/json")
        if path == "/api/show-extension-folder":  # Explorer with the extension folder selected, ready to drag
            if os.name == "nt":
                subprocess.Popen(["explorer", "/select,", str(EXTENSION)])
            return self.send(200, "{}", "application/json")
        if path == "/api/save-picture":  # the week card as a PNG in Pictures\Knightwise, shown in Explorer
            import base64
            from datetime import date
            data = str(body.get("png", ""))
            if not data.startswith("data:image/png;base64,"):
                return self.send(400, json.dumps({"message": "Not a picture."}), "application/json")
            from pathlib import Path
            folder = Path.home() / "Pictures" / "Knightwise"
            folder.mkdir(parents=True, exist_ok=True)
            target = folder / f"my-chess-week-{date.today().isoformat()}.png"
            target.write_bytes(base64.b64decode(data.split(",", 1)[1]))
            if os.name == "nt" and body.get("show", True):  # Save as picture shows it; sharing saves quietly
                subprocess.Popen(["explorer", "/select,", str(target)])
            return self.send(200, json.dumps({"path": str(target)}), "application/json")
        if path == "/api/copy-picture":  # Share: the week's picture on the Windows clipboard, to paste anywhere
            ok = copy_picture(str(body.get("png", "")))
            return self.send(200 if ok else 400, json.dumps({"ok": ok}), "application/json")
        if path == "/api/open-folder":
            if os.name == "nt":
                os.startfile(DATA.parent)
            return self.send(200, "{}", "application/json")
        if path == "/api/show":  # a second Knightwise.exe (or a notification) asks the running one to show a screen
            route = str(body.get("route", "home"))[:100]
            if SHOW and all(c.isascii() and (c.isalnum() or c in "/-_") for c in route):  # it goes into the window's JS
                SHOW(route)
            return self.send(200, "{}", "application/json")
        self.send(404, "not found", "text/plain")

    def save_film(self):
        """A recorded film (webm, at most 80 MB; the trailer is an MP4, larger) into Videos\\Knightwise, shown in Explorer (1.0)."""
        from urllib.parse import parse_qs, urlsplit
        from coach import film
        size = int(self.headers.get("Content-Length", 0))
        if not 0 < size <= (150_000_000 if self.headers.get("Content-Type") == "video/mp4" else 80_000_000):
            return self.send(400, json.dumps({"message": "Too big or empty."}), "application/json")
        gid = (parse_qs(urlsplit(self.path).query).get("game") or [""])[0]
        target = film.save(self.rfile.read(size), gid, "mp4" if self.headers.get("Content-Type") == "video/mp4" else "webm")
        if os.name == "nt":
            subprocess.Popen(["explorer", "/select,", str(target)])
        return self.send(200, json.dumps({"path": str(target)}), "application/json")

    def listen(self):
        """The player's voice: 16 kHz 16-bit mono samples from the app -> text. Through the player's own Groq or
        Gemini key first (fast and accurate, Jarvis's record); Whisper on this computer only if they installed it."""
        from coach import ai, hearing
        size = int(self.headers.get("Content-Length", 0))
        if not 0 < size <= 60 * hearing.RATE * 2:  # at most a minute of speech
            return self.send(400, json.dumps({"message": "Too long or empty."}), "application/json")
        pcm = self.rfile.read(size)
        if size < hearing.RATE // 2:  # under a quarter of a second: nothing said
            return self.send(200, json.dumps({"text": ""}), "application/json")
        import numpy as np
        if np.abs(np.frombuffer(pcm[:size // 2 * 2], dtype="<i2")).max(initial=0) < 200:  # silence: a dead microphone
            # (19 Oct: Bluetooth headphones switched off, the recording was all zeros, and Whisper wrote
            # "Thanks for watching!" for it). Never sent: the coach would answer words nobody said.
            return self.send(200, json.dumps({"text": "", "silent": True}), "application/json")
        try:
            text, provider = ai.hear(pcm, hearing.RATE)
            from coach import heard
            heard.note(text, provider)  # text only, on this PC: the hearing learns the player's words (flagship 6)
            return self.send(200, json.dumps({"text": text, "by": provider}), "application/json")
        except ai.NoKey as e:
            problem = str(e)
        except Exception as e:  # both keys busy or down
            log.warning("cloud hearing failed: %s", e)
            problem = "I couldn't hear you just now: the AI is busy. Try again in a minute."
        if not hearing.available():
            return self.send(503, json.dumps({"message": problem}), "application/json")
        import numpy as np
        try:
            text = hearing.transcribe(np.frombuffer(pcm, dtype="<i2").astype(np.float32) / 32768)
        except Exception as e:
            log.exception("listening failed")
            return self.send(500, json.dumps({"message": str(e)[:200]}), "application/json")
        return self.send(200, json.dumps({"text": text, "by": "this PC"}), "application/json")

    def coach_ai(self, path, body):
        """AI explanation of a key moment, or an answer to the player's question (needs a key in Settings)."""
        from coach import ai, insights, live_engine
        from coach.facts import moment_facts, position_facts
        rating = insights.home().get("rating")
        rows = MOMENT_CACHE.get(str(body.get("game", ""))) or []
        r = next((x for x in rows if x["ply"] == body.get("ply")), None)
        try:
            if path == "/api/explain":
                if not r:
                    return self.send(404, json.dumps({"message": "Unknown moment."}), "application/json")
                answer = ai.explain(moment_facts(r, classify(r)), rating)
            else:
                fen = str(body.get("fen", ""))
                if fen:
                    chess.Board(fen)  # refuse anything that isn't a position
                    with live_engine.LOCK:
                        context = {"position": position_facts(fen, live_engine.get())}
                else:  # a general question: answer from the player's own record
                    h = insights.home()
                    context = {"player_record": {k: h.get(k) for k in ("games", "results", "rating", "focus", "patterns",
                                                                      "pieces_per_game", "pieces_last20", "trend")}}
                if r:
                    context["key_moment"] = moment_facts(r, classify(r))
                lesson = body.get("lesson")
                if isinstance(lesson, dict):  # asked on a learning page: what it teaches (23 Oct test)
                    context["lesson"] = {k: str(v)[:400] for k, v in lesson.items()
                                         if k in ("title", "teaches", "opening", "line_so_far", "why_last_move", "next_move_idea") and v}
                solving = bool(body.get("solving"))
                if solving and "position" in context:  # still solving: the answer is held back, so it can't be given away
                    p = context["position"]
                    context["position"] = {k: v for k, v in p.items() if k != "engine_top_moves"}
                    context["still_solving"] = True
                answer = ai.ask(str(body.get("question", "")), context, rating, solving)
        except ai.NoKey as e:
            return self.send(400, json.dumps({"message": str(e), "no_key": True}), "application/json")
        except ValueError:
            return self.send(400, json.dumps({"message": "That isn't a chess position."}), "application/json")
        except Exception as e:
            log.warning("AI failed: %s", e)
            # the plain line, never "gemini: HTTP 400; groq: HTTP 401" (27 Oct, the owner's first 1.0 run)
            from coach import talk
            return self.send(502, json.dumps({"message": talk.why_not(e)}), "application/json")
        return self.send(200, json.dumps(answer), "application/json")

    def static_file(self, name, root=None):
        """The file a /ui/ address names, or None: inside the app's folder only. ".." is undone first, so nothing
        outside can be reached by the address; a folder the developer linked in (coach/ui/vendor in a second copy
        of the code, 20 Oct) is still served."""
        root = Path(os.path.abspath(root or UI))
        target = Path(os.path.abspath(root / name))
        return target if root in target.parents and target.is_file() else None

    def do_HEAD(self):
        """Is this file there? (the film asks before playing its music)"""
        path = self.path.split("?")[0]
        ok = path.startswith("/ui/") and self.static_file(path[len("/ui/"):]) is not None
        self.send_response(200 if ok else 404)
        self.end_headers()

    def static(self, name, root=None):
        """Files of the desktop app (coach/ui), or the extension's drawings; nothing outside them."""
        target = self.static_file(name, root)
        if target is None:
            return self.send(404, "not found", "text/plain")
        types = {".js": "text/javascript", ".css": "text/css", ".png": "image/png", ".jpg": "image/jpeg",
                 ".svg": "image/svg+xml", ".glb": "model/gltf-binary", ".gltf": "model/gltf+json",
                 ".bin": "application/octet-stream", ".wav": "audio/wav", ".flac": "audio/flac", ".ogg": "audio/ogg", ".mp3": "audio/mpeg",
                 ".json": "application/json", ".html": "text/html; charset=utf-8"}
        ctype = types.get(target.suffix, "application/octet-stream")
        data = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(data)

    def redirect(self, where):
        self.send_response(302)
        self.send_header("Location", where)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def send(self, code, body, ctype):
        data = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


STATE = {"phase": "starting"}
WAKE = threading.Event()  # set it to check for new games right now
UPDATE_LOCK = threading.Lock()  # the background check and Start over take turns
GENERATION = [0]  # bumped by Start over: a check that started before it must not leave the old player's games


class Server(ThreadingHTTPServer):
    """Only one copy may run: no sharing the port (on Windows the default lets a second copy bind it too)."""
    allow_reuse_address = False
    request_queue_size = 64  # a burst of requests waits its turn instead of being turned away (23 Oct security check)

    def server_bind(self):
        import socket
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


def extension_stamp():
    """A fingerprint of the extension folder Chrome loads (names, sizes, times)."""
    import hashlib
    h = hashlib.sha1(usedforsecurity=False)  # a fingerprint of files, not security
    for f in sorted(p for p in EXTENSION.rglob("*") if p.is_file()):
        st = f.stat()
        h.update(f"{f.relative_to(EXTENSION)}|{st.st_size}|{int(st.st_mtime)}".encode())
    return h.hexdigest()[:12]


TAG_SAY = {  # pattern -> (one, many): the archive tag's words
    "left a piece hanging": ("1 piece left hanging", "{n} pieces left hanging"),
    "walked into a fork or trick": ("walked into a fork", "walked into {n} forks"),
    "missed a free capture": ("missed a free piece", "missed {n} free pieces"),
    "walked into checkmate": ("walked into checkmate", "walked into checkmate"),
    "missed a checkmate": ("missed a checkmate", "missed {n} checkmates"),
    "stalemated a won game": ("stalemated a won game", "stalemated a won game"),
}


def game_tag(rows):
    """The Knightwise tag for one checked game in chess.com's archive: true and short. None if not checked."""
    if rows is None:
        return None
    counts = {}
    for r in review.biggest(rows, MOMENTS):  # exactly the review's key moments, read the same way
        p = classify(r)
        if p in TAG_SAY:
            counts[p] = counts.get(p, 0) + 1
    if not counts and max((r["ply"] for r in rows), default=0) < 18:  # left after 2 moves: not "a clean game" (19 Oct)
        return {"text": "too short to judge", "tone": "plain"}
    if not counts:
        return {"text": "clean game", "tone": "good"}
    order = sorted(counts, key=lambda p: (p != "stalemated a won game", -counts[p]))[:2]
    words = [TAG_SAY[p][0] if counts[p] == 1 else TAG_SAY[p][1].format(n=counts[p]) for p in order]
    return {"text": " · ".join(words), "tone": "bad"}


def copy_picture(data):
    """Put a PNG (a data: URL) on the Windows clipboard. The page can't: browsers keep pictures off the clipboard
    unless the page has a permission the app window doesn't give. Windows' own clipboard, through PowerShell."""
    import base64
    import tempfile
    if os.name != "nt" or not data.startswith("data:image/png;base64,"):
        return False
    path = os.path.join(tempfile.gettempdir(), "knightwise-share.png")
    with open(path, "wb") as fh:
        fh.write(base64.b64decode(data.split(",", 1)[1]))
    script = ("Add-Type -AssemblyName System.Windows.Forms,System.Drawing; "
              f"$i=[System.Drawing.Image]::FromFile('{path}'); [System.Windows.Forms.Clipboard]::SetImage($i); $i.Dispose()")
    done = subprocess.run(["powershell", "-NoProfile", "-STA", "-Command", script], capture_output=True, timeout=20,
                          creationflags=0x08000000)  # CREATE_NO_WINDOW: no console flashing up
    return done.returncode == 0


def browser_of(agent):
    """Which browser a request came from, by its User-Agent: so Settings can say "Connected in Chrome"."""
    agent = agent or ""
    for name, mark in (("edge", "Edg/"), ("opera", "OPR/"), ("brave", "Brave"), ("chrome", "Chrome/")):
        if mark in agent:
            return name
    return "other"


def players_of(gid):
    """Both usernames of a game. chess.com's archive can give a bot game the address of someone else's daily game,
    so the extension only shows a review when the page shows these two names."""
    from coach import insights
    g = next((g for g in insights._games() if game_id(g["url"]) == str(gid)), None)
    return [g["white"]["username"], g["black"]["username"]] if g else []


def coach_says(url):
    """?section=home|puzzles|review|progress|lessons|play&hour=0-23[&game=id]. A review of a game the coach doesn't
    know (not finished and checked) gets no board facts at all (fair play)."""
    from urllib.parse import parse_qs, urlsplit

    from coach import coaches
    q = {k: v[0] for k, v in parse_qs(urlsplit(url).query).items()}
    hour = int(q["hour"]) if q.get("hour", "").isdigit() else time.localtime().tm_hour
    moments = None
    if q.get("game", "").isdigit():
        rows = MOMENT_CACHE.get(q["game"])
        moments = None if rows is None else len(key_moments(rows)) if rows else 0
    extra = {}
    if q.get("section") == "member":  # a player's chess.com profile: prep against them (0.8)
        who = q.get("who", "").lower()
        extra["who"] = who if who and len(who) <= 30 and all(c.isalnum() or c in "-_" for c in who) else None
    if q.get("section") in ("home", "plan"):
        from coach import insights, live_engine, plan
        try:
            with live_engine.LOCK:
                extra["novelty"] = plan.novelty(engine=live_engine.get())
            extra["advice"] = coaches.advice(insights._games(), insights._moves(), player() or "")
        except Exception:
            log.exception("novelty")
    said = coaches.speak(q.get("section", "home"), hour=hour % 24, moments=moments, extra=extra,
                         again=q.get("again") == "1", in_app=q.get("in") == "app")
    from coach import voice
    s = settings.load()
    said["voice_on"] = bool(s.get("voice")) and voice.available()
    said["role"] = coaches.COACHES[said["coach"]]["role"]
    said["ai_ready"] = any(settings.get_key(slot) for slot in settings.SLOTS)
    said["talk_ready"] = settings.public()["talk_ready"]  # Talk by voice on chess.com (0.6)
    if not said["ai_ready"]:  # tell everyone the conversation feature exists
        said["ai_hint"] = coaches.AI_HINT
    try:  # her one new thing for this page: she comes up by herself and points at it (23 Oct test)
        said = with_point(said, q)
    except Exception:
        log.exception("the coach's pick")
    # a badge just completed: shown once, only where it's calm (an overview page in the app; on chess.com only its
    # home, puzzles, lessons and stats, never a game page)
    calm = q.get("tab", "home") in HUBS if q.get("in") == "app" else q.get("section") in ("home", "puzzles", "lessons", "progress")
    if calm:
        try:
            from coach import progress
            said["badge"] = progress.new_gold(ready=STATE.get("phase") == "ready")
        except Exception:
            log.exception("badge pop-up")
    return said


HUBS = ("home", "games", "train", "progress", "plan", "course", "level")  # app pages where the coach may suggest


def with_point(said, q):
    from coach import coaches, insights, nudge, talk
    in_app, section = q.get("in") == "app", q.get("section", "home")
    if q.get("tab"):
        nudge.seen(q["tab"])
    if not said.get("lines") and not said.get("quiet"):
        return said  # a page where the coach says nothing at all (someone's profile)
    # in the app, only on a page that gives an overview, never where you're working (practice, a lesson, a drill), and
    # not right after she opened that page for you (23 Oct test: "the coach says something, opens something else")
    if in_app and (q.get("nopoint") == "1" or q.get("tab", "home") not in HUBS):
        return said
    home = insights.home()
    g = home.get("last_game") or {}
    rematch = insights.extras_for(g["id"]).get("rematch") if in_app and g.get("checked") and g.get("result") != "win" else None
    rematch = rematch if rematch is not None else (insights.extras_for(g["id"]).get("rematch")
                                                   if g.get("checked") and g.get("result") != "win" else None)
    try:
        from coach import progress
        prog = progress.page()
    except Exception:
        prog = None
    p = nudge.pick("app" if in_app else "chesscom", section, home=home, lesson=talk.next_lesson(), rematch=rematch,
                   prog=prog, games=insights._games(), player=(insights._player() or "").lower(),
                   coach=said.get("coach"), extension=bool(STATE.get("extension_in")))
    if not p:
        return said
    lines = said.get("lines") or []
    # a greeting always comes first, then the suggestion (30 Oct test: "its suggestion should not come before greeting");
    # on a second visit that's the short "Welcome back." line
    keep = lines[:1] if lines else [coaches.line("again", said.get("coach") or "maya")]
    acts = said.get("actions") or []
    if p.get("action"):  # it lives in the other place: one button to it, first
        acts = [p["action"]] + [a for a in acts if a.get("app") != p["action"].get("app") or not a.get("app")]
    elif in_app and p.get("route"):  # in the app: the suggestion's own button, alone, so it's clear what it opens
        label = {"rematch": "Play it again", "game": "Open the game", "daily": "Start", "badge": "See your badges",
                 "clock": "Slow-down drill", "tour": "Show me", "lesson": "Open the lesson", "endgame": "Play it",
                 "opening": "Opening tree", "calc": "In your head"}.get(p.get("kind"), "Open it")
        acts = [{"label": label, "app": p["route"].split("@")[0], "best": True}]
    return {**said, "point": p, "quiet": False, "lines": keep + [p["line"]], "actions": acts}


def player():
    path = DATA / "player.txt"
    return path.read_text().strip() if path.exists() else None


PRACTISED = 5  # positions answered on the Practice page today that count as "practised today"


def today_done():
    """Home's three cards, done or not today (23 Oct test: the green button moves to the first one not done):
    Today's 5 minutes; the latest game opened for review; at least PRACTISED positions practised outside the 5 minutes."""
    from datetime import date
    from coach import daily, insights, memory, nudge
    try:
        h = insights.home()
        last = (h.get("last_game") or {}).get("id")
        kept = (daily._memory().get("set") or {})
        mine = {d.get("id") for d in kept.get("drills", [])} if kept.get("day") == date.today().isoformat() else set()
        return {"daily": bool((h.get("daily") or {}).get("done_today")),
                "review": bool(last) and f"games/{last}" in set(nudge._load().get("seen", [])),
                "practice": sum(1 for i in memory.today() if i not in mine) >= PRACTISED}
    except Exception as e:  # never break Home over this
        log.warning("today_done: %s", e)
        return {}


def status():
    return {"version": VERSION, "player": player(), "last_update": STATE.get("last_update"), "phase": STATE.get("phase"),
            "done": STATE.get("done", 0), "total": STATE.get("total", 0), "error": STATE.get("error"),
            "older": STATE.get("older"),  # the older games being checked while the app is ready (27 Oct)
            "data_version": STATE.get("data_version", 0),
            "review_ready": (DATA / "review.html").exists(), "extension_seen": STATE.get("extension_seen"),
            "extension_in": STATE.get("extension_in", {}), "health": health.summary(),
            # connected only if seen lately: it checks in every minute (22 Oct test: "connected" after it was removed)
            "extension_now": [b for b, t in STATE.get("extension_at", {}).items() if time.time() - t < 180],
            "extension_path": str(EXTENSION), "browsers": sorted(browsers()), "listen_install": STATE.get("listen_install"),
            "practice_day": STATE.get("practice_day"), "no_games": bool(STATE.get("no_games"))}


# what isn't the player's: kept by Start over (the app's own settings and downloads, the AI use count, feedback sent)
APP_FILES = {"settings.json", "ai-usage.json", "puzzles.json", "opening-evals.json", "health.json", "service.pid",
             "feedback-sent.json", "feedback.jsonl", "voice-cache"}


def clear_player_files(keep_player=False):
    import shutil
    for f in DATA.iterdir() if DATA.exists() else []:
        if f.name in APP_FILES or (keep_player and f.name == "player.txt"):
            continue
        try:
            shutil.rmtree(f, ignore_errors=True) if f.is_dir() else f.unlink(missing_ok=True)
        except OSError:  # still open by a check that's finishing: it's cleared again when that check ends
            log.warning("start over: %s busy", f.name)


def start_over():
    """Wrong account (24 Oct, owner): everything Knightwise knows about this player goes, nothing is mixed into the
    next one. The AI keys and the app's settings stay. A background check running now is told, and its files are
    cleared again when it ends (cloud review)."""
    GENERATION[0] += 1
    clear_player_files()
    try:  # what's kept in memory about the old player
        from coach import prep, progress
        progress._LAST.update(at=0.0, badges=None)
        prep._CACHE.clear()
    except Exception:
        pass
    log.info("start over: the player's data cleared")


def set_player(username):
    """Check the name exists on chess.com, save it, and start checking that player's games."""
    username = username.strip().lower()
    if not username or len(username) > 30 or not all(c.isalnum() or c in "-_" for c in username):
        return False, "That doesn't look like a chess.com username."
    try:
        fetch.get_json(f"https://api.chess.com/pub/player/{username}")
    except urllib.error.HTTPError as e:
        return False, "No chess.com player with that name." if e.code == 404 else "chess.com didn't answer. Try again."
    except OSError:
        return False, "Couldn't reach chess.com. Are you online?"
    if player() and player() != username:  # a different player: start fresh, keep nothing of the old one
        for name in ("moves.jsonl", "checked.txt", "review.html", "drills.html"):
            (DATA / name).unlink(missing_ok=True)
        for f in DATA.glob("games-*.json"):
            f.unlink()
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "player.txt").write_text(username)
    WAKE.set()
    return True, "Saved."


def browsers():
    """Installed browsers whose extensions page we can open: name -> exe."""
    found = {}
    if os.name != "nt":
        return found
    import winreg
    for name, exe in (("chrome", "chrome.exe"), ("edge", "msedge.exe")):
        for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            try:
                with winreg.OpenKey(root, rf"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{exe}") as key:
                    found[name] = winreg.QueryValue(key, None)
                break
            except OSError:
                continue
    return found


def open_extensions_page(which):
    """Open chrome://extensions or edge://extensions (a web page can't link there, a program can)."""
    exe = browsers().get(which)
    if not exe:
        return False
    subprocess.Popen([exe, "chrome://extensions" if which == "chrome" else "edge://extensions"])
    return True


def note_in_logbook(line):
    """One line in the player's chess logbook (logbook/chess.md)."""
    book = LOGBOOK / "chess.md"
    book.parent.mkdir(parents=True, exist_ok=True)
    with open(book, "a", encoding="utf-8") as fh:
        fh.write(f"- {time.strftime('%d %b %Y')}: {line}\n")


def notify(title, text, url):
    """Windows toast notification (built into Windows, nothing to install). Clicking it opens `url`."""
    xml = (f'<toast activationType="protocol" launch="{url}"><visual><binding template="ToastGeneric">'
           f'<text>{title}</text><text>{text}</text></binding></visual></toast>')
    app = APP_ID if FROZEN else r"{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe"
    ps = (
        "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType=WindowsRuntime]|Out-Null;"
        "[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType=WindowsRuntime]|Out-Null;"
        "$x=New-Object Windows.Data.Xml.Dom.XmlDocument;$x.LoadXml($env:COACH_TOAST);"
        "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($env:COACH_APP)"
        ".Show([Windows.UI.Notifications.ToastNotification]::new($x))"
    )
    result = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
                            env={**os.environ, "COACH_TOAST": xml, "COACH_APP": app}, capture_output=True,
                            text=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), timeout=30)
    if result.returncode:
        log.warning("notification failed: %s", result.stderr[:300])


def update_once():
    """New games -> check -> pages. Returns (games checked, whether this was the first time)."""
    first = not (DATA / "review.html").exists()
    STATE.update(phase="downloading your games", done=0, total=0, error=None)
    from coach import fixes
    fixes.refresh()  # once a day: the fix file from GitHub (never fails; offline keeps the last copy)
    fetch.fetch(player())
    if not puzzles.current() and not puzzles.from_pack():  # first run (the packed set), or the library grew
        STATE["phase"] = "downloading puzzles"
        puzzles.main()
    STATE["phase"] = "checking your games"
    # many games waiting (a first start, or a long break): the newest first, then Home opens and the older ones are
    # checked in the background (27 Oct: a new PC waited 25 minutes for 148 games before it showed anything)
    many = len(analyze.unchecked()) > analyze.FIRST_LOOK
    checked = analyze.main(argv=[], progress=lambda done, total: STATE.update(done=done, total=total),
                           limit=analyze.FIRST_LOOK if many else None)
    if not (DATA / "moves.jsonl").exists():  # a brand-new chess.com account: no games yet (26 Oct test: it looped on
        # "Something went wrong" forever). Ready, with nothing to check; the first game is picked up by the next check.
        STATE.update(phase="ready", no_games=True, last_update=time.strftime("%Y-%m-%d %H:%M"))
        return 0, False
    STATE["no_games"] = False
    today = time.strftime("%Y-%m-%d")
    STATE["phase"] = "building your pages"
    if checked or first:
        review.build()
    if checked or first or STATE.get("practice_day") != today:  # new practice every day: puzzles, due positions
        drills.build()
        STATE["practice_day"] = today
    STATE.update(phase="ready", last_update=time.strftime("%Y-%m-%d %H:%M"))
    if checked:  # new numbers: open pages redraw themselves (only then, not after every check)
        STATE["data_version"] = STATE.get("data_version", 0) + 1
    if many:  # the older games, while the player already uses the app; then the pages again, with all of them
        STATE["older"] = {"done": 0, "total": len(analyze.unchecked())}
        try:
            more = analyze.main(argv=[], progress=lambda done, total: STATE.update(older={"done": done, "total": total}))
        finally:
            STATE.pop("older", None)
        if more:
            checked += more
            review.build()
            drills.build()
            STATE["data_version"] = STATE.get("data_version", 0) + 1
    if checked or first:
        warm_up()
    return checked, first


def warm_up():
    """After new games: the slow-down drill and your next lesson worked out now, with an engine of its own, so they
    open at once instead of after 10 seconds of Stockfish (19 Oct). Never in the way: errors are only logged."""
    from coach import clock, course, insights
    try:
        eng = analyze.open_engine()
    except Exception:
        log.exception("warm-up: no engine")
        return
    try:
        for r in clock.rushed(insights._games(), insights._moves(), insights._player() or ""):
            drills.drill(eng, r["pattern"], r)
        nxt = course.course().get("next")
        if nxt:
            course.lesson(nxt, eng, insights.home().get("rating"))
    except Exception:
        log.exception("warm-up failed")
    finally:
        eng.quit()


def summary_of_new(n):
    """One line about the newest games for the notification, and the newest game's id."""
    rows = [json.loads(line) for line in open(DATA / "moves.jsonl")]
    end = {g["url"]: g["end_time"] for f in DATA.glob("games-*.json") for g in json.loads(f.read_text())["games"]}
    newest = sorted({r["url"] for r in rows}, key=lambda u: end.get(u, 0))[-n:]
    lost = sum(1 for r in rows if r["url"] in newest and classify(r) in review.LOSING_MATERIAL)
    games = "1 new game" if n == 1 else f"{n} new games"
    return f"{games} checked. Pieces given away: {lost}. Click to see your key moments.", game_id(newest[-1])


def open_link(route):
    """What a notification opens: the app window (installed app) or the page in the browser (from source)."""
    return f"chesscoach://{route}" if FROZEN else f"{URL}/#/{route}"


def loop():
    while True:
        if not player():
            STATE["phase"] = "waiting for your chess.com username"
            WAKE.wait()
            WAKE.clear()
            continue
        try:
            gen = GENERATION[0]
            with UPDATE_LOCK:
                n, first = update_once()
            if gen != GENERATION[0]:  # Start over happened while it ran: what it wrote was the old player's
                clear_player_files(keep_player=True)
                WAKE.set()
                continue
            if first:
                notify(NAME, f"Your review is ready: {n} game{'s' if n != 1 else ''} checked. Click to open it.", open_link("home"))
            elif n:
                log.info("checked %d new games", n)
                text, newest = summary_of_new(n)
                notify(NAME, text, open_link(f"games/{newest}"))
        except Exception as e:
            log.exception("update failed")
            # no internet (chess.com unreachable) is said plainly, not as an error code (26 Oct offline test)
            # and only while downloading: while checking, a helper process's broken pipe is a ConnectionError too,
            # and it said "Can't reach chess.com" with the internet fine (27 Oct, a new PC)
            offline = (isinstance(e, (urllib.error.URLError, ConnectionError, TimeoutError))
                       and not isinstance(e, urllib.error.HTTPError) and STATE.get("phase") == "downloading your games")
            STATE.update(phase="error", error="offline" if offline else str(e)[:200])  # chess.com busy or a file error is not "offline"
        WAKE.wait(EVERY)
        WAKE.clear()


def install_listening():
    """Download the listening model in the background; progress shows in /api/status."""
    from coach.get_voice import download_hearing
    STATE["listen_install"] = {"done": 0, "total": 0}
    try:
        download_hearing(lambda done, total: STATE.update(listen_install={"done": done, "total": total}))
        STATE["listen_install"] = None
    except Exception as e:
        log.exception("listening download failed")
        STATE["listen_install"] = {"error": str(e)[:200]}


def warm_voice():
    """Load the voice once at start, so the coach's first sentence comes quickly."""
    from coach import voice
    try:
        if voice.available() and settings.load()["voice"]:
            voice.warm()
    except Exception:
        log.exception("voice warm-up failed")


def start():
    """Start the server and the update loop in the background. Returns the server, or None if already running."""
    LOGBOOK.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(LOGBOOK / "service.log", maxBytes=200_000, backupCount=1)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    log.addHandler(handler)
    log.setLevel(logging.INFO)
    try:
        server = Server(("127.0.0.1", PORT), Handler)
    except OSError:
        log.info("already running (port %d in use)", PORT)
        return None
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "service.pid").write_text(str(os.getpid()))
    log.info("started")
    threading.Thread(target=server.serve_forever, daemon=True).start()
    threading.Thread(target=loop, daemon=True).start()
    threading.Thread(target=warm_voice, daemon=True).start()
    return server


def main():
    server = start()
    if server is None:
        return
    if not player():
        webbrowser.open(f"{URL}/welcome")
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()
