# Knightwise on the phone: the plan

Written 27 Nov 2026 while the owner studies for exams (1-11 Dec). Nothing here is decided until the owner says so.
Section 7 lists the decisions waiting for you.

**Short version:** a first phone app already works (116 KB, no downloads): type your chess.com or Lichess
username, see your newest 60 finished games, replay any of them on a board. The next big step is the engine
(Stockfish built for the browser, 1.9 MB, GPL-3, needs your OK). A first real version (review, habits,
practice from your own mistakes) is about **3-4 weeks of work** after you approve it.

---

## 1. What the PC app does today (from `coach/`)

| Area | What it does | Main files |
|---|---|---|
| Your games | Downloads every finished chess.com game; Stockfish checks every move you played | `fetch.py`, `analyze.py` |
| Your habits | Sorts big mistakes into habits (hanging pieces, missed mates, forks, back rank...) and says *why* in words | `patterns.py`, `why.py`, `facts.py` |
| Home, Games, one game | Numbers, the list of games, a game with its key moments and arrows | `insights.py`, `narrate.py`, `ui/` |
| Practice | Positions from your own big mistakes; spaced repetition (Leitner boxes) | `drills.py`, `memory.py`, `daylock.py` |
| Today's 5 minutes | One own position, one puzzle, your opening, a gentle streak | `daily.py` |
| Rematch | Replay a game from the move where it went wrong | `rematch.py` |
| Level ladder, course | Five levels, 43 lessons picked by your games | `ladder.py`, `course.py`, `plan.py` |
| Openings | One opening that suits you, your repertoire, your opening tree | `openings.py`, `repertoire.py`, `tree.py` |
| Clock coach | Where your time went (chess.com records the clock on every move) | `clock.py` |
| Endgames | Six must-know endings against best defence | `endgames.py` |
| Calculation | Blindfold, see it in your head, guess the human move | `blindfold.py`, `guess.py` |
| Prep and spar | How a future opponent plays (their public games); spar against their openings | `prep.py`, `scout.py`, `spar.py`, `maia.py` |
| Progress | Week story, badges, report, Wrapped, a 3D film of your best game | `progress.py`, `report.py`, `film.py` |
| Coaches | Maya and Viktor: one line each, voice (Kokoro), hearing (Whisper), optional AI key | `coaches.py`, `voice.py`, `hearing.py`, `talk.py`, `ai.py`, `answers.py` |
| On chess.com | The extension: arrows on the finished-game page, the coach bubble | `extension/` |
| Looks after itself | Fix file, chess.com self-check, quiet updates | `fixes.py`, `health.py`, `updater.py` |

## 2. Why the phone needs its own version

The PC app is Python + a Stockfish program + local AI models (about 376 MB in the Store package). A phone
browser can't run any of that. What it **can** run:

- **JavaScript** (the language of web pages): the screens, the rules of chess, the habits logic.
- **WebAssembly** ("Wasm"): programs like Stockfish, rebuilt to run inside the browser at near-normal speed.
- **Built-in phone features**: storage, offline files, the phone's own speaking voice.

So the phone version is a **web app you can install** (a PWA) at `abhra71.github.io/ChessCoach/app`, the same way
as your Study Tracker. No server of ours: chess.com's and Lichess's public APIs let a browser read games directly
(checked 27 Oct and again today). Everything stays on the phone.

Two ways to bring the PC app's *thinking* (habits, the "why") to the phone:

| | A. Rewrite in JavaScript | B. Run the Python as it is (Pyodide) |
|---|---|---|
| What | Port the parts we need (`patterns.py`, the key parts of `why.py`) to JS | Pyodide runs real Python in the browser; python-chess works in it |
| Download | Small (tens of KB) | About 10 MB more on first open (to check) |
| Speed | Fast to open | 3-5 s slower to start on a phone (to measure) |
| Upkeep | Two copies of the logic to keep in step | One copy; the PC and phone agree by design |
| For your learning | Learn JS | You'd be working in the Python you're learning |

**My recommendation: A**, for a small, fast app; port only what v1 needs, and keep the PC's tests as the answer
key (same game in, same habit out).

## 3. What a phone can have, and how

| PC feature | On the phone? | How |
|---|---|---|
| Download your games | **Yes (done)** | chess.com archives + Lichess games export, newest 60 first |
| Replay a game | **Yes (done)** | own move rules (`docs/app/rules.js`), the PC's board drawing |
| Check every move | Yes, needs the engine | Stockfish.js lite (Wasm, 1.9 MB), in a background worker |
| Your habits + why | Yes | port the habit sorting and the top reasons to JS |
| Practice from your mistakes | Yes | same Leitner boxes, kept in the phone's storage |
| Today's 5 minutes, streak | Yes | small, no new data |
| Rematch from the mistake | Yes, after the engine | engine plays the other side |
| Level ladder, course | Later | big; the lessons text can be shared with the PC |
| Clock coach | Yes (chess.com) | the clock is in each game's record already |
| Puzzles on your habit | Later | needs a small puzzle pack (about 1-2 MB, to measure) |
| Openings, repertoire, tree | Later | the opening catalogue is 5 small files (CC0) |
| Endgames | Later | engine, or Lichess's tablebase API online |
| Prep and spar | Later, think first | public games only, never during a game (section 5) |
| Human-move model (Maia-3) | Later, maybe never | AGPL model + ONNX runtime: tens of MB (to measure) |
| Coach's voice | Yes, cheaply | the phone's built-in voice (free, no download); Kokoro is too big for a phone |
| Hearing | Later | the phone's speech typing, or a Groq key like the PC |
| 3D film, Wrapped | Later | the film scene (Three.js) is about 1.5 MB |
| Arrows on chess.com | No | phones don't run Chrome extensions; arrows show in our app instead |

## 4. First version (v1): proposal

1. **Your games** (chess.com and Lichess) - done in the skeleton.
2. **Review a game**: the engine checks your moves, the board shows the big mistakes with the same arrows and
   labels as the PC ("You played", "Better"), one line from Maya per mistake.
3. **Your habits**: the top 2-3 habits from your last 20-60 games, with numbers ("hung a piece in 9 of 20 games").
4. **Practice**: positions from your own mistakes, spaced repetition, a streak.
5. **One-line coach**, calm look, one green button per screen, works offline after the first download.

Not in v1: course, ladder, openings, prep, voice conversation, AI keys. They come one by one later.

**How the engine works on a phone (plan):** the PC checks at depth 14 on all cores. A phone runs one thread.
So: check only *your* moves, newest 20 games first, show results as each game finishes, check the rest while the
app is open (a web app can't work when closed). Speed on a real phone is **not measured yet**: this is the
first job once the engine is approved. Then compare the phone's verdicts with the PC's on your own 142 games, so
the phone and PC agree on what a blunder is (the same 25-point "winning chance" drop, `coach/patterns.py`).

## 5. Fair play on the phone (the hard line)

Your chess.com account was closed on 27 Nov for engine use on a phone. The phone app must make that **impossible
to do by accident**, and never tempting:

- **Only games the site has already archived as finished.** chess.com's monthly archives hold finished games only;
  Lichess's export is asked for finished games only (`ongoing=false`), and aborted or unstarted games are dropped
  (`docs/app/games.js`).
- **No free position analysis**: no board editor, no "paste a position", no photo or screenshot of a board, no
  "share to Knightwise" from other apps. The engine will only ever be given positions from those finished games
  (one place in the code does this, so it's easy to check).
- **Nothing during a live game**: no overlay over other apps, no notifications while you play, the app never
  reads another app or the chess.com page.
- **Prep stays as on the PC**: a future opponent's public, finished games only, never once the game has started.
- The footer says it on every screen: "Only finished games. Knightwise is off during every live game."

## 6. Storage, offline, size

- **On the phone only.** Username and games in `localStorage` today (fine for 60 games, about 0.3 MB). When the
  engine's checks come, move to **IndexedDB** (the phone browser's database, far more room) and ask the browser
  to keep it (`navigator.storage.persist`). Nothing is sent anywhere except the requests to chess.com/Lichess.
- **Offline:** the service worker (`docs/app/sw.js`) keeps the app's files; the last games list is kept, so the app
  opens and replays games with no internet. New games need the internet once.
- **iPhone note:** Safari may clear a website's storage after 7 days unused, but not for an app added to the Home
  Screen. The app should say "Add to Home Screen" on iPhone.
- **Size budget (first install):** app 0.12 MB now + engine 1.9 MB + data for one player about 1 MB =
  **under 5 MB** for v1 (the PC package is 376 MB). Any extra (puzzles, film, voice) is downloaded only when used.

## 7. Decisions waiting for the owner

1. **The engine** (needs your OK before anything is downloaded):

   | Option | Size | Strength | Licence | Source |
   |---|---|---|---|---|
   | **Stockfish.js 19 lite, single-threaded** (recommended) | **1.9 MB** | "far stronger than any human" (its README), weaker than full | GPL-3.0 | github.com/nmrugg/stockfish.js (npm `stockfish` 19.0.1; the build chess.com's own site uses) |
   | Stockfish.js 19 full, single-threaded | 99 MB | full strength | GPL-3.0 | same |
   | Stockfish.js 19 lite, multi-threaded | 1.7 MB | faster on many cores | GPL-3.0 | same; needs special web-server headers GitHub Pages can't send (a workaround exists) |
   | Stockfish.js 19 asm.js | 3.2 MB | slow and weak | GPL-3.0 | same; only for very old phones |

   Sizes checked today from the published package (27 Nov). The 99 MB file is also right at GitHub Pages' 100 MB
   per-file limit. GPL-3 is fine: Knightwise is already open-source under a GPL-compatible licence.
   We'd copy just the two lite files (`stockfish-19-lite-single.js` + `.wasm`) into `docs/app/engine/`, no npm.
2. **Rewrite in JS (A) or Pyodide (B)** for the habits logic (section 2). Recommendation: A.
3. **Exact v1 list** (section 4): keep, cut, or add (e.g. the clock coach is cheap to add).
4. **Order with Lichess 1.3 and the 2.0 hero feature**: ROADMAP (26 Nov) says 1.3 Lichess 12-26 Dec, 2.0 by
   10 Feb, then mobile; on 27 Nov you said mobile as fast as possible. Options: mobile v1 in January before 2.0,
   or mobile after 2.0. (The phone app already reads Lichess, which is half of 1.3's download work.)
5. **Look**: today's skeleton uses the PC's calm look (warm greys, one green button). For v1: a bottom tab bar
   (Games, Habits, Practice)? Maya's face on the phone? Light/dark following the phone?
6. **Name and address**: "Knightwise" at abhra71.github.io/ChessCoach/app (it goes live only when merged to main).
   Link it from the website's home page then, or keep it quiet until v1?
7. **Free stores later** (F-Droid, Galaxy Store, Indus): a PWA can be wrapped as an Android app (Bubblewrap,
   Apache-2.0). F-Droid may label it for using chess.com (a non-free online service); to check when we get there.

## 8. Time estimates (honest)

Work by Claude in sessions, with you testing on your phone. "Day" = one working session.

| Step | Estimate | Status |
|---|---|---|
| Skeleton: install, username, games list, replay | 1 day | **done 27 Nov** |
| Engine in the browser + measure speed on a real phone | 1-2 days | waits for decision 1 |
| Check your moves + review screen with arrows | 3-4 days | |
| Habits (port the sorting and top "why" reasons) + compare with the PC on your 142 games | 5-7 days | |
| Practice + spaced repetition + streak | 3-4 days | |
| Your phone test, fixes, retest | 5-7 days | needs you |
| **v1 total** | **about 3-4 weeks** | |

Risks: the engine might be too slow on cheaper phones (then: fewer games, or shallower checks, decided on real
measurements); the phone's verdicts may differ from the PC's until tuned; iPhone storage rules.

## 9. Good first learning tasks for you (marked ⭐)

Small, real pieces of the app, each with a test to tell you if it works. JS and Python are close enough that each
helps the other.

- ⭐ **Read `docs/app/rules.js`** (about 170 lines, lots of comments): how "Nbd7" becomes a move. Then add one test
  to `tests/mobile/rules_test.js` (for example, castling queenside for Black) and run `node tests/mobile/rules_test.js`.
- ⭐ **A filter on the games list** (JS, `docs/app/app.js`): buttons "All / Wins / Losses / Draws". About 15 lines.
- ⭐ **Better ending words** (JS, `docs/app/games.js`): the `CC_HOW` and `LI_HOW` lists turn "checkmated" into
  "checkmate". Make them read nicer, e.g. "they ran out of time" vs "you ran out of time".
- ⭐ **Python twin of the PGN reader** (Python): write `pgn_moves(text)` that does what `pgnMoves` in `games.js`
  does, with a pytest test using the same example. Good practice with strings and lists.
- ⭐ **The win-chance formula** (Python then JS): `win_chance` in `coach/analyze.py` is 2 lines. Write it in JS for
  the phone, and check both give the same numbers for -300, 0, +300.
- Later, bigger: port the "hanging piece" habit from `coach/why.py` to JS, with Claude as tutor (you write first).

## 10. Try it now

On the PC, from the repo folder:

```powershell
python -m http.server 8771 --bind 127.0.0.1 --directory docs
```

Then open http://localhost:8771/app/ (press F12 and pick a phone size to see it at phone width).

What's there: `docs/app/` - `index.html` (the page), `app.js` (the three screens), `games.js` (downloads and reads
games), `rules.js` (the rules of chess for replaying), `board.js` and `pieces.js` (copied from the PC app),
`app.css` (the calm look), `sw.js` + `manifest.webmanifest` (install and offline). Tests: `tests/mobile/rules_test.js`
(also run by `python -m pytest` when Node.js is installed).

Checked on real games 27 Nov: 300 games from five public accounts (60 each; three on chess.com, two on Lichess)
replayed with no errors; for all 180 chess.com games the final position matched exactly the one chess.com
recorded. Also tried in a phone-sized browser window: username, list, replay, swipe-free buttons, a wrong
username, no sideways scrolling. **Not yet tried on a real phone or installed to a home screen.**
