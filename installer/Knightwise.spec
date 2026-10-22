# PyInstaller recipe for Knightwise.exe (a folder app: faster start than one big file).
# Build:  python -m PyInstaller installer/Knightwise.spec --noconfirm   (needs engine/ from python -m coach.get_engine)
from pathlib import Path

from PyInstaller.utils.hooks import collect_all

ROOT = Path(SPECPATH).parent
VOICE = [collect_all(m) for m in ("kokoro_onnx", "espeakng_loader", "phonemizer", "language_tags", "segments",
                                  "faster_whisper", "ctranslate2", "tokenizers")]

a = Analysis(
    [str(ROOT / "coach" / "app.py")],
    pathex=[str(ROOT)],
    datas=[
        (str(ROOT / "engine"), "engine"),                     # Stockfish
        (str(ROOT / "extension"), "extension"),               # icon for the tray
        (str(ROOT / "coach" / "drills_template.html"), "coach"),
    ] + ([(str(ROOT / "coach" / "feedback.key"), "coach")] if (ROOT / "coach" / "feedback.key").exists() else []) + [  # one-click feedback
        (str(ROOT / "coach" / "ui"), "coach/ui"),             # the desktop app's screens
        (str(ROOT / "coach" / "library"), "coach/library"),   # strong players' games by pawn structure (CC0)
        (str(ROOT / "coach" / "openings"), "coach/openings"),  # the opening catalogue (Lichess, CC0)
        (str(ROOT / "voice" / "kokoro-v1.0.int8.onnx"), "voice"),  # the coach's voice (Kokoro); listening downloads later
        (str(ROOT / "voice" / "voices-v1.0.bin"), "voice"),
    ] + [d for v in VOICE for d in v[0]],
    binaries=[b for v in VOICE for b in v[1]],
    hiddenimports=["pystray._win32", "coach.service", "coach.drills", "coach.puzzles", "coach.insights",
                   "coach.settings", "keyring.backends.Windows", "webview.platforms.edgechromium",
                   "coach.voice", "coach.hearing", "coach.get_voice", "coach.ai", "coach.facts", "coach.live_engine", "anthropic",
                   "coach.daily", "coach.progress", "coach.tree", "coach.brief", "coach.plan", "coach.openings", "coach.coaches",
                   "coach.why", "coach.course", "coach.maia", "coach.spar", "coach.elite"] + [h for v in VOICE for h in v[2]],
    excludes=["tkinter", "pytest"],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="Knightwise",
    icon=str(ROOT / "installer" / "Knightwise.ico"),
    console=False,  # no black window
)
coll = COLLECT(exe, a.binaries, a.datas, name="Knightwise")
