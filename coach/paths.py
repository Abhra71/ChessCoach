"""Where things live.

From the project folder (developers): everything inside the project (data/, logbook/, engine/).
Installed app (ChessCoach.exe): the program files sit in the install folder; the player's own data and logbooks
go in %LOCALAPPDATA%\\ChessCoach, the normal place for a Windows app's per-user data.
"""
import os
import sys
from pathlib import Path

FROZEN = getattr(sys, "frozen", False)
PROJECT = Path(__file__).resolve().parent.parent
APP = Path(getattr(sys, "_MEIPASS", PROJECT)) if FROZEN else PROJECT  # bundled files (engine, extension)
HOME = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "ChessCoach" if FROZEN else PROJECT

DATA = HOME / "data"
LOGBOOK = HOME / "logbook"
ENGINE = APP / "engine" / "stockfish" / "stockfish-windows-x86-64-universal.exe"
EXTENSION = (Path(sys.executable).parent / "extension") if FROZEN else PROJECT / "extension"
TEMPLATES = Path(__file__).resolve().parent
ICON = APP / "extension" / "icon128.png"
