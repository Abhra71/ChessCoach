"""Download all finished games of a chess.com player (public API, no login needed).

Run:  python -m coach.fetch <chess.com username>   (add --all to download every month again)
Output: data/games-YYYY-MM.json, data/player.txt
"""
import json
import sys
import urllib.error
import urllib.request

from coach import health
from coach.paths import DATA
HEADERS = {"User-Agent": "ChessCoach (open-source chess coach; github.com/Abhra71/ChessCoach)"}


def get_json(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=30) as resp:
        return json.load(resp)


def fetch(user, refresh_all=False):
    """Save the player's monthly game files. Only months not saved yet, plus the latest month, are downloaded.
    Returns the number of games that were not saved before."""
    DATA.mkdir(exist_ok=True)
    try:  # the self-check: chess.com's API still answers, in the shape Knightwise reads
        archives = get_json(f"https://api.chess.com/pub/player/{user}/games/archives")["archives"]
    except urllib.error.HTTPError as e:
        if e.code != 404:  # 404 is an unknown username, not a broken service
            health.record("api-archives", False, f"HTTP {e.code}")
        raise
    except urllib.error.URLError:  # no internet on this PC: not chess.com's fault, nothing to report
        raise
    except (ValueError, KeyError, TypeError) as e:  # an answer, but not in the shape Knightwise reads
        health.record("api-archives", False, type(e).__name__)
        raise
    health.record("api-archives", True)
    new = 0
    for i, url in enumerate(archives):
        year, month = url.rstrip("/").split("/")[-2:]
        path = DATA / f"games-{year}-{month}.json"
        latest = i == len(archives) - 1
        if path.exists() and not latest and not refresh_all:
            continue
        before = len(json.loads(path.read_text())["games"]) if path.exists() else 0
        games = get_json(url)
        missing = health.missing_fields(games)
        health.record("api-games", not missing, ", ".join(missing))
        if missing:  # keep the last good copy rather than save something Knightwise can't read
            continue
        path.write_text(json.dumps(games))
        new += len(games["games"]) - before
    (DATA / "player.txt").write_text(user)
    return new


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: python -m coach.fetch <chess.com username> [--all]")
    print(f"{fetch(sys.argv[1].lower(), '--all' in sys.argv)} new games saved in {DATA}")


if __name__ == "__main__":
    main()
