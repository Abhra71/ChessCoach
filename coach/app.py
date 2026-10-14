"""Knightwise.exe: the coach's own window, plus an icon by the clock.

Starts the background coach (coach.service) and opens the app in its own window (Windows' built-in WebView2).
Closing the window keeps the coach running by the clock; "Quit" in the icon's menu really stops it.
Opening Knightwise.exe again (Start menu, a notification) just brings the running window back.
"""
import json
import os
import multiprocessing
import sys
import threading
import urllib.request

from coach.paths import ICON, NAME, PACKAGED, place_extension


def ask_running_copy(route):
    """Tell the coach that is already running to show its window. True if it answered."""
    from coach import service
    req = urllib.request.Request(f"{service.URL}/api/show", data=json.dumps({"route": route}).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=3)
        return True
    except OSError:
        return False


def _older(running, mine):
    as_tuple = lambda v: tuple(int(x) for x in str(v).split(".") if x.isdigit()) or (0,)
    return as_tuple(running) < as_tuple(mine)


def replace_older_copy():
    """An older Knightwise still running (it starts with Windows) would answer for this one: on 14 Oct an installed
    0.4.1 held the port and the 0.5.0 test copy quietly gave way to it. Close that older copy. True if it closed."""
    import subprocess
    from coach import service
    from coach.paths import VERSION
    try:
        running = json.loads(urllib.request.urlopen(f"{service.URL}/api/status", timeout=3).read()).get("version", "0")
    except (OSError, ValueError):
        return False
    if not _older(running, VERSION) or sys.platform != "win32":
        return False
    quiet = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    lines = subprocess.run(["netstat", "-ano", "-p", "TCP"], capture_output=True, text=True, creationflags=quiet).stdout
    pids = {ln.split()[-1] for ln in lines.splitlines() if f"127.0.0.1:{service.PORT} " in ln and "LISTENING" in ln}
    for pid in pids:
        image = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"], capture_output=True, text=True,
                               creationflags=quiet).stdout.lower()
        if "knightwise.exe" in image or "chesscoach.exe" in image or "python" in image:  # only ever Knightwise (its old name too)
            subprocess.run(["taskkill", "/PID", pid, "/F"], capture_output=True, creationflags=quiet)
    import time
    time.sleep(1.5)
    return bool(pids)


def tray(show, quit_app):
    import pystray
    from PIL import Image

    from coach import service

    def check_now(icon, item):
        service.WAKE.set()
        icon.notify("Checking chess.com for new games…", NAME)

    icon = pystray.Icon("Knightwise", Image.open(ICON), NAME, menu=pystray.Menu(
        pystray.MenuItem("Open Knightwise", lambda icon, item: show("home"), default=True),
        pystray.MenuItem("Practice", lambda icon, item: show("practice")),
        pystray.MenuItem("Check for new games now", check_now),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit Knightwise", lambda icon, item: quit_app()),
    ))
    icon.run_detached()
    return icon


def allow_microphone(window):
    """Let our own page (127.0.0.1) use the microphone for "Talk", without an endless permission wait.
    Any other page's request is left alone (WebView2 decides as usual)."""
    import System
    from Microsoft.Web.WebView2.Core import CoreWebView2PermissionKind, CoreWebView2PermissionState
    browser = window.native.browser

    def on_permission(sender, args):
        if args.Uri.startswith("http://127.0.0.1:") and args.PermissionKind == CoreWebView2PermissionKind.Microphone:
            args.State = CoreWebView2PermissionState.Allow

    def subscribe():  # the engine may only be touched from the window's own thread
        browser.webview.CoreWebView2.PermissionRequested += on_permission

    window.native.Invoke(System.Action(subscribe))


def at_login(set_up):
    """Started by Windows at sign-in (not by the player)? Then wait quietly by the clock instead of opening a window.
    The installer passes --background; the Store app's start-up task can't pass anything, so: just signed in, no link.
    Never before set-up: the very first start (a new player, or a Store tester) always shows the welcome screen."""
    if not set_up:
        return False
    if "--background" in sys.argv:
        return True
    if not PACKAGED or len(sys.argv) > 1 or sys.platform != "win32":
        return False
    minutes = minutes_since_sign_in()
    return minutes is not None and minutes < 4  # Windows starts its start-up apps right after you sign in


def minutes_since_sign_in():
    """How long ago the player signed in to Windows. Not the time since Windows started: with Fast Startup,
    turning the PC on resumes a saved Windows, so it can say it started days ago while you signed in just now."""
    import ctypes
    from ctypes import wintypes

    class Info(ctypes.Structure):  # WTSINFOW
        _fields_ = [("State", ctypes.c_int), ("SessionId", wintypes.DWORD)] +                    [(n, wintypes.DWORD) for n in ("InBytes", "OutBytes", "InFrames", "OutFrames", "InComp", "OutComp")] +                    [("Station", wintypes.WCHAR * 32), ("Domain", wintypes.WCHAR * 17), ("User", wintypes.WCHAR * 21)] +                    [(n, ctypes.c_int64) for n in ("Connect", "Disconnect", "LastInput", "Logon", "Now")]
    wts, buf, size = ctypes.windll.wtsapi32, ctypes.c_void_p(), wintypes.DWORD()
    try:
        if not wts.WTSQuerySessionInformationW(None, wintypes.DWORD(0xFFFFFFFF), 24, ctypes.byref(buf), ctypes.byref(size)):
            return None
        info = ctypes.cast(buf, ctypes.POINTER(Info)).contents
        return (info.Now - info.Logon) / 1e7 / 60 if info.Logon else None
    except OSError:
        return None
    finally:
        if buf:
            wts.WTSFreeMemory(buf)


def main():
    # the welcome's music may start by itself (the window only ever shows our own pages, never other sites)
    os.environ.setdefault("WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS", "--autoplay-policy=no-user-gesture-required")
    import webview

    from coach import service

    route = next((a.split("chesscoach://", 1)[1] for a in sys.argv[1:] if a.startswith("chesscoach://")), "home")
    if sys.platform == "win32" and not PACKAGED:  # taskbar shows "Knightwise", not Python (the Store app has its own id)
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(service.APP_ID)
    server = service.start()
    if server is None and replace_older_copy():
        server = service.start()
    if server is None:  # already running: bring that window forward instead
        ask_running_copy(route)
        return

    state = {"quitting": False}
    place_extension()
    window = webview.create_window(NAME, f"{service.URL}/#/{route}", width=1240, height=820, maximized=True, hidden=at_login(bool(service.player())),
                                   min_size=(900, 620), background_color="#0A0A0A")

    def show(where):
        window.evaluate_js(f"location.hash = '#/{where.strip('/')}'")
        window.show()
        window.maximize()  # also un-minimises; restore() would shrink it back to 1240×820

    def quit_app():
        state["quitting"] = True
        icon.stop()
        window.destroy()

    def on_closing():
        if state["quitting"]:
            return True
        window.hide()  # keep coaching in the background; the icon by the clock brings it back
        return False

    window.events.closing += on_closing

    def on_loaded():
        if not state.get("mic"):
            state["mic"] = True
            try:
                allow_microphone(window)
            except Exception as e:  # never stop the app over the microphone
                service.log.warning("microphone permission hook failed: %s", e)

    window.events.loaded += on_loaded
    service.SHOW = lambda where: threading.Thread(target=show, args=(where,), daemon=True).start()
    icon = tray(show, quit_app)
    webview.start(private_mode=False, storage_path=str(service.DATA.parent / "webview"))
    server.shutdown()


if __name__ == "__main__":
    multiprocessing.freeze_support()  # the game checker uses several processes; needed inside Knightwise.exe
    main()
