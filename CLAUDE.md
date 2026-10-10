# Chess Coach: the user's standing instructions (read before anything else)

## What it is
An elite chess coach that "sits behind you" on chess.com: it knows how you play, finds your mistakes, shows
better moves with arrows on the chess.com board itself, picks what to learn next, and talks by voice.
For everyone from day one, tuned to each player's level. (Replaces Jarvis, archived 10 Oct 2026:
github.com/Abhra71/Jarvis; keys, Whisper models and data kept in `C:\Syntax_Assembler\jarvis-keep`.)

## Hard line: fair play
Completely off during any game against a real person: no hints, no arrows, no reading the board.
Fully on everywhere else (game review, analysis, puzzles, lessons, before/after games).

## Decisions
- 10 Oct: **open-source** (GPL-compatible), so Stockfish + python-chess are fine. User data and keys never in the repo.
- Planned stack (agreed in principle, install one piece at a time after asking): Stockfish 17, python-chess,
  Lichess opening explorer + tablebases + puzzle DB, chess.com public API, browser extension for arrows,
  Whisper (from jarvis-keep) for hearing, Kokoro for speaking, tray logbook window, SQLite memory.
- First step: Stockfish + python-chess -> the user's top 3 mistake patterns from their 142 games
  (already downloaded in `data/`). First look: 4 won games stalemated, 35 of 63 losses by checkmate, 14 on time.

## How to work
- **Elite, not cosmetic.** The best available engine, data and models, proven on the user's real games.
- **Curated, not noisy.** Only the one or two things that matter for this player now, at their level.
- **Measure on real data:** the user's own games (chess.com user `gushynanda`) and their verdict
  ("is this me?"). Never report a score from tests you wrote as progress.
- **Discuss before installing or downloading anything:** what it is, why, source, size, licence.
- **The user works by voice and reads plain language.** Say what you're doing, why, what you found, including
  bad news and mistakes, with numbers. No jargon walls. Say before you take over the screen.
- **Two logbooks:** the user's chess-themed one (games, mistakes, progress), and a debug log for Claude
  (what went wrong, smart storage budget, no passwords).
- **No sentence patterns / regexes for understanding speech.** Fix understanding properly.
- **AI is used where it adds value; the engine and code do the rest** (cheap and fast for everyone).
- Commit and push after each working piece, only when the tests pass.
- End every reply with: `Coach: ~N% · Feel: ~N%` (feel = from the user's own use, not tests).
- The user can't sit to approve prompts: use simple, pre-approved command shapes.
