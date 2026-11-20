# Contributing to Knightwise

Thanks for wanting to help! Knightwise is a free, open-source chess coach made by one teenager, and every bit of
help counts, from a two-minute bug report to code.

## No code needed

- **Report a bug** or **suggest an idea** with the short forms in [Issues](https://github.com/Abhra71/ChessCoach/issues/new/choose).
- **Ask, share, discuss** in [Discussions](https://github.com/Abhra71/ChessCoach/discussions): your progress, a
  confusing screen, a habit you'd like the coaches to notice.
- **Languages (planned):** the coaches only speak English today. If you'd like Maya and Viktor in your language,
  say so in Discussions: knowing which languages people want decides what comes first.
- **Tell a chess friend**, or leave an honest rating on the
  [Microsoft Store page](https://www.microsoft.com/store/apps/9NKLGS6K72J2?cid=github).

## Running it from the code (Windows)

```
pip install -r requirements.txt
python -m coach.get_engine      # Stockfish 19 and the human-move model (about 100 MB)
python -m coach.get_voice       # the coaches' voices (optional)
try.bat test                    # a test copy with its own data, separate from the Store app
```

Run the tests before sending a change:

```
python -m pytest -q
```

They also run on GitHub for every push, with the same Stockfish 19 as the app.

## The rules every change keeps

1. **Fair play.** Nothing may help during a game against a real person: no hints, no arrows, no reading the board.
   The browser extension stays off on any live-game page. A change that weakens this can't be merged.
2. **The engine decides, the AI explains.** Moves and verdicts come from Stockfish; the AI only puts the engine's
   facts into words, and is never allowed to invent moves.
3. **Understanding speech and typing is the AI's job,** not sentence patterns or regular expressions.
4. **Players' data stays on their PC.** No accounts, no tracking, and never a key or a player's file in the repo.
5. **Plain words.** Short sentences a beginner understands, in British spelling.
6. **Calm look.** Warm greys, one green button per screen, pictures and numbers before sentences.

## Where things are

| | |
|---|---|
| `coach/` | the app: checking games, practice, the coaches, the local server |
| `coach/ui/` | the desktop app's pages |
| `extension/` | the Chrome/Edge extension (the coach on chess.com) |
| `tests/` | the tests |
| `docs/MAINTAINING.md` | how everything works and how to release |

Questions? Open a Discussion: there are no silly ones.
