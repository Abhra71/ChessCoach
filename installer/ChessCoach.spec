# PyInstaller recipe for ChessCoach.exe (a folder app: faster start than one big file).
# Build:  python -m PyInstaller installer/ChessCoach.spec --noconfirm   (needs engine/ from python -m coach.get_engine)
from pathlib import Path

ROOT = Path(SPECPATH).parent

a = Analysis(
    [str(ROOT / "coach" / "app.py")],
    pathex=[str(ROOT)],
    datas=[
        (str(ROOT / "engine"), "engine"),                     # Stockfish
        (str(ROOT / "extension"), "extension"),               # icon for the tray
        (str(ROOT / "coach" / "drills_template.html"), "coach"),
        (str(ROOT / "coach" / "ui"), "coach/ui"),             # the desktop app's screens
        (str(ROOT / "coach" / "setup_arrows.html"), "coach"),
    ],
    hiddenimports=["pystray._win32", "coach.service", "coach.drills", "coach.puzzles", "coach.insights",
                   "coach.settings", "keyring.backends.Windows", "webview.platforms.edgechromium"],
    excludes=["tkinter", "pytest"],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="ChessCoach",
    icon=str(ROOT / "installer" / "ChessCoach.ico"),
    console=False,  # no black window
)
coll = COLLECT(exe, a.binaries, a.datas, name="ChessCoach")
