"""ChessCoach.exe: the coach with an icon by the clock.

Starts the background coach (coach.service), shows a tray icon with a small menu, and opens the welcome page the
first time. Opening it a second time (e.g. from the Start menu) just opens your review.
"""
import multiprocessing
import sys
import webbrowser

from coach.paths import ICON


def menu_icon():
    import pystray
    from PIL import Image

    from coach import service

    def open_page(path):
        return lambda icon, item: webbrowser.open(f"{service.URL}{path}")

    def check_now(icon, item):
        service.WAKE.set()
        icon.notify("Checking chess.com for new games…", "Chess Coach")

    def quit_app(icon, item):
        icon.stop()

    return pystray.Icon("ChessCoach", Image.open(ICON), "Chess Coach", menu=pystray.Menu(
        pystray.MenuItem("Open my review", open_page("/"), default=True),
        pystray.MenuItem("Practice", open_page("/practice")),
        pystray.MenuItem("Arrows on chess.com", open_page("/setup-arrows")),
        pystray.MenuItem("Check for new games now", check_now),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit Chess Coach", quit_app),
    ))


def main():
    from coach import service

    if sys.platform == "win32":  # notifications and taskbar show "Chess Coach", not Python
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(service.APP_ID)
    server = service.start()
    if server is None:  # already running: just show the review (or the welcome page)
        webbrowser.open(service.URL)
        return
    if not service.player():
        webbrowser.open(f"{service.URL}/welcome")
    menu_icon().run()  # until "Quit"
    server.shutdown()


if __name__ == "__main__":
    multiprocessing.freeze_support()  # the game checker uses several processes; needed inside ChessCoach.exe
    main()
