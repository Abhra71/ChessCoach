"""Download the engines into engine/: the latest official Stockfish (GPL-3) and, for the human-move model, Leela
(lc0, GPL-3, CPU build) with the nine Maia networks (CSSLab, GPL-3).

Run:  python -m coach.get_engine
Sources: github.com/official-stockfish/Stockfish/releases (about 80 MB), github.com/LeelaChessZero/lc0/releases
(v0.32.1, 24 MB; its own bundled network is removed, only Maia is used), github.com/CSSLab/maia-chess/releases
(v1.0, nine files of about 1.3 MB)
"""
import io
import json
import urllib.request
import zipfile

from coach.paths import PROJECT

ASSET = "stockfish-windows-x86-64-universal.zip"
LC0 = "https://github.com/LeelaChessZero/lc0/releases/download/v0.32.1/lc0-v0.32.1-windows-cpu-openblas.zip"
MAIA = "https://github.com/CSSLab/maia-chess/releases/download/v1.0/maia-{}.pb.gz"


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
    from coach import maia
    print("downloading Leela and Maia ...")
    lc0 = PROJECT / "engine" / "lc0"
    zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(LC0, timeout=300).read())).extractall(lc0)
    for net in lc0.glob("*.pb.gz"):  # Leela's own network: not used, Maia replaces it
        net.unlink()
    nets = PROJECT / "engine" / "maia"
    nets.mkdir(parents=True, exist_ok=True)
    for r in maia.RATINGS:
        (nets / f"maia-{r}.pb.gz").write_bytes(urllib.request.urlopen(MAIA.format(r), timeout=120).read())
    print(f"installed in {lc0} and {nets}")


if __name__ == "__main__":
    main()
