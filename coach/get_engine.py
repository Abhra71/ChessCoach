"""Download the latest official Stockfish (GPL-3) for Windows into engine/.

Run:  python -m coach.get_engine
Source: github.com/official-stockfish/Stockfish/releases (about 80 MB)
"""
import io
import json
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSET = "stockfish-windows-x86-64-universal.zip"


def main():
    req = urllib.request.Request("https://api.github.com/repos/official-stockfish/Stockfish/releases/latest",
                                 headers={"User-Agent": "ChessCoach"})
    release = json.load(urllib.request.urlopen(req, timeout=30))
    url = next(a["browser_download_url"] for a in release["assets"] if a["name"] == ASSET)
    print(f"downloading Stockfish {release['tag_name']} ...")
    data = urllib.request.urlopen(url, timeout=300).read()
    zipfile.ZipFile(io.BytesIO(data)).extractall(ROOT / "engine")
    print(f"installed in {ROOT / 'engine'}")


if __name__ == "__main__":
    main()
