"""The coach running quietly in the background.

- First start: a welcome page asks for the chess.com username, then shows progress while the games are checked.
- Every 10 minutes: download new games, check them, rebuild the review and practice pages.
- When a new game has been checked: a small Windows notification.
- A local web server on http://127.0.0.1:8765 (this computer only) that serves the pages, the guided set-up of the
  browser extension, and tells the extension the key moments of a finished game.

Run:  python -m coach.service   (the installed app, ChessCoach.exe, runs this behind its tray icon)
"""
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

from coach import analyze, drills, fetch, memory, puzzles, review, settings
from coach.paths import DATA, EXTENSION, FROZEN, LOGBOOK, NAME, PACKAGE, TEMPLATES
from coach.patterns import classify
from coach.review import explain, move_number

PORT = 8765
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


def moment(r):
    """One key moment as the extension needs it: where, which arrows, what to say."""
    pattern = classify(r)
    board = chess.Board(r["fen"])
    mine, best = board.parse_san(r["move"]), board.parse_san(r["best"])
    return {
        "ply": r["ply"], "move_number": move_number(r), "color": r["color"],
        "placement": r["fen"].split()[0],  # the board just before the player's move
        "after_placement": _after(r["fen"], mine),
        "move": r["move"], "move_uci": mine.uci(), "best": r["best"], "best_uci": best.uci(),
        "reply_uci": r["reply_pv"][0] if r["reply_pv"] else None,
        "pattern": pattern if pattern != "other" else "a big mistake",
        "say": explain(pattern, r) if pattern else f"Better was {r['best']}.",
        "loss": r["loss"],
    }


def _after(fen, move):
    board = chess.Board(fen)
    board.push(move)
    return board.fen().split()[0]


def key_moments(rows):
    """The few moves that cost the most in one game, in game order."""
    return [moment(r) for r in review.biggest(rows, MOMENTS)]


MOMENT_CACHE = Moments()
UI = TEMPLATES / "ui"
SHOW = None  # set by the desktop app: show the window at a screen


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"

    def do_GET(self):
        path = self.path.split("?")[0].rstrip("/")
        if path.startswith("/api/game/"):
            rows = MOMENT_CACHE.get(path.rsplit("/", 1)[-1])
            # unknown game = not finished and checked yet: say nothing (fair play)
            body = {"known": rows is not None, "moments": key_moments(rows) if rows else [],
                    "players": players_of(path.rsplit("/", 1)[-1]) if rows is not None else []}
            return self.send(200, json.dumps(body), "application/json")
        if path == "/api/status":
            return self.send(200, json.dumps(status()), "application/json")
        if path == "/api/extension-stamp":  # changes whenever the extension's files change (it then reloads itself)
            return self.send(200, json.dumps({"stamp": extension_stamp()}), "application/json")
        if path == "/api/coach":  # what the coach of a chess.com section says (the extension shows it)
            return self.send(200, json.dumps(coach_says(self.path)), "application/json")
        if path == "/api/hello":  # the browser extension says it is installed and can reach the coach
            STATE["extension_seen"] = time.strftime("%Y-%m-%d %H:%M")
            return self.send(200, "{}", "application/json")
        if path == "/api/listen/warm":  # the player pressed Talk: load the listening model while they speak
            from coach import hearing
            if hearing.available():
                threading.Thread(target=hearing._whisper, daemon=True).start()
            return self.send(200, "{}", "application/json")
        if path == "/api/stats":
            return self.send(200, json.dumps(memory.practice_stats()), "application/json")
        from coach import insights
        if path == "/api/home":
            return self.send(200, json.dumps(insights.home()), "application/json")
        if path == "/api/games":
            return self.send(200, json.dumps(insights.games_list()), "application/json")
        if path.startswith("/api/games/"):
            detail = insights.game_detail(path.rsplit("/", 1)[-1])
            return self.send(200 if detail else 404, json.dumps(detail or {"message": "Game not found."}), "application/json")
        if path == "/api/practice-set":
            practice = DATA / "drills.json"
            return self.send(200, practice.read_bytes() if practice.exists() else b"[]", "application/json")
        if path == "/api/settings":
            return self.send(200, json.dumps(settings.public()), "application/json")
        if path in ("", "/app", "/welcome"):  # the desktop app (it shows the welcome screen itself when needed)
            return self.send(200, (UI / "index.html").read_bytes(), "text/html; charset=utf-8")
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
        origin = self.headers.get("Origin")
        if origin not in (None, URL):
            return self.send(403, "forbidden", "text/plain")
        if self.path.startswith("/api/listen") and self.headers.get("Content-Type") == "application/octet-stream":
            return self.listen()
        if self.headers.get("Content-Type") != "application/json":
            return self.send(403, "forbidden", "text/plain")
        try:
            body = json.loads(self.rfile.read(min(int(self.headers.get("Content-Length", 0)), 10_000)))
        except ValueError:
            return self.send(400, "bad json", "text/plain")
        path = self.path.split("?")[0].rstrip("/")
        if path == "/api/practice" and body.get("kind") in ("game", "puzzle"):
            memory.record_practice(str(body.get("id"))[:200], body["kind"], bool(body.get("right")))
            return self.send(200, json.dumps(memory.practice_stats()), "application/json")
        if path == "/api/verdict" and body.get("answer") in ("yes", "some", "no"):
            memory.record_verdict(body["answer"])
            note_in_logbook(f"Your verdict on the review (\"is this me?\"): {body['answer']}")
            return self.send(200, "{}", "application/json")
        if path == "/api/player":
            ok, message = set_player(str(body.get("username", "")))
            return self.send(200 if ok else 400, json.dumps({"ok": ok, "message": message}), "application/json")
        if path == "/api/chat":  # talking with a coach on chess.com (needs a key; never fails without one)
            from coach import ai, coaches
            turns = body.get("history") if isinstance(body.get("history"), list) else []
            history = [(str(t[0]), str(t[1])) for t in turns[-6:] if isinstance(t, list) and len(t) == 2]
            reply = coaches.chat(str(body.get("coach", "zara")), str(body.get("message", "")), history)
            if not reply["ai"] and ai.ready():
                reply["note"] = "The AI is busy right now, so I'm keeping it short. Ask again in a minute."
            return self.send(200, json.dumps(reply), "application/json")
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
        if path == "/api/open-folder":
            if os.name == "nt":
                os.startfile(DATA.parent)
            return self.send(200, "{}", "application/json")
        if path == "/api/show":  # a second ChessCoach.exe (or a notification) asks the running one to show a screen
            if SHOW:
                SHOW(str(body.get("route", "home"))[:100])
            return self.send(200, "{}", "application/json")
        self.send(404, "not found", "text/plain")

    def listen(self):
        """The player's spoken question: 16 kHz 16-bit mono samples from the app -> text (Whisper, on this computer)."""
        from coach import hearing
        if not hearing.available():
            return self.send(503, json.dumps({"message": "Listening isn't installed. Settings > Voice."}), "application/json")
        size = int(self.headers.get("Content-Length", 0))
        if not 0 < size <= 60 * hearing.RATE * 2:  # at most a minute of speech
            return self.send(400, json.dumps({"message": "Too long or empty."}), "application/json")
        import numpy as np
        samples = np.frombuffer(self.rfile.read(size), dtype="<i2").astype(np.float32) / 32768
        try:
            text = hearing.transcribe(samples)
        except Exception as e:
            log.exception("listening failed")
            return self.send(500, json.dumps({"message": str(e)[:200]}), "application/json")
        return self.send(200, json.dumps({"text": text}), "application/json")

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

    def static(self, name):
        """Files of the desktop app (coach/ui), nothing outside it."""
        target = (UI / name).resolve()
        if UI.resolve() not in target.parents or not target.is_file():
            return self.send(404, "not found", "text/plain")
        types = {".js": "text/javascript", ".css": "text/css", ".png": "image/png", ".jpg": "image/jpeg",
                 ".svg": "image/svg+xml", ".glb": "model/gltf-binary", ".gltf": "model/gltf+json",
                 ".bin": "application/octet-stream", ".wav": "audio/wav", ".flac": "audio/flac", ".json": "application/json"}
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
        self.send_header("Access-Control-Allow-Origin", "*")
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
    said = coaches.speak(q.get("section", "home"), hour=hour % 24, moments=moments)
    from coach import voice
    s = settings.load()
    said["voice_on"] = bool(s.get("voice")) and voice.available()
    said["role"] = coaches.COACHES[said["coach"]]["role"]
    said["ai_ready"] = any(settings.get_key(slot) for slot in settings.SLOTS)
    if not said["ai_ready"]:  # tell everyone the conversation feature exists
        said["ai_hint"] = coaches.AI_HINT
    return said


def player():
    path = DATA / "player.txt"
    return path.read_text().strip() if path.exists() else None


def status():
    return {"player": player(), "last_update": STATE.get("last_update"), "phase": STATE.get("phase"),
            "done": STATE.get("done", 0), "total": STATE.get("total", 0), "error": STATE.get("error"),
            "review_ready": (DATA / "review.html").exists(), "extension_seen": STATE.get("extension_seen"),
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
    if not puzzles.OUT.exists():
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
