"""Download the engines into engine/: the latest official Stockfish (GPL-3) and the human-move model, Maia-3.

Run:  python -m coach.get_engine
Sources: github.com/official-stockfish/Stockfish/releases (about 80 MB), and Maia-3 5M from Hugging Face
(UofTCSSLab/Maia3-5M, 21 MB, AGPL-3.0), turned into engine/maia3/maia3-5m.npz by installer/make_maia3.py.
Until 20 Oct 2026 the human-move model was Maia 1 run by Leela (lc0): no longer used or downloaded.
"""
import io
import json
import urllib.request
import zipfile

from coach.paths import PROJECT

ASSET = "stockfish-windows-x86-64-universal.zip"


def main():
    req = urllib.request.Request("https://api.github.com/repos/official-stockfish/Stockfish/releases/latest",
                                 headers={"User-Agent": "Knightwise"})
    release = json.load(urllib.request.urlopen(req, timeout=30))
    url = next(a["browser_download_url"] for a in release["assets"] if a["name"] == ASSET)
    print(f"downloading Stockfish {release['tag_name']} ...")
    data = urllib.request.urlopen(url, timeout=300).read()
    zipfile.ZipFile(io.BytesIO(data)).extractall(PROJECT / "engine")
    print(f"installed in {PROJECT / 'engine'}")
    human_moves()


def human_moves():
    import importlib.util
    print("downloading Maia-3 (21 MB) ...")
    spec = importlib.util.spec_from_file_location("make_maia3", PROJECT / "installer" / "make_maia3.py")
    make = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(make)
    make.main()


if __name__ == "__main__":
    main()
