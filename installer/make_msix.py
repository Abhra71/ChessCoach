"""Builds the Microsoft Store package: dist/Knightwise-<version>.msix (the Store signs it on upload).

Run, after PyInstaller has built dist/ChessCoach:
    python installer/make_msix.py
Needs Microsoft's Windows SDK Build Tools (makeappx, makepri) unpacked in build/sdktools
(nuget.org package Microsoft.Windows.SDK.BuildTools).
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APPDIR = ROOT / "dist" / "ChessCoach"
MSIX = ROOT / "installer" / "msix"
STAGE = ROOT / "build" / "msix-stage"
TOOLS = next((ROOT / "build" / "sdktools" / "pkg" / "bin").glob("*/x64"), None)


def run(*args):
    result = subprocess.run([str(a) for a in args], capture_output=True, text=True)
    if result.returncode:
        sys.exit(f"{Path(args[0]).name} failed:\n{result.stdout[-3000:]}\n{result.stderr[-2000:]}")
    return result.stdout


def main():
    if TOOLS is None:
        sys.exit("Windows SDK Build Tools not found in build/sdktools")
    if not (APPDIR / "ChessCoach.exe").exists():
        sys.exit("Build the app first: python -m PyInstaller installer/ChessCoach.spec")
    manifest = (MSIX / "AppxManifest.xml").read_text(encoding="utf-8")
    version = re.search(r'<Identity[^>]*Version="([\d.]+)"', manifest).group(1)

    shutil.rmtree(STAGE, ignore_errors=True)
    shutil.copytree(APPDIR, STAGE)
    shutil.copytree(MSIX / "Assets", STAGE / "Assets")
    shutil.copy(MSIX / "AppxManifest.xml", STAGE / "AppxManifest.xml")

    # resources.pri: lets Windows pick the sharpest icon for each screen and the taskbar
    config = ROOT / "build" / "priconfig.xml"
    run(TOOLS / "makepri.exe", "createconfig", "/cf", config, "/dq", "en-US", "/o")
    run(TOOLS / "makepri.exe", "new", "/pr", STAGE, "/cf", config, "/mn", STAGE / "AppxManifest.xml",
        "/of", STAGE / "resources.pri", "/o")

    out = ROOT / "dist" / f"Knightwise-{version}.msix"
    run(TOOLS / "makeappx.exe", "pack", "/d", STAGE, "/p", out, "/o")
    print(f"{out}  ({out.stat().st_size / 1e6:.0f} MB)")


if __name__ == "__main__":
    main()
