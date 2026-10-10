"""Where things live.

From the project folder (developers): everything inside the project (data/, logbook/, engine/).
Installed app (ChessCoach.exe): the program files sit in the install folder; the player's own data and logbooks
go in %LOCALAPPDATA%\\ChessCoach, the normal place for a Windows app's per-user data.
"""
import os
import sys
from pathlib import Path

NAME = "Knightwise"
FROZEN = getattr(sys, "frozen", False)


def package_family():
    """The Store package's family name when running as the Microsoft Store app, else None."""
    if sys.platform != "win32":
        return None
    import ctypes
    size = ctypes.c_uint32(0)
    get = ctypes.windll.kernel32.GetCurrentPackageFamilyName
    if get(ctypes.byref(size), None) != 122:  # 122 = buffer too small: we have a package; anything else: we don't
        return None
    buf = ctypes.create_unicode_buffer(size.value)
    return buf.value if get(ctypes.byref(size), buf) == 0 else None


def documents():
    """The player's Documents folder (wherever OneDrive or the player has moved it)."""
    if sys.platform == "win32":
        import ctypes
        buf = ctypes.create_unicode_buffer(260)
        if ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, buf) == 0:  # 5 = My Documents
            return Path(buf.value)
    return Path.home() / "Documents"


PACKAGE = package_family() if FROZEN else None
PACKAGED = PACKAGE is not None
PROJECT = Path(__file__).resolve().parent.parent
APP = Path(getattr(sys, "_MEIPASS", PROJECT)) if FROZEN else PROJECT  # bundled files (engine, extension)
HOME = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "ChessCoach" if FROZEN else PROJECT

DATA = HOME / "data"
LOGBOOK = HOME / "logbook"
ENGINE = APP / "engine" / "stockfish" / "stockfish-windows-x86-64-universal.exe"
BUNDLED_EXTENSION = APP / "extension"
if PACKAGED:
    EXTENSION = documents() / NAME / "extension"
elif FROZEN:
    EXTENSION = Path(sys.executable).parent / "extension"
else:
    EXTENSION = PROJECT / "extension"
TEMPLATES = Path(__file__).resolve().parent
ICON = APP / "extension" / "icon128.png"


def place_extension():
    """Store app: copy the browser extension where Chrome can load it, again whenever the app brings a newer one."""
    if not PACKAGED:
        return
    import json
    import shutil
    try:
        new = json.loads((BUNDLED_EXTENSION / "manifest.json").read_text(encoding="utf-8"))["version"]
        old = json.loads((EXTENSION / "manifest.json").read_text(encoding="utf-8"))["version"]
    except (OSError, ValueError, KeyError):
        old, new = None, "copy"
    if old != new:
        shutil.copytree(BUNDLED_EXTENSION, EXTENSION, dirs_exist_ok=True)
