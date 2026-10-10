"""Download all finished games of a chess.com player (public API, no login needed).

Run:  python -m coach.fetch <chess.com username>
Output: data/games-YYYY-MM.json, data/player.txt
"""
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
HEADERS = {"User-Agent": "ChessCoach (open-source chess coach; github.com/Abhra71/ChessCoach)"}


def get_json(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=30) as resp:
        return json.load(resp)


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: python -m coach.fetch <chess.com username>")
    user = sys.argv[1].lower()
    DATA.mkdir(exist_ok=True)
    archives = get_json(f"https://api.chess.com/pub/player/{user}/games/archives")["archives"]
    total = 0
    for url in archives:
        year, month = url.rstrip("/").split("/")[-2:]
        games = get_json(url)
        (DATA / f"games-{year}-{month}.json").write_text(json.dumps(games))
        total += len(games["games"])
        print(f"{year}-{month}: {len(games['games'])} games")
    (DATA / "player.txt").write_text(user)
    print(f"{total} games saved in {DATA}")


if __name__ == "__main__":
    main()
