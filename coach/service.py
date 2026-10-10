"""The coach running quietly in the background.

- Every 10 minutes: download new games, check them, rebuild the review and practice pages.
- When a new game has been checked: a small Windows notification.
- A local web server on http://127.0.0.1:8765 (this computer only) that serves the pages and tells the browser
  extension the key moments of a finished game.

Run:  python -m coach.service          (python -m coach.autorun install  starts it with Windows)
"""
import json
import logging
import os
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from logging.handlers import RotatingFileHandler
from pathlib import Path

import chess

from coach import analyze, drills, fetch, memory, review
from coach.patterns import classify
from coach.review import explain, move_number

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
PORT = 8765
EVERY = 600  # seconds between checks for new games
MOMENTS = 3  # key moments shown per game

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
        "pattern": pattern if pattern != "other" else "a big mistake", "say": explain(pattern, r) if pattern else f"Better was {r['best']}.",
        "loss": r["loss"],
    }


def _after(fen, move):
    board = chess.Board(fen)
    board.push(move)
    return board.fen().split()[0]


def key_moments(rows):
    """The few moves that cost the most in one game, in game order."""
    big = [r for r in rows if classify(r)]
    big = sorted(big, key=lambda r: -r["loss"])[:MOMENTS]
    return [moment(r) for r in sorted(big, key=lambda r: r["ply"])]


MOMENT_CACHE = Moments()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0].rstrip("/")
        if path.startswith("/api/game/"):
            rows = MOMENT_CACHE.get(path.rsplit("/", 1)[-1])
            # unknown game = not finished and checked yet: say nothing (fair play)
            body = {"known": rows is not None, "moments": key_moments(rows) if rows else []}
            return self.send(200, json.dumps(body), "application/json")
        if path == "/api/status":
            player = (DATA / "player.txt").read_text().strip() if (DATA / "player.txt").exists() else None
            return self.send(200, json.dumps({"player": player, "last_update": STATE.get("last_update")}),
                             "application/json")
        if path == "/api/stats":
            return self.send(200, json.dumps(memory.practice_stats()), "application/json")
        pages = {"": "review.html", "/review": "review.html", "/review.html": "review.html",
                 "/practice": "drills.html", "/drills.html": "drills.html"}
        if path in pages and (DATA / pages[path]).exists():
            return self.send(200, (DATA / pages[path]).read_bytes(), "text/html; charset=utf-8")
        self.send(404, "not found", "text/plain")

    def do_POST(self):
        """Answers from our own pages only: JSON from http://127.0.0.1:8765 (other sites can't send JSON here)."""
        origin = self.headers.get("Origin")
        if origin not in (None, f"http://127.0.0.1:{PORT}") or self.headers.get("Content-Type") != "application/json":
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
        self.send(404, "not found", "text/plain")

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


STATE = {}


class Server(ThreadingHTTPServer):
    """Only one copy may run: no sharing the port (on Windows the default lets a second copy bind it too)."""
    allow_reuse_address = False

    def server_bind(self):
        import socket
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


def note_in_logbook(line):
    """One line in the player's chess logbook (logbook/chess.md)."""
    book = ROOT / "logbook" / "chess.md"
    book.parent.mkdir(exist_ok=True)
    with open(book, "a", encoding="utf-8") as fh:
        fh.write(f"- {time.strftime('%d %b %Y')}: {line}\n")


def notify(title, text, url):
    """Windows toast notification (built into Windows, nothing to install). Clicking it opens `url`."""
    xml = (f'<toast activationType="protocol" launch="{url}"><visual><binding template="ToastGeneric">'
           f'<text>{title}</text><text>{text}</text></binding></visual></toast>')
    ps = (
        "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType=WindowsRuntime]|Out-Null;"
        "[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType=WindowsRuntime]|Out-Null;"
        "$x=New-Object Windows.Data.Xml.Dom.XmlDocument;$x.LoadXml($env:COACH_TOAST);"
        "$app='{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\\WindowsPowerShell\\v1.0\\powershell.exe';"
        "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($app)"
        ".Show([Windows.UI.Notifications.ToastNotification]::new($x))"
    )
    result = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
                            env={**os.environ, "COACH_TOAST": xml}, capture_output=True, text=True,
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), timeout=30)
    if result.returncode:
        log.warning("notification failed: %s", result.stderr[:300])


def update_once():
    """New games -> check -> pages. Returns how many new games were checked."""
    user = (DATA / "player.txt").read_text().strip()
    fetch.fetch(user)
    checked = analyze.main(argv=[])
    today = time.strftime("%Y-%m-%d")
    if checked:
        review.build()
    if checked or STATE.get("practice_day") != today:  # new practice every day: new puzzles, due positions
        drills.build()
        STATE["practice_day"] = today
    STATE["last_update"] = time.strftime("%Y-%m-%d %H:%M")
    return checked


def summary_of_new(n):
    """One line about the newest games for the notification."""
    rows = [json.loads(line) for line in open(DATA / "moves.jsonl")]
    end = {g["url"]: g["end_time"] for f in DATA.glob("games-*.json") for g in json.loads(f.read_text())["games"]}
    newest = sorted({r["url"] for r in rows}, key=lambda u: end.get(u, 0))[-n:]
    lost = sum(1 for r in rows if r["url"] in newest and classify(r) in review.LOSING_MATERIAL)
    games = "1 new game" if n == 1 else f"{n} new games"
    return f"{games} checked. Pieces given away: {lost}. Click to see your key moments."


def loop():
    while True:
        try:
            n = update_once()
            if n:
                log.info("checked %d new games", n)
                notify("Chess Coach", summary_of_new(n), f"http://127.0.0.1:{PORT}/")
        except Exception:
            log.exception("update failed")
        time.sleep(EVERY)


def main():
    (ROOT / "logbook").mkdir(exist_ok=True)
    handler = RotatingFileHandler(ROOT / "logbook" / "service.log", maxBytes=200_000, backupCount=1)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    log.addHandler(handler)
    log.setLevel(logging.INFO)
    try:
        server = Server(("127.0.0.1", PORT), Handler)
    except OSError:
        log.info("already running (port %d in use), exiting", PORT)
        return
    log.info("started")
    threading.Thread(target=loop, daemon=True).start()
    server.serve_forever()


if __name__ == "__main__":
    main()
