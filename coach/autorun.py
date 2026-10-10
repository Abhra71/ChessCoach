"""Start the coach quietly with Windows (a shortcut in your Startup folder; no admin rights, easy to remove).

Run:  python -m coach.autorun install     (also starts it now)
      python -m coach.autorun remove
      python -m coach.autorun status
"""
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STARTUP = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
SHORTCUT = STARTUP / "Chess Coach.lnk"


def pythonw():
    exe = Path(sys.executable)
    quiet = exe.with_name("pythonw.exe")
    return quiet if quiet.exists() else exe


def running():
    try:
        urllib.request.urlopen("http://127.0.0.1:8765/api/status", timeout=2)
        return True
    except OSError:
        return False


def install():
    ps = ("$s=(New-Object -ComObject WScript.Shell).CreateShortcut($env:LNK);"
          "$s.TargetPath=$env:EXE;$s.Arguments='-m coach.service';$s.WorkingDirectory=$env:DIR;"
          "$s.Description='Chess Coach: checks your new chess.com games';$s.WindowStyle=7;$s.Save()")
    env = {**os.environ, "LNK": str(SHORTCUT), "EXE": str(pythonw()), "DIR": str(ROOT)}
    subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps], env=env, check=True)
    if not running():
        subprocess.Popen([str(pythonw()), "-m", "coach.service"], cwd=ROOT,
                         creationflags=getattr(subprocess, "DETACHED_PROCESS", 0))
    print(f"installed: starts with Windows ({SHORTCUT}) and is running now")


def remove():
    SHORTCUT.unlink(missing_ok=True)
    print("removed from Startup. (If it is running now, it stops when you log off or restart.)")


def status():
    print(f"starts with Windows: {'yes' if SHORTCUT.exists() else 'no'}")
    print(f"running now: {'yes' if running() else 'no'}")


if __name__ == "__main__":
    {"install": install, "remove": remove, "status": status}.get(
        sys.argv[1] if len(sys.argv) > 1 else "", lambda: sys.exit(__doc__))()
