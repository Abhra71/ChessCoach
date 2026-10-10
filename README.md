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
| Review page: your top 3 patterns on real boards from your own games, in plain words | works |
| Practice page: positions from your own games, click your move, it says right or why not | works |
| Only new games are downloaded and checked (so it can later run by itself) | works |
| Runs by itself in the background after each game | planned |
| After-game review with arrows on the chess.com board (browser extension) | planned |
| Practice that repeats over days until it sticks, plus matched Lichess puzzles | planned |
| Voice (talk to the coach) | planned |
| Windows installer and public beta | planned |

## Try it now (Windows, Python 3.12)

```
pip install -r requirements.txt
python -m coach.get_engine                       # downloads Stockfish (~80 MB) into engine/
python -m coach.update <your chess.com username>
```

`update` downloads your games, checks every move you made with Stockfish (about 2 minutes for 150 games on
8 cores, the first time) and writes two pages to open in your browser: **`data/review.html`** and
**`data/drills.html`**. Run `python -m coach.update`
again after you play: it only downloads and checks the new games.

The review page starts with your score to bring down, **pieces given away per game** (all games, and your
last 20), then shows your top 3 mistake patterns, how often each happened, the habit that fixes it, and
3 real positions from your games for each: your move (red), what they could do next (orange), the better
move (green), with a link to the game on chess.com.

The practice page gives 12 other positions from your games, the move before a big mistake. Click a piece,
then a square. A safe move gets a yes; a bad one gets the reason ("then their bishop takes your queen on g7").
Every legal move was scored by Stockfish when the page was built, so the page needs no internet or engine.

`python -m coach.patterns` prints the full count in the terminal, for example (a ~300-rated player, 140 games):

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
| `coach/analyze.py` | checks every move of games not checked yet, writes `data/moves.jsonl` |
| `coach/patterns.py` | sorts big mistakes into patterns |
| `coach/review.py` | builds `data/review.html` (top patterns on real boards) |
| `coach/drills.py`, `coach/drills_template.html` | builds `data/drills.html` (practice on your own positions) |
| `coach/update.py` | one step: new games -> check -> review and practice pages |
| `tests/` | `python -m pytest -q tests` |

Your games, results and logbooks stay on your computer in `data/` and `logbook/`. They are never uploaded
and never committed.

## Plan

Stockfish, Lichess opening explorer, endgame tablebases and puzzle database, the chess.com public API,
a browser extension that draws arrows on the chess.com board, Whisper (listening) and Kokoro (speaking),
a small tray window with your logbook, and a local SQLite memory.

## Licence

GPL-3.0 (see `LICENSE`). Stockfish and python-chess are also GPL-3.0.
