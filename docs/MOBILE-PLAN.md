# Knightwise on the phone: the plan

Written 27 Nov 2026 while the owner studies for exams (1-11 Dec). Nothing here is decided until the owner says so.
Section 7 lists the decisions waiting for you.

**Short version:** a first phone app already works (37 KB on first open, no downloads): type your chess.com or
Lichess username, see your newest finished games (60, or fewer on a phone with little memory), replay any of them
on a board. It is built for **cheap phones** (section 4b) and measured on a simulated one: first screen in 1.8 s on
slow 3G with the processor slowed 6 times. The next big step is the engine (Stockfish built for the browser,
"lite" 1.9 MB, GPL-3, needs your OK). A first real version (review, habits, practice from your own mistakes,
optional Google sign-in to sync phone and PC: section 11) is about **5-6 weeks of work** after you approve it
(3-4 weeks without the sign-in).

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
6. **Optional Google sign-in** to carry your progress between phone and PC (owner decision 27 Nov; section 11).

Not in v1: course, ladder, openings, prep, voice conversation, AI keys. They come one by one later.

**How the engine works on a phone (plan):** the PC checks at depth 14 on all cores. A phone runs one thread.
So: check only *your* moves, newest 20 games first, show results as each game finishes, check the rest while the
app is open (a web app can't work when closed). Speed on a real phone is **not measured yet**: this is the
first job once the engine is approved. Then compare the phone's verdicts with the PC's on your own 142 games, so
the phone and PC agree on what a blunder is (the same 25-point "winning chance" drop, `coach/patterns.py`).

## 4a. First launch: the owner's scope (28 Nov 2026) - this replaces section 4's list for the first launch

Owner: "the core and 1 or 2 small mobile features", plus one flagship. Decided on 28 Nov:
- **Core:** replay and review finished games with their key moments; today's 5 minutes + streak; your numbers and focus.
- **Flagship: the analysis board** (`docs/app/analysis/`): move either side, arrows and circles, set up any position,
  promotion, flip, step through a line, open from any moment of your finished games. **No engine on the board, ever**
  (owner's choice: it stays a wooden board on a screen). Built on **chessground 9.2.1** (Lichess's board, GPL-3.0-or-later,
  30 KB + 15 KB of CSS, approved 28 Nov, in `docs/app/vendor/chessground/`). A self-contained module the PC app can reuse.
- **Engine for the core: Stockfish.js 19 lite**, single-threaded, 1.9 MB (approved 28 Nov). Never on the analysis board.
- **Phone touches:** a home-screen shortcut to Today's 5 minutes; swipe between a game's key moments.
- A gentle "the full coach is on PC" pointer to the Store page.
- Google sign-in (section 11) and the rest of section 4 wait until after the first launch.
- **Owner, 28 Nov (after trying it):** rewrite the PC's thinking in **JavaScript** (option A, section 2), with the PC's
  rules and tests as the answer key. Build the **core first**, then the board. The phone must open on a **Home page like
  the PC's** (Today 5 min + Start, last game + Review, Your focus + Practise, habit numbers, streak), and a game page
  like the PC's review (key moments with "You played / Better" arrows; all moves folded away). The analysis board
  stays built but hidden until the core is done.

## 4b. Built for cheap phones (owner's rule, 27 Nov)

**The phone we design for:** a cheap Android phone, Android 9 or newer, Chrome; **2-3 GB of memory, 4 slow
cores**; on slow 3G or patchy 4G. If it runs well there, it runs well everywhere.

What that means in the app (done in the skeleton):

- **Small:** plain JavaScript, no frameworks, system fonts. The whole app's code is 60 KB (before compression);
  the first screen downloads **37 KB in 7 files**.
- **Heavy parts load only when needed:** the board, pieces and chess rules (26 KB) load the first time you open
  a game. The engine will load only when you ask for a check, never on the first screen.
- **Games arrive bit by bit:** chess.com one month at a time, newest first; Lichess read as it streams in. The list
  shows the first games while the rest download. A month's big download is dropped as soon as it's read.
- **Kept small:** each game is a short summary with its moves as one line of text; the board positions are worked
  out only for the game you open. Saved in **IndexedDB** (the phone browser's database), not in memory.
- **Fewer games on weak phones:** the browser says roughly how much memory it has. 60 games normally, 30 with
  2 GB or 2 cores, 20 with 1 GB or less.
- **Smooth board:** the board has a fixed square size (nothing on the page jumps), fast taps draw once per screen
  frame, and only the two changed moves in the move list are repainted.
- **Offline after the first open:** the app's files are kept by the service worker; the big install icons are
  fetched only when installing.

**How it was tested (27 Nov):** a headless Microsoft Edge with a throwaway profile, driven through DevTools
(`tests/mobile/lowend_check.mjs`): **CPU 6 times slower**, **slow 3G** (400 ms delay, 400 kbit/s) or **slow 4G**
(150 ms, 1.6 Mbit/s), a 375 x 812 phone screen, real chess.com and Lichess downloads.

| Measured (CPU 6x slower) | chess.com, slow 3G | Lichess, slow 3G | chess.com, slow 4G |
|---|---|---|---|
| First screen ready | 1.8 s | 1.8 s | 0.8 s |
| Downloaded for the first screen | 37 KB | 37 KB | 37 KB |
| First games on screen | 1.4 s (3 games) | 1.3 s (22 games) | 0.8 s |
| All 60 games in | 5.5 s | 1.7 s | 2.5 s |
| Memory used by the page (JavaScript) | 1.4 MB | 1.7 MB | 1.4 MB |
| Opening a game (first time, loads the board) | 0.24 s | 0.27 s | 0.36 s |
| One tap on "next move" to the new board on screen | 28 ms (worst 33) | 28 ms (worst 33) | 35 ms (worst 41) |
| Reopening with no internet | 0.7 s, saved list shown | 0.6 s | 0.1 s |

With the phone reporting 2 GB of memory: 30 games, all in 3.8 s on slow 3G. **Limits of this test:** a slowed-down
PC is not a real cheap phone (the PC's memory and disk are still fast), and chess.com's speed varies. The real check
is your phone, and a cheap one if a friend has one.

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

- **On the phone only.** Games in **IndexedDB** (the phone browser's database, far more room than `localStorage`;
  `docs/app/store.js`), the username in `localStorage`. The app asks the browser to keep the data
  (`navigator.storage.persist`). The engine's checks will go in the same database. Nothing is sent anywhere except
  the requests to chess.com/Lichess.
- **Offline:** the service worker (`docs/app/sw.js`) keeps the app's files; the last games list is kept, so the app
  opens and replays games with no internet. New games need the internet once.
- **iPhone note:** Safari may clear a website's storage after 7 days unused, but not for an app added to the Home
  Screen. The app should say "Add to Home Screen" on iPhone.
- **Size budget (first install):** app 0.06 MB of code now (37 KB for the first screen) + engine 1.9 MB +
  data for one player about 1 MB = **under 5 MB** for v1 (the PC package is 376 MB). Any extra (puzzles, film,
  voice) is downloaded only when used. Rule: the first screen stays **under 200 KB**.

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

   **Lite vs full on a cheap phone:**

   | | Lite, single-threaded | Full, single-threaded |
   |---|---|---|
   | Download (once, then kept offline) | 1.9 MB: about 40 s on slow 3G, 10 s on slow 4G | 99 MB: about 33 min on slow 3G, 8 min on slow 4G |
   | Memory while checking | small net + 16 MB table: roughly 20-40 MB (estimate) | big net alone is most of the 99 MB, so roughly 120-150 MB (estimate); risky with 2 GB, where the browser may close the tab |
   | Speed | small net, so more positions per second (to measure) | stronger per position, slower per position (to measure) |
   | Strength | "far stronger than any human" (its README); enough to find a club player's blunders | full strength |

   The download times are arithmetic from the sizes; the memory figures are estimates. The first job after your
   OK is to measure both on the cheap-phone test and on your phone.

   **Recommended: lite, with a time limit per position**, sized to the phone: about 0.3 s per position on a weak
   phone (2 GB or 2 cores), deeper on stronger ones. A game has about 35 of your moves, so about 10-15 s per game,
   and about 4-5 minutes for the newest 20 games on a weak phone (arithmetic, to measure). How it runs:
   - in a **background worker** (a separate thread), so tapping and scrolling never wait for the engine;
   - **one game at a time**, saved as soon as it's done, so nothing is lost if the app closes;
   - **only while the app is open and on screen**: it pauses when you switch apps or the screen turns off
     (`visibilitychange`), and carries on from the next game when you come back (battery-friendly);
   - the engine downloads only when you first ask for a check, never on the first screen.
   Multi-threaded and full builds stay off for v1 (headers GitHub Pages can't send; size and memory).
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
8. **Google sign-in details**: the decisions marked **[OWNER]** in section 11.

**Decided by the owner (28 Nov):** no backend and no Vercel / Cloudflare hosting. The phone app stays on GitHub
Pages, every phone does its own work (lite engine), and sync goes through each player's own Google Drive.

## 8. Time estimates (honest)

Work by Claude in sessions, with you testing on your phone. "Day" = one working session.

| Step | Estimate | Status |
|---|---|---|
| Skeleton: install, username, games list, replay | 1 day | **done 27 Nov** |
| Engine in the browser + measure speed on a real phone | 1-2 days | waits for decision 1 |
| Check your moves + review screen with arrows | 3-4 days | |
| Habits (port the sorting and top "why" reasons) + compare with the PC on your 142 games | 5-7 days | |
| Practice + spaced repetition + streak | 3-4 days | |
| Optional Google sign-in + sync, phone side | 4-5 days | needs the Google setup (section 11) |
| Optional Google sign-in + sync, PC side (Python app) | 4-5 days | |
| Your phone test, fixes, retest (now with sync between your phone and PC) | 7-9 days | needs you |
| **v1 total** | **about 5-6 weeks** (3-4 without sign-in) | |

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
`app.css` (the calm look), `store.js` (saving on the phone), `sw.js` + `manifest.webmanifest` (install and
offline). Tests: `tests/mobile/rules_test.js` (also run by `python -m pytest` when Node.js is installed);
cheap-phone timings: `tests/mobile/lowend_check.mjs` (section 4b).

Checked on real games 27 Nov: 300 games from five public accounts (60 each; three on chess.com, two on Lichess)
replayed with no errors; for all 180 chess.com games the final position matched exactly the one chess.com
recorded. Also tried in a phone-sized browser window (username, list, replay, a wrong username, no sideways
scrolling) and on the simulated cheap phone (section 4b). **Not yet tried on a real phone or installed to a home
screen.**

## 11. Optional Google sign-in: your progress on phone and PC (owner decision, 27 Nov)

**Decided:** mobile v1 has an **optional** "Sign in with Google" from day one. It keeps your progress the same on
your phone and your PC, in a hidden folder in **your own Google Drive**. There is still no Knightwise server.
Everything works fully without signing in, as it does today. Not built yet; this is the design.
Decisions for you are marked **[OWNER]**.

### What syncs, and what never does

| Syncs (small, about 50-500 KB in all) | Never syncs |
|---|---|
| Practice boxes (which positions, which box, when they're due) | AI keys (they stay in Windows Credential Manager / on the phone) |
| Streak and the days you practised | What the coach heard you say, voice recordings |
| Settings (theme, coach, voice on/off, chess.com and Lichess usernames) | Your games themselves (both apps download them again from chess.com / Lichess) |
| Checked-game results: per finished game, its mistakes and the engine's verdicts | Logbooks, debug logs, feedback |
| Badges earned, lessons passed | Anything about a game that isn't finished and archived (see Fair play below) |

**[OWNER]** Is that the right list? Adding the course and ladder later is easy; they're built from the same data.

### How it works

- **Where:** one small file (`knightwise-sync.json`) in Google Drive's **app-data folder**: a hidden folder
  only Knightwise can see. It isn't in your Drive's file list, other apps can't read it, and Knightwise can't
  see any of your other files.
- **When:** on opening the app, after each practice session or checked game (a few seconds later, so several
  changes go together), and when the internet comes back. Never while the app is hidden (battery, cheap phones).
- **Conflict rule, item by item:**
  - Most things: **the newest change wins.** Each item carries when it last changed and on which device.
    Example: you move a position to box 3 on the phone at 18:00, and to box 2 on the PC at 18:05. Box 2 wins.
  - **Practice days and badges are added together, never lost.** The streak is worked out from the days, so
    practising on both devices on the same day can't break it.
  - Checked games: whichever check is deeper or newer (the PC's full engine beats the phone's lite check).
  - Deleting something leaves a short "deleted" mark, so the other device doesn't bring it back.
  - A device clock that is wrong by a few minutes can pick the wrong "newest". Rare, and it only affects that item.
- **Offline:** changes wait on the device and go up the next time it's online. Nothing is lost by being offline.
- **Signing out** keeps everything on this device; it just stops syncing. A **"Delete my synced data"** button
  removes the file from your Drive.

### Which Google permission (scope)

| Scope | What it allows | Google's checks | Fits? |
|---|---|---|---|
| **`drive.appdata`** (recommended) | Only Knightwise's own hidden app folder | **Non-sensitive**: brand check only (name, logo, website, privacy page; Google says about 2-3 days). No "unverified app" warning, no 100-user cap | Yes: exactly what we need, nothing more |
| `drive.file` | Files Knightwise creates or you open with it, **visible** in your Drive | Also non-sensitive; same brand check | Works, but the file shows in your Drive and can be moved or deleted by accident |
| `drive` (full Drive) | All your files | **Restricted**: full review plus a paid security assessment | No |

Checked on Google's pages on 27 Nov: [Drive scopes](https://developers.google.com/workspace/drive/api/guides/api-specific-auth),
[app-data folder](https://developers.google.com/workspace/drive/api/guides/appdata),
[unverified apps](https://support.google.com/cloud/answer/7454865),
[app audience and testing](https://support.google.com/cloud/answer/15549945). Two limits to know:
- **While the Google project is in "Testing":** only up to 100 test users you list by email, and their sign-in
  expires after 7 days. So we test with your own account (and a parent's or friend's), then publish.
- **After publishing ("In production") with `drive.appdata` only:** no user cap, and no warning screen once the
  brand check passes. The 100-user cap and the warning are for sensitive or restricted scopes, which we don't use.

No email or profile scope is needed: the app doesn't need to know who you are, only to reach its own folder.
**[OWNER]** Show "Signed in as name@gmail.com"? That adds the basic `email` scope (also non-sensitive). Friendlier,
but one more piece of data. My suggestion: no.

### What you (and a parent) do in Google Cloud: about 1-2 hours, then a 2-3 day wait

**A parent is needed** (you're under 18): Google Cloud's terms must be accepted by an adult. Either the project
lives in a parent's Google account (you added as an editor), or a parent accepts the terms on the developer
account with you. **[OWNER]** Which account owns the project? (The developer account is the natural choice.)

1. console.cloud.google.com -> **New project** "Knightwise". **A parent accepts the Google Cloud Terms of
   Service here.** No billing account should be needed for the Drive API at our size (to confirm on the day).
2. **APIs & Services -> Enable APIs -> Google Drive API.**
3. **Google Auth Platform -> Branding:** app name "Knightwise", support email (the developer inbox), logo, home page
   `https://abhra71.github.io/ChessCoach/`, privacy policy link, authorised domain `abhra71.github.io`. The domain
   must be verified in Search Console by an owner of the project: the portfolio was verified on 24 Nov with the
   main Gmail, so that account must be an owner or editor of the project, or verify the domain again.
4. **Audience:** External. Leave it in **Testing** and add test users (your account, a parent's).
5. **Data access:** add the scope `https://www.googleapis.com/auth/drive.appdata` only.
6. **Clients:** create two OAuth client IDs:
   - **Web application** (the phone app): authorised JavaScript origins `https://abhra71.github.io` and
     `http://localhost:8771` (testing on the PC).
   - **Desktop app** (the PC app).
   Paste both client IDs to Claude. They aren't secret (Google says a desktop app can't keep its "secret" secret
   either), so they can go in the open-source code.
7. When sync works for you: **Publish app** (In production) and **submit the brand check** (about 2-3 days).
   **A parent may need to confirm** anything Google emails the project owner about.

### The phone side (web app)

- Signing in uses Google's own sign-in window. Two ways:
  - **Google Identity Services** script from `accounts.google.com` (Google's terms, not open source; size to
    measure), loaded **only when you tap "Sign in"**, never on the first screen. The usual way.
  - **No library:** the plain OAuth redirect to Google and back. Nothing extra to load, a little more code.
  **[OWNER]** Which one? My suggestion: no library (smaller, nothing extra to approve), unless it turns out clumsy
  on iPhone.
- A web app gets a 1-hour pass from Google, with no long-lasting key. After an hour, the next sync asks Google again
  quietly; if that fails (cookies blocked), the app says "Sign in again to sync" and keeps working.
- Talks to Drive with plain `fetch` (no Google library): read the file, merge, write it back.

### The PC side (Python app)

- The **desktop sign-in flow Google recommends**: Knightwise opens your browser at Google's sign-in page, and
  Google sends you back to `http://127.0.0.1:<port>` on your own PC (Knightwise's local server already runs
  there), with PKCE (a one-time check so nothing else can use the answer). No new Python package: `urllib` is
  enough (about 150 lines). A library (`google-auth-oauthlib`, Apache-2.0) would be shorter but is a new download
  needing your OK. My suggestion: no library.
- The long-lasting Google key is kept in **Windows Credential Manager** (like the AI keys), never in a file.
- **The Store app:** the packaged app already runs its local server, so returning to `127.0.0.1` needs no change to
  the package or the Store listing, and the Store app already opens the browser (Send feedback, chess.com links).
  To test on the Store build before release.
- Sync runs in the background service at the same calm moments as the phone (after practice, after a checked game,
  on start), never on a timer that wakes the PC.
- Settings gets a "Sync with Google (optional)" card: Sign in / Signed in, Sync now, Sign out, Delete my synced data.

### Privacy policy changes (`PRIVACY.md`)

Today it promises no accounts. Before the release that adds sign-in it needs:
- "Sign in with Google is optional. If you use it, your progress (the list above) is saved in a hidden app folder
  in **your own Google Drive**. Knightwise has no server; the maker never sees it."
- What is sent to Google, when, and that Google's privacy policy applies to it.
- How to delete it: the app's "Delete my synced data", or Google Drive -> Settings -> Manage apps -> Knightwise ->
  Delete hidden app data; and how to remove Knightwise's access at myaccount.google.com/permissions.
- Google's required line: Knightwise's use of information from Google APIs follows the
  [Google API Services User Data Policy](https://developers.google.com/terms/api-services-user-data-policy),
  including the Limited Use requirements.
- The Children section: signing in uses the player's own Google account, under Google's own age rules.
- Also update, with a parent: the Store's data questions in Partner Center and the age rating (IARC).

### Fair play

- Sync only carries what both apps already allow: progress, settings, and results of **finished, archived** games.
  There is no item for a position, a move suggestion or a game in progress, and the merge **drops anything it
  doesn't know**, so even an edited sync file can't carry help into a game.
- Neither app ever syncs from a chess.com or Lichess game page, and the PC doesn't sync while the extension says a
  game may be running in any tab (it already pauses the coach then).
- The phone can't send a position to the PC for analysis, nor the PC to the phone. No "analyse this" path exists in
  any direction.

### Time added to v1 (honest)

| Piece | Estimate |
|---|---|
| Your Google Cloud setup (with a parent) | 1-2 hours, then a 2-3 day wait for the brand check |
| Phone: sign-in, Drive file, merge rules, offline queue, Settings card, tests | 4-5 days |
| PC: desktop sign-in, Credential Manager, the same merge rules in Python, Settings card, tests | 4-5 days |
| Testing both together (two devices, offline, conflicts, sign out, delete), fixes | inside your phone test (now 7-9 days) |
| **Added to v1** | **about 2 weeks**: v1 goes from about 3-4 weeks to **about 5-6 weeks** |

The merge rules would be written once in Python and once in JS, with the **same test cases** for both, so phone
and PC always agree. ⭐ A good learning task: write the Python merge for one item kind (the practice days) from
the JS version, with its test.
