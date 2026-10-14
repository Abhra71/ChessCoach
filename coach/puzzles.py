"""Download the Lichess puzzle database (free, public domain / CC0) and keep only the puzzles the coach uses.

Run:  python -m coach.puzzles
Source: https://database.lichess.org/lichess_db_puzzle.csv.zst (~300 MB). It is unpacked while it downloads,
so only the kept puzzles are saved: data/puzzles.json (about 10 MB).
"""
import collections
import csv
import io
import json
import sys
import urllib.request

import zstandard

from coach.paths import DATA

OUT = DATA / "puzzles.json"
URL = "https://database.lichess.org/lichess_db_puzzle.csv.zst"

# Lichess puzzle theme for each mistake pattern
THEMES = {
    "left a piece hanging": "hangingPiece",
    "missed a free capture": "hangingPiece",
    "walked into a fork or trick": "fork",
    "walked into checkmate": "mateIn1",
    "missed a checkmate": "mateIn2",
}
# the grandmaster's library: every theme a beginner-to-club player needs, so the coaches can always bring something new
KEEP_THEMES = {"hangingPiece", "fork", "mateIn1", "mateIn2", "pin", "skewer", "discoveredAttack", "doubleCheck",
               "backRankMate", "smotheredMate", "trappedPiece", "deflection", "attraction", "capturingDefender",
               "promotion", "defensiveMove", "pawnEndgame", "rookEndgame", "queenEndgame", "opening",
               # 0.9, for 1,600 to 2,000+: deeper ideas, and the endings beyond rook and pawn
               "quietMove", "zugzwang", "intermezzo", "clearance", "interference", "xRayAttack", "exposedKing",
               "kingsideAttack", "advancedPawn", "bishopEndgame", "knightEndgame"}
# every level, spread evenly: up to PER_BAND puzzles of each theme in each 100-point band, from the easiest Lichess
# has (about 400) to the hardest (about 3,000+). Until 14 Oct only 400-1,600 was kept, with 69 puzzles in the 400s,
# so a 254 player got 1,400s. Real Lichess puzzles only, none made up.
BAND = 100
PER_BAND = 40
VERSION = 4  # bump when KEEP_THEMES or the spread changes: the app downloads again


def band(rating):
    return int(rating) // BAND * BAND


def wanted(row):
    """Clear, well-tested puzzles: a settled rating, liked and played often."""
    return int(row["RatingDeviation"]) <= 90 and int(row["Popularity"]) >= 80 and int(row["NbPlays"]) >= 300


def main():
    req = urllib.request.Request(URL, headers={"User-Agent": "ChessCoach (github.com/Abhra71/ChessCoach)"})
    kept = {t: [] for t in KEEP_THEMES}
    full = collections.Counter()  # (theme, band) -> puzzles kept
    seen = 0
    with urllib.request.urlopen(req, timeout=60) as resp:
        text = io.TextIOWrapper(zstandard.ZstdDecompressor().stream_reader(resp), encoding="utf-8")
        for row in csv.DictReader(text):  # the file is sorted by puzzle id, so themes and ratings come mixed
            seen += 1
            if seen % 200_000 == 0:
                print(f"\r{seen:,} puzzles read", end="", file=sys.stderr, flush=True)
            themes, b = set(row["Themes"].split()), band(row["Rating"])
            hit = sorted(t for t in themes & KEEP_THEMES if full[t, b] < PER_BAND)
            if not hit or not wanted(row):
                continue
            full[hit[0], b] += 1
            kept[hit[0]].append({"id": row["PuzzleId"], "fen": row["FEN"], "moves": row["Moves"].split(),
                                 "rating": int(row["Rating"]), "themes": sorted(themes)})
    OUT.parent.mkdir(exist_ok=True)  # a new install has no data/ folder yet
    OUT.write_text(json.dumps({**kept, "_version": VERSION}))
    print(f"\nread {seen:,} puzzles, kept " + ", ".join(f"{t}: {len(v)}" for t, v in kept.items()), file=sys.stderr)


if __name__ == "__main__":
    main()


def current():
    """Is the kept set up to date with KEEP_THEMES?"""
    try:
        return json.loads(OUT.read_text()).get("_version") == VERSION
    except (OSError, ValueError):
        return False
