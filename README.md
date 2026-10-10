# Chess Coach

A free, open-source chess coach that learns how **you** play on chess.com, finds the habits that lose you
games, and trains you out of them, one or two things at a time, at your level.

> **Fair play:** the coach is completely off during any game against a real person. No hints, no arrows,
> no reading the board. It only works on finished games, analysis, puzzles and lessons.

## Status: early (not ready for players yet)

| Piece | State |
|---|---|
| Download a player's games from chess.com | works |
| Check every move with Stockfish and find the big mistakes | works |
| Sort mistakes into patterns (hanging pieces, missed captures, forks, missed mates, stalemated wins) | works |
| After-game review with arrows on the chess.com board (browser extension) | planned |
| Drills built from your own mistakes, matched puzzles | planned |
| Voice (talk to the coach) | planned |
| Windows installer and public beta | planned |

## Try it now (Windows, Python 3.12)

```
pip install -r requirements.txt
python -m coach.get_engine                # downloads Stockfish (~80 MB) into engine/
python -m coach.fetch <your chess.com username>
python -m coach.analyze                   # checks every move you made; ~10 min for 150 games on 8 cores
python -m coach.patterns                  # prints your mistake patterns
```

Example output (a ~300-rated player, 140 games):

```
150 x left a piece hanging         in  82 games  (under 30s on clock: 16)
 51 x missed a free capture        in  33 games  (under 30s on clock: 3)
 25 x walked into a fork or trick  in  21 games  (under 30s on clock: 0)
```

## How it works

- **Stockfish** (the strongest chess engine) scores the position before and after each of your moves.
- The score is turned into a **winning chance** (0-100). A move that drops it by 25 or more is a big mistake.
- Each big mistake is sorted by **what happened next** in the engine's line: you lost a piece straight away
  (hanging), a couple of moves later (fork or trick), you missed a free capture, missed a mate, or walked into one.

## Files

| Path | What |
|---|---|
| `coach/fetch.py` | downloads games from the chess.com public API (no login) |
| `coach/get_engine.py` | downloads the official Stockfish release |
| `coach/analyze.py` | checks every move, writes `data/moves.jsonl` |
| `coach/patterns.py` | sorts big mistakes into patterns |
| `tests/` | `python -m pytest -q tests` |

Your games, results and logbooks stay on your computer in `data/` and `logbook/`. They are never uploaded
and never committed.

## Plan

Stockfish, Lichess opening explorer, endgame tablebases and puzzle database, the chess.com public API,
a browser extension that draws arrows on the chess.com board, Whisper (listening) and Kokoro (speaking),
a small tray window with your logbook, and a local SQLite memory.

## Licence

GPL-3.0 (see `LICENSE`). Stockfish and python-chess are also GPL-3.0.
