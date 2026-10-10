"""ChessCoach.exe: the coach's own window, plus an icon by the clock.

Starts the background coach (coach.service) and opens the app in its own window (Windows' built-in WebView2).
Closing the window keeps the coach running by the clock; "Quit" in the icon's menu really stops it.
Opening ChessCoach.exe again (Start menu, a notification) just brings the running window back.
"""
import json
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


def at_login():
    """Started by Windows at sign-in (not by the player)? Then wait quietly by the clock instead of opening a window.
    The installer passes --background; the Store app's start-up task can't pass anything, so: just signed in, no link."""
    if "--background" in sys.argv:
        return True
    if not PACKAGED or len(sys.argv) > 1 or sys.platform != "win32":
        return False
    import ctypes
    ctypes.windll.kernel32.GetTickCount64.restype = ctypes.c_uint64
    return ctypes.windll.kernel32.GetTickCount64() < 4 * 60 * 1000  # Windows started less than 4 minutes ago


def main():
    import webview

    from coach import service

    route = next((a.split("chesscoach://", 1)[1] for a in sys.argv[1:] if a.startswith("chesscoach://")), "home")
    if sys.platform == "win32" and not PACKAGED:  # taskbar shows "Knightwise", not Python (the Store app has its own id)
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(service.APP_ID)
    server = service.start()
    if server is None:  # already running: bring that window forward instead
        ask_running_copy(route)
        return

    state = {"quitting": False}
    place_extension()
    window = webview.create_window(NAME, f"{service.URL}/#/{route}", width=1240, height=820, hidden=at_login(),
                                   min_size=(900, 620), background_color="#0A0A0A")

    def show(where):
        window.evaluate_js(f"location.hash = '#/{where.strip('/')}'")
        window.show()
        window.restore()

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
    multiprocessing.freeze_support()  # the game checker uses several processes; needed inside ChessCoach.exe
    main()
