"""Updates without the player doing anything (1.2; the owner, 20 Nov: "big apps do not require removing it from the tray").

The Microsoft Store downloads a new Knightwise by itself, but Windows can't switch to it while Knightwise runs, and
Knightwise always runs by the clock. So the Store app learns the newest version from the fix file (fixes.json on
GitHub, read once a day: "latest"), and when that is newer than itself it waits for a calm moment: the window closed
or minimised, nobody using the coach (the app or the extension) for 10 minutes, no game check running. Then it asks
Windows to start it again in about two minutes (a one-time scheduled task that opens chesscoach://background, so it
comes back quietly by the clock) and quits. Windows finishes the waiting update while it's closed.

At most one quiet try a day for each new version. If Knightwise comes back still old (the Store hadn't downloaded it
yet), Home shows "Update ready" with a button to try now, and a button to the Store page.

Fair play: nothing here reads a game. A restart during someone's live game changes nothing there: the coach is off.
"""
import json
import logging
import subprocess
import threading
import time

from coach import fixes
from coach.paths import DATA, PACKAGED, VERSION

log = logging.getLogger("knightwise")
TASK = "Knightwise restart"
QUIET_MINUTES = 10  # nobody used the coach for this long
EVERY = 300  # look every 5 minutes
STORE_ID = "9NKLGS6K72J2"
FILE = DATA / "update-try.json"  # {"version": tried for, "day": "YYYY-MM-DD", "from": the version that tried}

WINDOW = {"shown": False, "since": time.time()}  # set by the app window (coach/app.py)
USE = {"at": time.time()}  # the last time the player used the app or the extension
HOUSEKEEPING = {"/api/status", "/api/hello", "/api/fixes", "/api/extension-stamp", "/api/health"}  # timers, not a person


def as_tuple(v):
    return tuple(int(x) for x in str(v).split(".") if x.isdigit()) or (0,)


def newer(latest, mine=None):
    """Is `latest` a newer version than `mine` (this copy)? "1.2.0" > "1.1.0"; nothing or rubbish is never newer."""
    return bool(latest) and as_tuple(latest) > as_tuple(VERSION if mine is None else mine)


def latest():
    return fixes.current().get("latest")


def used(path):
    """Every request: the player's own use resets the quiet clock, the timers don't."""
    if path.split("?")[0].rstrip("/") not in HOUSEKEEPING:
        USE["at"] = time.time()


def window(shown):
    if shown != WINDOW["shown"]:
        WINDOW.update(shown=shown, since=time.time())


def _tried():
    try:
        return json.loads(FILE.read_text())
    except (OSError, ValueError):
        return {}


def calm(state, busy, now=None):
    """A calm moment: the window away, no use for 10 minutes, no game check running."""
    now = now or time.time()
    quiet = QUIET_MINUTES * 60
    return (not WINDOW["shown"] and now - WINDOW["since"] >= quiet and now - USE["at"] >= quiet
            and not busy and state.get("phase") in ("ready", "error") and not state.get("older")
            and not state.get("practice_pending") and not state.get("listen_install"))


def should_try(state, busy, today=None, now=None):
    """Time for the quiet restart: a newer version, a calm moment, and not tried for it today."""
    want = latest()
    if not PACKAGED or not newer(want):
        return False
    t = _tried()
    if t.get("version") == want and t.get("day") == (today or time.strftime("%Y-%m-%d")):
        return False
    return calm(state, busy, now)


def status():
    """For Home: {"latest": "1.2.0", "tried": True} when a newer version is out; None when we're current."""
    want = latest()
    if not PACKAGED or not newer(want):
        return None
    return {"latest": want, "tried": _tried().get("version") == want}


def _schedule(route, minutes=2):
    """Ask Windows to open Knightwise again in a couple of minutes, from outside the app (so the app is fully closed
    and Windows can switch to the new version meanwhile). A one-time task; the next start removes it."""
    # PowerShell's scheduler takes a real time (schtasks wants the date written the way this PC's language writes it:
    # day/month in India, so a restart near midnight could land on the wrong day)
    ps = ("$a = New-ScheduledTaskAction -Execute 'explorer.exe' -Argument $env:KW_LINK; "
          "$t = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes([int]$env:KW_MIN); "
          # on a laptop's battery too (Windows' default skips scheduled tasks on battery), and late if it was asleep
          "$s = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable; "
          "Register-ScheduledTask -TaskName $env:KW_TASK -Action $a -Trigger $t -Settings $s -Force | Out-Null")
    import os
    quiet = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps], capture_output=True, text=True,
                           env={**os.environ, "KW_LINK": f"chesscoach://{route}", "KW_MIN": str(minutes), "KW_TASK": TASK},
                           creationflags=quiet, timeout=60)
    except (OSError, subprocess.SubprocessError) as e:
        log.warning("update: couldn't schedule the restart: %s", e)
        return False
    if r.returncode:
        log.warning("update: couldn't schedule the restart: %s", (r.stderr or r.stdout)[:300])
    return r.returncode == 0


def restart(quit_app, route="background"):
    """Schedule the comeback, note the try, quit. Never quits without a comeback scheduled. True if it quit."""
    want = latest() or ""
    if not _schedule(route):
        return False
    FILE.parent.mkdir(parents=True, exist_ok=True)
    FILE.write_text(json.dumps({"version": want, "day": time.strftime("%Y-%m-%d"), "from": VERSION}))
    log.info("update: %s is out (this is %s): restarting so Windows can finish it", want, VERSION)
    quit_app()
    return True


def on_start():
    """Knightwise just started: remove the comeback task, and note in the logbook whether the update took."""
    if not PACKAGED:
        return
    quiet = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        subprocess.run(["schtasks", "/Delete", "/F", "/TN", TASK], capture_output=True, creationflags=quiet, timeout=30)
    except Exception:
        pass
    t = _tried()
    if t.get("from") and t.get("from") != VERSION:
        log.info("update: now %s (was %s)", VERSION, t["from"])
        FILE.unlink(missing_ok=True)
    elif t.get("from"):
        log.info("update: still %s after the restart; %s isn't downloaded yet", VERSION, t.get("version"))


def store_page():
    """The Store's own page for Knightwise, where "Update" installs it right away."""
    import os
    os.startfile(f"ms-windows-store://pdp/?productid={STORE_ID}")


def watch(state, lock, quit_app):
    """The background look, every 5 minutes (Store app only)."""
    if not PACKAGED:
        return

    def run():
        while True:
            time.sleep(EVERY)
            try:
                if should_try(state, lock.locked()):
                    restart(quit_app)
                    return
            except Exception:
                log.exception("update watch")
    threading.Thread(target=run, daemon=True).start()
