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
| Runs by itself in the background: checks new games every 10 minutes, Windows notification | works |
| Browser extension: key moments of your finished games with arrows on the chess.com board | works (beta) |
| Lichess puzzles matched to your habits, mixed into the practice page (new set every day) | works |
| Practice remembers you: missed positions come back the next day, right ones after 3, 7, 21, 60 days | works |
| "Is this you?" answer on the review page, saved in your logbook | works |
| Voice (talk to the coach) | planned |
| Windows installer and public beta | planned |

## Try it now (Windows, Python 3.12)

```
pip install -r requirements.txt
python -m coach.get_engine                       # downloads Stockfish (~80 MB) into engine/
python -m coach.puzzles                          # optional: Lichess puzzles (reads ~300 MB, keeps ~2.5 MB)
python -m coach.update <your chess.com username>
```

`update` downloads your games, checks every move you made with Stockfish (about 2 minutes for 150 games on
8 cores, the first time) and writes two pages to open in your browser: **`data/review.html`** and
**`data/drills.html`**. Run `python -m coach.update`
again after you play: it only downloads and checks the new games.

The review page starts with **your last game** (result, pieces given away, its key moments on boards: this is
what the notification opens), then your score to bring down, **pieces given away per game** (all games, and your
last 20), then shows your top 3 mistake patterns, how often each happened, the habit that fixes it, and
3 real positions from your games for each: your move (red), what they could do next (orange), the better
move (green), with a link to the game on chess.com.

The practice page gives 12 other positions from your games, the move before a big mistake, mixed with 12
Lichess puzzles on the same habits (hanging pieces, forks, mate in 1 and 2; rated 400-1200; a new set every day).
Click a piece, then a square. In your own positions a safe move gets a yes and a bad one gets the reason
("then their bishop takes your queen on g7"); every legal move was scored by Stockfish when the page was built,
so the page needs no internet or engine. Opened through the coach (http://127.0.0.1:8765/practice) it keeps
your answers: a position you miss comes back the next day, one you get right comes back after longer and longer
gaps (1, 3, 7, 21, 60 days) until it sticks. In puzzles you see their last move (orange), then find yours; longer
puzzles answer and wait for your next move.

### Let it run by itself

```
python -m coach.autorun install      # starts with Windows, and starts now
python -m coach.autorun status
python -m coach.autorun remove       # stops it and removes it from Windows startup
```

It runs quietly in the background (no window). Every 10 minutes it looks for new finished games on chess.com,
checks them, rebuilds both pages and shows a Windows notification. Your pages are then at
**http://127.0.0.1:8765/** (review) and **http://127.0.0.1:8765/practice** (this computer only).
Its own log is `logbook/service.log`.

### Arrows on chess.com (browser extension, beta)

1. Keep the coach running (`python -m coach.autorun install`, or `python -m coach.service` in a terminal).
2. In Chrome go to `chrome://extensions` (Edge: `edge://extensions`), switch on **Developer mode**, click
   **Load unpacked** and choose the `extension` folder of this project.
3. Open one of your finished games on chess.com (`chess.com/game/live/...`). A small **Chess Coach** panel
   lists the key moments. Click one: the board jumps there and shows the better move (green) and your move
   (red). "What happened next" shows your move and their answer (orange). The – button shrinks the panel.
4. The Chess Coach button in the browser toolbar says whether the coach is running and links to your review
   and practice pages.

**Fair play:** the extension only shows something for games the coach already knows, and the coach only knows
games that chess.com has archived as finished. During a live game it shows nothing at all. It never moves pieces
and never sends anything to chess.com; it only talks to the coach on your own computer.

`python -m coach.patterns` prints the full count in the terminal, for example (a ~300-rated player, 140 games):

```
124 x left a piece hanging         in  73 games  (under 30s on clock: 16)
 35 x walked into a fork or trick  in  28 games  (under 30s on clock: 0)
 31 x missed a free capture        in  24 games  (under 30s on clock: 2)
```

## How it works

- **Stockfish** (the strongest chess engine) scores the position before and after each of your moves.
- The score is turned into a **winning chance** (0-100). A move that drops it by 25 or more is a big mistake.
- Each big mistake is sorted by **what happened next** in the engine's line: you lost a piece straight away
  (hanging: counted after your best reply, so a piece you can take back is not hanging), a couple of moves later
  (fork or trick), you missed a whole piece that was free (a knight, bishop, rook or queen; pawn grabs don't count),
  missed a mate, or walked into one. Everything else is "other" (deeper tactics, slow threats).

## Files

| Path | What |
|---|---|
| `coach/fetch.py` | downloads games from the chess.com public API (no login) |
| `coach/get_engine.py` | downloads the official Stockfish release |
| `coach/analyze.py` | checks every move of games not checked yet, writes `data/moves.jsonl` |
| `coach/patterns.py` | sorts big mistakes into patterns |
| `coach/review.py` | builds `data/review.html` (top patterns on real boards) |
| `coach/drills.py`, `coach/drills_template.html` | builds `data/drills.html` (your positions + matched puzzles) |
| `coach/puzzles.py` | downloads the Lichess puzzle database (CC0) and keeps the themes the coach uses |
| `coach/update.py` | one step: new games -> check -> review and practice pages |
| `coach/service.py` | background helper: update every 10 min, notification, local server for pages and the extension |
| `coach/autorun.py` | start the helper with Windows (Startup folder shortcut) or remove it |
| `coach/memory.py` | practice answers and spacing (which positions come back when), your "is this you?" answers |
| `extension/` | the Chrome/Edge extension (arrows and key-moments panel on chess.com) |
| `tests/` | `python -m pytest -q tests` |

Your games, results and logbooks stay on your computer in `data/` and `logbook/`. They are never uploaded
and never committed.

## Plan

Stockfish, Lichess opening explorer, endgame tablebases and puzzle database, the chess.com public API,
a browser extension that draws arrows on the chess.com board, Whisper (listening) and Kokoro (speaking),
a small tray window with your logbook, and a local SQLite memory.

## Licence

GPL-3.0 (see `LICENSE`). Stockfish and python-chess are also GPL-3.0. The Lichess puzzle database is
public domain (CC0), from database.lichess.org.
