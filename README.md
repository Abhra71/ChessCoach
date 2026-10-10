# Knightwise

<img src="installer/msix/Assets/Square150x150Logo.scale-200.png" width="96" alt="Knightwise logo">

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
| Browser extension: key moments of your finished games with labelled arrows (Better / You played / Reply) on the chess.com board; guided set-up with pictures and copy buttons | works (beta) |
| Lichess puzzles matched to your habits, mixed into the practice page (new set every day) | works |
| Practice remembers you: missed positions come back the next day, right ones after 3, 7, 21, 60 days | works |
| "Is this you?" answer on the review page, saved in your logbook | works |
| Welcome screen: a photorealistic 3D antique chess set (Poly Haven, CC0) replaying the Opera Game behind the card, offline | works |
| Desktop app window: Home (your focus, score, trend, last game), Games, Practice, Settings; dark and light | works (beta) |
| Settings: chess.com account, theme, voice, two optional AI key slots kept in Windows Credential Manager | works (AI use: next) |
| The coach speaks (Kokoro, on this computer): briefing, key moments, practice feedback; 4 voices | works |
| AI explanations and "Ask the coach" with your own key (Gemini, Groq, Claude or OpenAI), grounded in engine facts | works (beta) |
| Play the Coach: a game against the engine at your level (10 levels, about 300 to 2200); the coach warns about loose pieces, pauses after a blunder (take back or play on), hints in two steps, all spoken | works (beta) |
| Ask the coach by voice: Talk button, Whisper on this computer (one-time 485 MB download in Settings) | works (beta) |
| Windows installer: Next, Next, Finish; icon by the clock; welcome page asks your chess.com name | works (beta, not yet published) |
| Microsoft Store package (MSIX, signed by Microsoft on upload, so Windows never blocks it): starts with Windows, notifications, extension copied to Documents\Knightwise | built, not yet submitted |

## For players: install

1. Get **Knightwise** from the Microsoft Store (coming soon: the first release goes to a small private group of
   testers). Click **Get**: no installer, no Python, no admin rights, and Windows doesn't block it, because the Store
   signs it.
3. A welcome page opens: type your chess.com username. The coach checks your games (about 2 minutes the first
   time) and shows your review. From then on it lives as a knight icon by the clock and checks each new game
   by itself.
4. Optional, 1 minute: **Arrows on chess.com** (in the icon's menu) walks you through adding the browser
   extension and turns green when it works.

Your data stays on your computer in `%LOCALAPPDATA%\ChessCoach`. Uninstall from Windows Settings like any app.
Privacy: [PRIVACY.md](PRIVACY.md). Knightwise is independent and not connected with chess.com.

## For developers: run from source (Windows, Python 3.12)

```
pip install -r requirements.txt
python -m coach.get_engine                       # downloads Stockfish (~80 MB) into engine/
python -m coach.get_voice                        # optional: speaking (~120 MB) and listening (~485 MB) into voice/
python -m coach.get_assets                       # the 3D welcome scene (~20 MB) into coach/ui/vendor/
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

**Why no hints in chess.com bot games?** chess.com's fair-play rules forbid any tool that analyses positions during
play, with no exception for bot games. So live help happens only in **Play the Coach**, inside this app.

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
| `coach/app.py` | ChessCoach.exe: the app window (pywebview + WebView2), icon by the clock, the background coach |
| `coach/paths.py` | where files live (project folder, or %LOCALAPPDATA%\ChessCoach when installed) |
| `coach/ui/` | the desktop app's screens (one page: Home, Games, Practice, Play, Settings, Welcome) |
| `coach/ui/backdrop.js`, `coach/get_assets.py` | the 3D welcome scene (Three.js + Poly Haven chess set) and its download |
| `coach/insights.py` | the numbers and lists the app shows (dashboard, games, one game in detail) |
| `coach/voice.py`, `coach/hearing.py`, `coach/get_voice.py` | speaking (Kokoro), listening (Whisper), and their downloads |
| `coach/ai.py` | optional AI explanations and answers through the player's own keys (key 1, then key 2) |
| `coach/facts.py` | hard facts about a position or moment (loose pieces, what a move does, engine lines) the AI must stick to |
| `coach/live_engine.py` | one Stockfish kept open for live questions and games |
| `coach/play.py` | Play the Coach: the weakened opponent, live warnings, blunder check, hints |
| `coach/settings.py` | theme, voice and the two AI key slots (keys in Windows Credential Manager, never in files) |
| `installer/` | how the installer is built (PyInstaller recipe, Inno Setup script, icon) |
| `installer/msix/`, `installer/make_msix.py`, `installer/make_icons.py` | the Microsoft Store package: manifest (identity from Partner Center), icons, Store listing text |
| `PRIVACY.md` | the privacy policy linked from the Store |
| `tests/` | `python -m pytest -q tests` |

### Build the installer

```
pip install pyinstaller -r requirements.txt
python -m coach.get_engine
python -m coach.get_voice
python -m coach.get_assets
python -m PyInstaller installer/ChessCoach.spec --noconfirm
"%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" installer\ChessCoach.iss     # Inno Setup 6, free
```

Result: `dist\ChessCoach-Setup-<version>.exe` (about 245 MB: Stockfish, the voice and the speech libraries).

### Build the Microsoft Store package

After the PyInstaller step above, with Microsoft's free Windows SDK Build Tools (nuget.org package
`Microsoft.Windows.SDK.BuildTools`) unpacked in `build\sdktools`:

```
python installer/make_icons.py      # only when the logo changes (needs Microsoft Edge)
python installer/make_msix.py
```

Result: `dist\Knightwise-<version>.msix` (about 316 MB), uploaded in Partner Center, which signs it.
The Store page text is in `installer/msix/STORE_LISTING.md`.

Your games, results and logbooks stay on your computer in `data/` and `logbook/`. They are never uploaded
and never committed.

## Plan

Stockfish, Lichess opening explorer, endgame tablebases and puzzle database, the chess.com public API,
a browser extension that draws arrows on the chess.com board, Whisper (listening) and Kokoro (speaking),
a small tray window with your logbook, and a local SQLite memory.

## Licence

GPL-3.0 (see `LICENSE`). Stockfish and python-chess are also GPL-3.0. The voice is Kokoro (Apache-2.0); listening is Whisper via faster-whisper (MIT). The Lichess puzzle database is
public domain (CC0), from database.lichess.org. The 3D chess set is "Chess Set" by Riley Queen on Poly Haven (CC0);
Three.js is MIT.
