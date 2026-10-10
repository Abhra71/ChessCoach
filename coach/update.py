"""One step: download new games, check them with Stockfish, rebuild the review page.

Run:  python -m coach.update [chess.com username]   (username only needed the first time)
"""
import sys
from pathlib import Path

from coach import analyze, fetch, review

ROOT = Path(__file__).resolve().parent.parent


def main():
    player_file = ROOT / "data" / "player.txt"
    if len(sys.argv) > 1:
        user = sys.argv[1].lower()
    elif player_file.exists():
        user = player_file.read_text().strip()
    else:
        sys.exit("first time: python -m coach.update <chess.com username>")
    print(f"{fetch.fetch(user)} new games from chess.com for {user}")
    sys.argv = sys.argv[:1]
    analyze.main()
    print(f"review page: {review.build()}")


if __name__ == "__main__":
    main()
