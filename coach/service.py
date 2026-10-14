"""The coach running quietly in the background.

- First start: a welcome page asks for the chess.com username, then shows progress while the games are checked.
- Every 10 minutes: download new games, check them, rebuild the review and practice pages.
- When a new game has been checked: a small Windows notification.
- A local web server on http://127.0.0.1:8765 (this computer only) that serves the pages, the guided set-up of the
  browser extension, and tells the extension the key moments of a finished game.

Run:  python -m coach.service   (the installed app, ChessCoach.exe, runs this behind its tray icon)
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

import chess
import chess.pgn

from coach import analyze, drills, fetch, health, memory, puzzles, review, settings
from coach.paths import BUNDLED_EXTENSION, DATA, EXTENSION, FROZEN, LOGBOOK, NAME, PACKAGE, TEMPLATES, VERSION
from coach.patterns import classify
from coach.review import explain, move_number

PORT = int(os.environ.get("KNIGHTWISE_PORT", "8765"))  # another port only for a second copy while developing
URL = f"http://127.0.0.1:{PORT}"
EVERY = 600  # seconds between checks for new games
MOMENTS = 3  # key moments shown per game
# notifications say "Knightwise": the Store app's own id, or the id the installer gives the Start menu shortcut
APP_ID = f"{PACKAGE}!Knightwise" if PACKAGE else "Abhra71.ChessCoach"

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
    why = explain(pattern, r) if pattern else f"Better was {r['best']}."
    say = why
    if real and best_reply and real != best_reply:
        say += f" In the game they missed it and played {after.san(real)}."
    return {
        "steps": walk(r, mine, best, best_reply, real, after, why),
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
        "pattern": pattern if pattern != "other" else "a big mistake",
        "say": say,
        "loss": r["loss"],
    }


def walk(r, mine, best, best_reply, real, after, why):
    """One key moment told one step at a time (debrief points 17, 18, 42): You played, Better, They replied, Their
    better. Each step says which board it's on ("before" or "after" your move) and its arrows."""
    g = grade(r["loss"])
    a = "an" if g[0] in "AEIOU" else "a"
    steps = [{"kind": "mine", "title": "You played", "san": r["move"], "board": "before",
              "text": f"You played {r['move']}, {a} {g.lower()}.", "arrows": [[mine.uci(), "mine"]]}]
    if best != mine:
        steps.append({"kind": "better", "title": "Better", "san": r["best"], "board": "before",
                      "text": f"Better was {r['best']}. It kept about {round(r['loss'])}% more of your chance to win.",
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
                from coach import insights
                body.update(insights.extras_for(path.rsplit("/", 1)[-1]))
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
        if path == "/api/coach":  # what the coach of a chess.com section says (the extension shows it)
            return self.send(200, json.dumps(coach_says(self.path)), "application/json")
        if path == "/api/hello":  # the browser extension says it is installed and can reach the coach
            STATE["extension_seen"] = time.strftime("%Y-%m-%d %H:%M")
            STATE.setdefault("extension_in", {})[browser_of(self.headers.get("User-Agent"))] = STATE["extension_seen"]
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
            return self.send(200, json.dumps(insights.home()), "application/json")
        if path == "/api/games":
            return self.send(200, json.dumps(insights.games_list()), "application/json")
        if path.startswith("/api/games/"):
            detail = insights.game_detail(path.rsplit("/", 1)[-1])
            return self.send(200 if detail else 404, json.dumps(detail or {"message": "Game not found."}), "application/json")
        if path == "/api/warmup":  # chess.com home: three positions from today's practice, before you play
            from coach import drills
            return self.send(200, json.dumps(drills.warmup()), "application/json")
        if path == "/api/practice-set":
            from coach import brief
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
                out = plan.plan(engine=live_engine.get())
            from coach import brief
            for item in list((out.get("items") or {}).values()) + [out.get("novelty")]:
                if item and item.get("drills"):
                    brief.add(item["drills"])
            return self.send(200, json.dumps(out), "application/json")
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
            except urllib.error.HTTPError as e:
                return self.send(404, json.dumps({"message": "No chess.com player with that name." if e.code == 404
                                                  else "chess.com didn't answer. Try again."}), "application/json")
            except OSError:
                return self.send(503, json.dumps({"message": "Couldn't reach chess.com. Are you online?"}), "application/json")
            return self.send(200 if out else 404, json.dumps(out or {"message": "They have no public games in the last 3 months."}), "application/json")
        if path == "/api/calc":  # the calculation trainer: see the whole line before anything moves (0.9)
            from coach import brief, drills
            items = drills.calculation(insights.home().get("rating"), time.strftime("%Y-%m-%d"))
            return self.send(200, json.dumps(brief.add(items)), "application/json")
        if path == "/api/repertoire" or path.startswith("/api/repertoire/"):  # your three opening lines (0.8)
            from coach import brief, live_engine, repertoire
            from urllib.parse import parse_qs, urlsplit
            fresh = parse_qs(urlsplit(self.path).query).get("fresh") == ["1"]
            with live_engine.LOCK:
                lines = repertoire.build(live_engine.get(), fresh=fresh)
            if path == "/api/repertoire":
                return self.send(200, json.dumps([{k: l[k] for k in ("id", "name", "side", "against", "style", "kept")}
                                                  for l in lines]), "application/json")
            i = path.rsplit("/", 1)[-1]
            if not i.isdigit() or int(i) >= len(lines):
                return self.send(404, json.dumps({"message": "No such line."}), "application/json")
            item = repertoire.lesson(lines[int(i)])
            brief.add(item["drills"])
            return self.send(200, json.dumps(item), "application/json")
        if path == "/api/ladder":  # your level: every skill from beginner to 2,000+, on your last 20 games (0.6)
            from coach import ladder
            return self.send(200, json.dumps(ladder.page()), "application/json")
        if path.startswith("/api/lesson/"):  # a lesson on one Lichess theme at your level, for the ladder's skills
            from coach import brief, plan, puzzles
            import random as _random
            theme = path.rsplit("/", 1)[-1]
            if theme not in puzzles.KEEP_THEMES or theme not in plan.THEME_NAME:
                return self.send(404, json.dumps({"message": "No such lesson."}), "application/json")
            kind = plan.endgame if theme.endswith("Endgame") else plan.tactic
            item = kind(theme, insights.home().get("rating"), _random.Random(theme + time.strftime("%Y-%m-%d")))
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
        if self.headers.get("Content-Type") != "application/json":
            return self.send(403, "forbidden", "text/plain")
        try:
            big = ("/api/save-picture", "/api/copy-picture")  # a picture of your week is bigger
            limit = 4_000_000 if self.path in big else 10_000
            body = json.loads(self.rfile.read(min(int(self.headers.get("Content-Length", 0)), limit)))
        except ValueError:
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
        if path == "/api/endgame/move":  # your move in the endgame trainer, its check, and the best defence
            from coach import endgames
            try:
                out = endgames.play(str(body["id"]), str(body["fen"]), str(body["uci"])[:5], max(0, min(99, int(body.get("made", 0)))),
                                    int(body.get("limit") or 0))
            except (KeyError, ValueError):
                out = None
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
        if path == "/api/player":
            ok, message = set_player(str(body.get("username", "")))
            return self.send(200 if ok else 400, json.dumps({"ok": ok, "message": message}), "application/json")
        if path == "/api/daily/done":
            from coach import daily
            return self.send(200, json.dumps(daily.done()), "application/json")
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
            entry.update(helped=max(0, min(5, int(body.get("helped") or 0))), version=VERSION, at=time.strftime("%Y-%m-%d %H:%M"))
            DATA.mkdir(parents=True, exist_ok=True)
            with open(DATA / "feedback.jsonl", "a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry) + "\n")
            note_in_logbook(f"Feedback saved ({entry['page']}): {entry['wrong'][:80]}")
            return self.send(200, json.dumps({"saved": True}), "application/json")
        if path == "/api/talk":  # a spoken turn with a coach: the reply, and one checked thing to do (0.6)
            from coach import talk
            turns = body.get("history") if isinstance(body.get("history"), list) else []
            history = [(str(t[0]), str(t[1])) for t in turns[-6:] if isinstance(t, list) and len(t) == 2]
            where = body.get("where") if isinstance(body.get("where"), dict) else {}
            where = {k: str(v)[:40] for k, v in where.items() if k in ("section", "game", "step")}
            return self.send(200, json.dumps(talk.reply(str(body.get("coach", "maya")), str(body.get("text", "")),
                                                        history, where)), "application/json")
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
                                  else str(body["voice"]))
            except Exception as e:
                log.exception("voice failed")
                return self.send(500, json.dumps({"message": str(e)[:200]}), "application/json")
            return self.send(200, audio, "audio/wav")
        if path == "/api/keys":
            try:
                settings.set_key(str(body.get("slot")), str(body.get("provider")), str(body.get("key", "")))
            except ValueError as e:
                return self.send(400, json.dumps({"message": str(e)}), "application/json")
            return self.send(200, json.dumps(settings.public()), "application/json")
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
        if path == "/api/show":  # a second ChessCoach.exe (or a notification) asks the running one to show a screen
            route = str(body.get("route", "home"))[:100]
            if SHOW and all(c.isascii() and (c.isalnum() or c == "/") for c in route):  # it goes into the window's JS
                SHOW(route)
            return self.send(200, "{}", "application/json")
        self.send(404, "not found", "text/plain")

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
        try:
            text, provider = ai.hear(pcm, hearing.RATE)
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
                answer = ai.ask(str(body.get("question", "")), context, rating)
        except ai.NoKey as e:
            return self.send(400, json.dumps({"message": str(e), "no_key": True}), "application/json")
        except ValueError:
            return self.send(400, json.dumps({"message": "That isn't a chess position."}), "application/json")
        except Exception as e:
            log.warning("AI failed: %s", e)
            return self.send(502, json.dumps({"message": f"The AI didn't answer: {str(e)[:200]}"}), "application/json")
        return self.send(200, json.dumps(answer), "application/json")

    def static(self, name, root=None):
        """Files of the desktop app (coach/ui), or the extension's drawings; nothing outside them."""
        root = root or UI
        target = (root / name).resolve()
        if root.resolve() not in target.parents or not target.is_file():
            return self.send(404, "not found", "text/plain")
        types = {".js": "text/javascript", ".css": "text/css", ".png": "image/png", ".jpg": "image/jpeg",
                 ".svg": "image/svg+xml", ".glb": "model/gltf-binary", ".gltf": "model/gltf+json",
                 ".bin": "application/octet-stream", ".wav": "audio/wav", ".flac": "audio/flac", ".ogg": "audio/ogg", ".json": "application/json"}
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


class Server(ThreadingHTTPServer):
    """Only one copy may run: no sharing the port (on Windows the default lets a second copy bind it too)."""
    allow_reuse_address = False

    def server_bind(self):
        import socket
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


def extension_stamp():
    """A fingerprint of the extension folder Chrome loads (names, sizes, times)."""
    import hashlib
    h = hashlib.sha1()
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
    return said


def player():
    path = DATA / "player.txt"
    return path.read_text().strip() if path.exists() else None


def status():
    return {"version": VERSION, "player": player(), "last_update": STATE.get("last_update"), "phase": STATE.get("phase"),
            "done": STATE.get("done", 0), "total": STATE.get("total", 0), "error": STATE.get("error"),
            "review_ready": (DATA / "review.html").exists(), "extension_seen": STATE.get("extension_seen"),
            "extension_in": STATE.get("extension_in", {}), "health": health.summary(),
            "extension_path": str(EXTENSION), "browsers": sorted(browsers()), "listen_install": STATE.get("listen_install")}


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
    fetch.fetch(player())
    if not puzzles.current():  # first run, or the library grew
        STATE["phase"] = "downloading puzzles"
        puzzles.main()
    STATE["phase"] = "checking your games"
    checked = analyze.main(argv=[], progress=lambda done, total: STATE.update(done=done, total=total))
    today = time.strftime("%Y-%m-%d")
    STATE["phase"] = "building your pages"
    if checked or first:
        review.build()
    if checked or first or STATE.get("practice_day") != today:  # new practice every day: puzzles, due positions
        drills.build()
        STATE["practice_day"] = today
    STATE.update(phase="ready", last_update=time.strftime("%Y-%m-%d %H:%M"))
    return checked, first


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
            n, first = update_once()
            if first:
                notify(NAME, f"Your review is ready: {n} games checked. Click to open it.", open_link("home"))
            elif n:
                log.info("checked %d new games", n)
                text, newest = summary_of_new(n)
                notify(NAME, text, open_link(f"games/{newest}"))
        except Exception as e:
            log.exception("update failed")
            STATE.update(phase="error", error=str(e)[:200])
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
            voice.say("Ready.")
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
