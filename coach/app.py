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

from coach.paths import ICON


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
        icon.notify("Checking chess.com for new games…", "Chess Coach")

    icon = pystray.Icon("ChessCoach", Image.open(ICON), "Chess Coach", menu=pystray.Menu(
        pystray.MenuItem("Open Chess Coach", lambda icon, item: show("home"), default=True),
        pystray.MenuItem("Practice", lambda icon, item: show("practice")),
        pystray.MenuItem("Check for new games now", check_now),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit Chess Coach", lambda icon, item: quit_app()),
    ))
    icon.run_detached()
    return icon


def main():
    import webview

    from coach import service

    route = next((a.split("chesscoach://", 1)[1] for a in sys.argv[1:] if a.startswith("chesscoach://")), "home")
    if sys.platform == "win32":  # notifications and taskbar show "Chess Coach", not Python
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(service.APP_ID)
    server = service.start()
    if server is None:  # already running: bring that window forward instead
        ask_running_copy(route)
        return

    state = {"quitting": False}
    window = webview.create_window("Chess Coach", f"{service.URL}/#/{route}", width=1240, height=820,
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
    service.SHOW = lambda where: threading.Thread(target=show, args=(where,), daemon=True).start()
    icon = tray(show, quit_app)
    webview.start(private_mode=False, storage_path=str(service.DATA.parent / "webview"))
    server.shutdown()


if __name__ == "__main__":
    multiprocessing.freeze_support()  # the game checker uses several processes; needed inside ChessCoach.exe
    main()
