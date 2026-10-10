"""One step: download new games, check them with Stockfish, rebuild the review and practice pages.

Run:  python -m coach.update [chess.com username]   (username only needed the first time)
"""
import sys

from coach import analyze, drills, fetch, review
from coach.paths import DATA



def main():
    player_file = DATA / "player.txt"
    if len(sys.argv) > 1:
        user = sys.argv[1].lower()
    elif player_file.exists():
        user = player_file.read_text().strip()
    else:
        sys.exit("first time: python -m coach.update <chess.com username>")
    print(f"{fetch.fetch(user)} new games from chess.com for {user}")
    analyze.main(argv=[])
    print(f"review page: {review.build()}")
    page, n = drills.build()
    print(f"practice page ({n} positions): {page}")


if __name__ == "__main__":
    main()
