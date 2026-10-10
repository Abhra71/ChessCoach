# PyInstaller recipe for ChessCoach.exe (a folder app: faster start than one big file).
# Build:  python -m PyInstaller installer/ChessCoach.spec --noconfirm   (needs engine/ from python -m coach.get_engine)
from pathlib import Path

from PyInstaller.utils.hooks import collect_all

ROOT = Path(SPECPATH).parent
VOICE = [collect_all(m) for m in ("kokoro_onnx", "espeakng_loader", "phonemizer", "language_tags", "segments")]

a = Analysis(
    [str(ROOT / "coach" / "app.py")],
    pathex=[str(ROOT)],
    datas=[
        (str(ROOT / "engine"), "engine"),                     # Stockfish
        (str(ROOT / "extension"), "extension"),               # icon for the tray
        (str(ROOT / "coach" / "drills_template.html"), "coach"),
        (str(ROOT / "coach" / "ui"), "coach/ui"),             # the desktop app's screens
        (str(ROOT / "coach" / "setup_arrows.html"), "coach"),
        (str(ROOT / "voice"), "voice"),                       # the coach's voice (Kokoro)
    ] + [d for v in VOICE for d in v[0]],
    binaries=[b for v in VOICE for b in v[1]],
    hiddenimports=["pystray._win32", "coach.service", "coach.drills", "coach.puzzles", "coach.insights",
                   "coach.settings", "keyring.backends.Windows", "webview.platforms.edgechromium",
                   "coach.voice"] + [h for v in VOICE for h in v[2]],
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
