# Knightwise: the maintainer's handbook

Written on 20 Oct 2026, at 1.0, brought up to date on 23 Oct 2026 after the hand test, for keeping Knightwise working for years with no Claude Code: just you, a normal
Claude chat, and this file. Every recipe says what to type, what to check, and how to undo it.

---

## 0. Start here: working with a Claude chat

A Claude chat can't see your PC or run anything. It reads what you paste and writes changes for you to make. So:

1. **Open a new chat and paste this first:**
   > I maintain Knightwise, a free open-source chess coach for chess.com (Windows app in Python, plus a Chrome/Edge
   > extension). Here is the maintainer's handbook: [paste this whole file]. I'll paste the files you need. Please
   > give me exact edits (the old text and the new text), keep the code's style, use British spelling, and tell me
   > which tests to run. Never suggest anything that helps during a game against a real person.
2. **Paste the files it asks for.** Section 2 says which file does what. Paste the whole file, not a piece.
3. **Make its edits** in VS Code or Notepad: find the old text, replace it with the new.
4. **Run the tests** (section 3). Paste the result back if anything fails.
5. **Try it** in the app, the part you changed.
6. **Commit and push** (section 3) only when the tests pass.

**Big changes:** ask for one small step at a time. A chat can't hold the whole app in its head; this handbook and
the file you paste are its memory. If a change grows past three files, stop and split it.

**If a chat's change breaks things:** `git checkout -- .` throws away every change since your last commit (section 3).

---

## 1. The rules that never change
- **Fair play.** Completely off during any game against a real person: no hints, no arrows, no reading the board.
  Fully on everywhere else. The extension only shows itself on an allow-list of chess.com sections
  (`extension/buddy.js`, `section()`), and the review only for games chess.com has archived as finished.
- **Free.** No paywall, no adverts, no account. AI is optional, with the player's own free key.
- **Honest.** Never claim a rating gain or anything not proven; say where things come from. The human-move model is
  "an estimate of a level, never a real person".
- **Player data and keys never go in the repo.** `data/`, `logbook/`, `engine/`, `voice/` and `coach/ui/vendor/`
  are in `.gitignore`. Keys live in Windows Credential Manager (`coach/settings.py`).
- **No word patterns for understanding speech.** The AI works out what a player meant (`coach/talk.py`).
- **Discuss before downloading anything new:** what, why, source, size, licence.
- **Tests pass before every commit.**

---

## 2. The map: which file does what

| You want to change… | The file |
|---|---|
| What the coaches say (sentences, jokes) | `coach/coaches.py` (`SAY`, `JOKES`) |
| What the coaches do on chess.com (Maya's box, warm-up, red ring, Talk) | `extension/buddy.js` |
| The review on chess.com's own board | `extension/coach.js` |
| Everything Knightwise reads from chess.com's pages | `extension/contract.js` (+ `fixes.json`) |
| The red ring's routes | `coach/coaches.py` (`ROUTES`) |
| The app's pages | `coach/ui/app.js` (one function per page: `home()`, `reportView()`, …), styles `coach/ui/app.css` |
| The coaches in the app, Talk, the board trainer | `coach/ui/coaches.js` |
| The app's server (every `/api/...` address) | `coach/service.py` |
| Downloading games from chess.com | `coach/fetch.py` |
| Checking moves with Stockfish | `coach/analyze.py` |
| Why a move was a mistake | `coach/why.py` |
| Every move's label and line in a review (Book, Brilliant, Best… Blunder), openings, accuracy | `coach/narrate.py` (`LABELS`, `_label()`, `_sacrifice()`, `accuracy()`) |
| What the AI coach is told, and what it may do (open, review, guide, offer…) | `coach/talk.py` (`RULES`, `ABOUT`, `VERBS`, `action()`) |
| When Maya greets on chess.com, the folded tab, her suggestions there | `extension/buddy.js` (`kw-visit-greeted`), `coach/coaches.py` (`CHESSCOM_FOR`, `fresh_today()`) |
| The Ask bars in the app (the answer fading, the glowing suggestion) | `coach/ui/app.js` (`askBox()`) |
| The coach coming up by herself with one new thing per page (a new game, today's 5 minutes, a rematch, the next lesson, something untried, chess.com's place for the habit) | `coach/nudge.py` (`candidates()`, `UNTRIED`, `A_DAY`), shown by `with_point()` in `coach/service.py`, pointed at by `kwPoint()` in `coach/ui/app.js` and `guideStart()` in `extension/buddy.js` |
| Send feedback (one click, 4 a day) | `coach/service.py` (`SENDS_A_DAY`, `feedback_send_allowed()`), key in `coach/feedback.key` |
| Habits (hanging pieces, forks…) | `coach/patterns.py`, `coach/review.py` (`ABOUT`) |
| Practice positions and puzzles | `coach/drills.py`, `coach/puzzles.py`, `coach/memory.py` |
| The course, the level ladder, the plan | `coach/course.py`, `coach/ladder.py`, `coach/plan.py` |
| The human-move model (Maia-3) | `coach/maia.py` (+ `installer/make_maia3.py`) |
| Guess the human move, Blindfold, the film, the report | `coach/guess.py`, `coach/blindfold.py`, `coach/film.py` + `coach/ui/film.js`, `coach/report.py` |
| Rematch, sparring, prep, endgames, clock | `coach/rematch.py`, `coach/spar.py`, `coach/prep.py`, `coach/endgames.py`, `coach/clock.py` |
| The AI (Groq, Gemini) and hearing | `coach/ai.py`, `coach/talk.py`, `coach/hearing.py`, `coach/heard.py` |
| The voices | `coach/voice.py` |
| Settings and keys | `coach/settings.py` |
| Where files live, the version | `coach/paths.py`; the version number is in `extension/manifest.json` |
| The fix file | `fixes.json` (repo root) and `coach/fixes.py` |
| The installer and Store package | `installer/` |
| Tests | `tests/` (one file per part: `tests/test_<part>.py`) |

---

## 3. Everyday commands
Open **PowerShell** in the project folder (in Explorer: the folder, then type `powershell` in the address bar).

| What | Type |
|---|---|
| Run all the tests (about a minute) | `python -m pytest -q --ignore=tests/test_live_chesscom.py` |
| Run one part's tests | `python -m pytest -q tests/test_coaches.py` |
| Try the app with your games | double-click `try.bat` |
| Try it as a brand-new player | `try fresh` |
| See what you changed | `git status` then `git diff` |
| Throw away every change since the last commit | `git checkout -- .` |
| Commit and push | `git add -A` then `git commit -m "What changed, in plain words"` then `git push` |
| See the app's own log | open `logbook/service.log` |
| A test copy with its own data and no keys (kept between sessions) | `try test`; start it again from nothing: `try test new`. Its data is in `%TEMP%\knightwise-test` |

**After a change, what to restart:**
- a `.py` file: quit Knightwise from the tray (or close its `pythonw` processes) and start it again;
- a file in `coach/ui/`: press **Ctrl+R** in the app window;
- a file in `extension/`: `chrome://extensions` → Knightwise → the round arrow, then refresh the chess.com tab.

**Tracing what the coach did:** every talk turn writes one line to `logbook/service.log`:
`talk maya at home: 'what they said' -> the action, ai=True, 2.1 s: 'what she answered'`. When she does the wrong
thing, paste that line and `coach/talk.py` into the chat.

**Tests on GitHub:** every push runs all the tests on GitHub's computer. A failure emails you. To see why without
signing in: open the repo's **Actions** tab, the failed run: each failing test is named there.

**Two chess.com checks run by themselves:** on every visit, in the player's browser (Settings shows the result), and
every Monday on GitHub (`.github/workflows/chesscom-check.yml`), which opens a GitHub issue if chess.com's public API
changed.

---

## 4. When something breaks: symptom → cause → fix

| # | What you see | Most likely | Fix |
|---|---|---|---|
| 1 | Maya or the tags stopped appearing on chess.com | chess.com renamed something | Section 5 (the fix file). Settings → chess.com check names what broke |
| 2 | Reviews don't appear on chess.com game pages | chess.com moved its game addresses (it did on 13 Oct 2026) | Add the new address pattern to `game_addresses` in `fixes.json` (section 5) |
| 3 | The red ring says "I can't find the way from this page" | a chess.com menu link moved | `nav` in `fixes.json` (section 5); or change `ROUTES` in `coach/coaches.py` |
| 4 | No new games come in | chess.com's public API changed, or no internet | The Monday check opens an issue with the detail. `coach/fetch.py` reads the API; the last good games are kept |
| 5 | Talk answers slowly, or "I can't reach the AI" | the provider retired a model, or its free limits changed | `coach/ai.py` picks models from the provider's own list: update the preference lists (`_openai_style(... prefer ...)`, `_gemini`, `SMALL`). Test with Settings → Test key |
| 6 | Talk hears nothing | the hearing model was renamed | `HEAR_MODEL` in `coach/ai.py` (Groq: `whisper-large-v3`); also the microphone in Windows Sound settings |
| 7 | The coach answers but the reply is cut off or empty | a reasoning model used up its length | `THINK_ROOM` in `coach/ai.py`; for a new Groq model family, add it next to the `gpt-oss` line |
| 8 | No voice | Kokoro files missing or a voice renamed | `python -m coach.get_voice`; voice names in `coach/voice.py` (`CHOICES`) |
| 9 | The welcome film or game film is black | Three.js or the 3D set didn't load | `python -m coach.get_assets`; if Three.js was upgraded, see section 6 |
| 10 | "Couldn't load this screen" on a page | a bug in that page | The message names the error. Paste it, the page's function from `coach/ui/app.js`, and the `/api/...` part of `coach/service.py` into the chat |
| 11 | The extension says "Knightwise was updated, refresh this page" | the app is newer than the page | Refresh the page. Normal after an update |
| 12 | Rematch or Guess the human move fails | the human-move model file is missing | `python -m coach.get_engine` (downloads Stockfish and Maia-3) |
| 13 | The app won't start | port 8765 is taken by another Knightwise | Quit Knightwise by the clock, or restart the PC |
| 14 | A test fails on GitHub but not on your PC | GitHub's computer is Linux and has no saved data | The failing test assumes something about your PC; make it set up what it needs (see `tests/conftest.py`) |
| 15 | The Store rejects an upload | version not higher, or the manifest changed | Section 7: the version must go up in both places |
| 16 | Talk does the wrong thing (opens a page when asked for advice, ignores "please do") | the AI misread `RULES` | Find the `talk` line in `logbook/service.log`; add one plain sentence to `RULES` in `coach/talk.py`, and a test in `tests/test_talk.py` |
| 17 | A review label looks wrong (too many Excellent, a false Brilliant) | the thresholds | `LABELS` and `_label()` in `coach/narrate.py` (win chance lost, plus pawns given away); `_sacrifice()` for Brilliant. Tests: `tests/test_narrate.py` |
| 18 | Talk hears words nobody said, or ignores a quiet voice | the silence gates | `QUIET` (600) and `NO_SPEECH` (0.6) in `coach/ai.py`. Lower `QUIET` for quiet microphones |
| 19 | Send feedback stops working | the Web3Forms key is missing, or 4 sends today already | Is `coach/feedback.key` packed in the build? The limit is `SENDS_A_DAY` in `coach/service.py`. Without a key it opens the email app |
| 20 | The red ring stops after one page | a page reached mid-route skipped the ring | `guideArrive()` in `extension/buddy.js` must run before the quiet-greeting return (fixed 23 Oct) |
| 21 | The voice is too fast or too slow when teaching | the teaching pace | `SLOW` (0.86) in `coach/voice.py`; greetings use the normal pace |

**To pause a broken feature for everyone at once** (while you work on it): add its name to `off` in `fixes.json`
(section 5). Names: `review`, `tags`, `warmup`, `prep`, `talk`, `coach`, `guide`. It shows "resting" instead of
breaking.

---

## 5. The fix file: repairing chess.com changes without a release

Every copy of Knightwise reads `fixes.json` from GitHub's **main** branch once a day. An edit there reaches every
player the next day. No new version, no Store upload. (Until dev-0.6 is merged into main, main has no fixes.json;
the self-healing below works anyway.)

**Knightwise already heals itself first:** when a name stops working, it looks for the thing by what it is (the
board by its pieces, the archive rows by their game links) and reports what it found in Settings → chess.com check.
The fix file is for when that isn't enough.

**Steps:**
1. On chess.com, find the new name. In Chrome: right-click the thing → **Inspect**; the highlighted line shows its
   tag and `class="…"`. Or read it from Settings → chess.com check, which often names it.
2. On github.com, open `fixes.json` on the **main** branch → the pencil (Edit).
3. Add the new name **first** in its list (old names stay as backups):
   - the board: `"boards": ["new-board-name"]`
   - archive rows / the line under them: `"archive_rows"`, `"archive_slots"` (CSS selectors, e.g. `".new-row-class"`)
   - a new game address: `"game_addresses": ["^/games/live/(\\d+)"]` (a pattern; the game number in brackets)
   - a red-ring route: `"nav": {"bots": ["/play", "/play/computer"]}`; a button by its words: `"/puzzles/rated|Solve Puzzles"`
   - pause a feature: `"off": ["guide"]`
4. **Commit changes.** Raise `"version"` by one.
5. Check the next day on your own PC (or restart Knightwise: it reads it at start).

Only short text and known names are accepted (`coach/fixes.py` checks), so a typo can't break the app; at worst
the line is ignored.

---

## 6. Upgrading a part: will anything break?

**If you never upgrade a part, it keeps working exactly as tested.** Nothing in Knightwise updates itself except the
fix file. Upgrade only when there's a reason (a bug fixed upstream, a security fix, something stopped working).

**The general recipe, for any part:**
1. Write down the old version (the table below says where it's set).
2. Change that one number.
3. Run the download command for that part, if it has one.
4. Run all the tests.
5. Try the parts of the app the table names.
6. All fine: commit with the new version in the message. Anything wrong: put the old number back and run the
   download again. That's the undo.

| Part | Version now | Where it's set | What could break, and what to check | Risk |
|---|---|---|---|---|
| **Stockfish** (the move checker) | 19 | `coach/get_engine.py` downloads the latest release | Its scores can shift a little between versions. Knightwise turns scores into winning chances (`coach/analyze.py`) and uses thresholds (a big mistake = 25+ points of winning chance; endgames "won" at +4). Check: reviews still find the same big mistakes; tests `test_patterns`, `test_endgames`, `test_why`. After upgrading, raise `CACHE_VERSION` in `coach/drills.py` so practice is worked out again | Low |
| **The human-move model** (Maia-3, 5M) | weights of 20 Oct 2026 | `installer/make_maia3.py` (URL) → `engine/maia3/maia3-5m.npz` | Knightwise runs the model itself (`coach/maia.py`), copied line by line from Maia-3's code. New weights with the same design: just run `python installer/make_maia3.py`. A different design (more layers, other sizes, a new input): `HEADS`, `LAYERS` and `logits()` in `coach/maia.py` must match the new code. **The proof:** `tests/test_maia.py` checks it still predicts about half of strong players' real moves; a wrong copy scores far lower. The bigger 23M model uses a part (`gab_per_square_dim` > 0) that `logits()` doesn't have yet | Medium |
| **python-chess** | 1.11.2 | `requirements.txt` | Very stable. Run all tests | Low |
| **Three.js** (3D) | r186 | `THREE` in `coach/get_assets.py` | Three.js renames things often between versions. Check the welcome film (`coach/ui/backdrop.js`) and a game film (`coach/ui/film.js`): `try fresh` shows the welcome; Progress → your best game → film. The importmap in `coach/ui/index.html` names the files | Medium |
| **The 3D chess set** | Poly Haven "Chess Set", 2k | `coach/get_assets.py` | It's built as a mirror image, so both films flip the picture. A different set: remove the flip in `film.js` (`ctx.scale(-1, 1)`) and in `app.css` (`.backdrop canvas … scaleX(-1)`) if its queens stand on their own colour | Low |
| **Kokoro** (voices) | kokoro-onnx 0.6.1, model files v1.0 | `requirements.txt`, `coach/get_voice.py` | Voice names (`af_heart`, `am_michael`) must still exist: `coach/voice.py` `CHOICES`. Listen to Maya and Viktor | Medium |
| **onnxruntime** | 1.31.0 | `requirements.txt` | Used by the voices. Listen after upgrading | Low |
| **faster-whisper** | 1.2.1 | `requirements.txt` | Only for hearing on the PC without a key (optional) | Low |
| **pywebview** (the app window) | 6.2.1 | `requirements.txt` | The window, the tray, saving pictures. Open the app, every page, quit from the tray | Medium |
| **pystray** (the icon by the clock) | 0.19.5 | `requirements.txt` | The icon and its menu | Low |
| **keyring** (keys in Credential Manager) | 25.7.0 | `requirements.txt` | Keys still found: Settings shows "set, ends with …" | Low |
| **numpy** | 2.5.3 | `requirements.txt` | The human-move model and hearing: tests `test_maia`, `test_hearing` | Low |
| **Groq and Gemini models** | chosen by Knightwise from their lists | `coach/ai.py` | They change by themselves; Knightwise picks from what they list. See section 4, rows 5 to 7 | – |
| **GitHub's test computer** | ubuntu-latest, Python 3.12 | `.github/workflows/tests.yml` | GitHub moves "latest" forward (Ubuntu 26 from 19 Oct 2026). If the tests break only there, pin `runs-on: ubuntu-24.04`. Keep the pip line's versions the same as `requirements.txt` | Low |
| **Chrome/Edge extension rules** (Manifest V3) | MV3 | `extension/manifest.json` | Rare. Chrome announces changes a year ahead | Low |
| **PyInstaller, Windows SDK tools** (building) | whatever is installed | your PC | Only matter when building (section 7). If a build fails after upgrading one, go back a version | Low |

**Things that change without anyone asking** (and what protects you):
- chess.com's pages: self-healing, the fix file, the check in Settings.
- chess.com's public API: the Monday check on GitHub opens an issue.
- Groq and Gemini models and free limits: Knightwise picks from their lists; the coach falls back to its written sentences.
- Lichess: puzzles and the opening catalogue are downloaded once and kept; the endgame tablebase is asked live
  (`coach/endgames.py`, `TABLEBASE`) and the engine takes over if it doesn't answer.
- Windows and WebView2: the app window; rarely a problem.

---

## 7. Releasing a new version

**You need:** a parent for anything in Partner Center that asks to accept terms (you're under 18). About an hour.

0. **The full hand test comes first. Never build or upload before it.** Biggest features first: game review, the
   coach on chess.com, Talk, practice and daily, plan/course/level, Train, Home/Progress/Settings, then rare things.
   Note each finding in `docs/TEST-NOTES-1.0.md` (a number, what you saw, fixed or not). Fix, test again, and only
   when the list is clear go on to step 1. A quick test instead of the full one has always let something through.
1. **The version number goes up in two places**, always together:
   - `extension/manifest.json` → `"version": "1.0.1"` (three numbers)
   - `installer/msix/AppxManifest.xml` → `Version="1.0.1.0"` (four numbers, the last always 0)
   The Store refuses a version that isn't higher than the last one.
2. **Tests:** all pass.
3. **Get the parts** (only once on a new PC, or after upgrading one):
   `python -m coach.get_engine` · `python -m coach.get_voice` · `python -m coach.get_assets`
   **Two files that are never in the repo, but must be next to the code before a build:**
   - `coach/puzzles-pack.json`: the puzzle set packed in the app, so a new player doesn't wait for a 300 MB download.
     Make it with `python -m coach.puzzles` (it writes `data/puzzles.json`) and copy that file to
     `coach/puzzles-pack.json`. If you change `KEEP_THEMES` in `coach/puzzles.py`, raise `VERSION` there and remake it.
   - `coach/feedback.key`: the Web3Forms access key (one line) that lets Send feedback email you in one click. It's on
     web3forms.com, signed in as nanotech.mark.robots@gmail.com. Without it, Send opens the player's email app instead.
4. **Build the app:** `python -m PyInstaller installer/Knightwise.spec --noconfirm` → `dist\Knightwise`
   (the trailer's 225 MB in `coach/ui/vendor/trailer` is left out by the spec on purpose)
5. **Build the Store package:** `python installer/make_msix.py` → `dist\Knightwise-<version>.msix` (about 300 MB).
   It needs Microsoft's free Windows SDK Build Tools unpacked in `build\sdktools` (nuget.org package
   `Microsoft.Windows.SDK.BuildTools`).
6. **Upload:** partner.microsoft.com → Apps and games → **Knightwise** → **Start update** → Packages → drop the
   .msix → Store listings (text in `installer/msix/STORE_LISTING.md`; update it when features change) → **Submit**.
   Certification takes from 30 minutes to a few days; Partner Center emails you.
7. **The extension for Edge:** zip the *contents* of the `extension` folder → partner.microsoft.com → Edge →
   Extensions → Knightwise → Update → upload the zip → Submit. (Chrome users load it from the app: Arrows on
   chess.com.)
8. **Merge and tag:** `git checkout main`, `git merge dev-…`, `git push`, then `git tag v1.0.1` and `git push --tags`.

**Smart App Control** on your PC blocks unsigned programs, so a build you made yourself may not run there until the
Store has signed it. Test from the source with `try.bat` instead; the Store build is tested after certification.

---

## 7b. The look: rules every screen follows (approved 22 Oct 2026)
- Warm layered greys (sidebar #1e1c1a, page #262421, cards #312e2b), never pure black. No outlines, no coloured bar on
  a card's edge (the owner: "every AI tool has that bar").
- One green button per screen, for the one thing to do. Red or orange only for danger, like a blunder.
- Pictures and numbers instead of sentences: small boards, bars, dots, a ✓. A card has a title and at most one short
  line; anything longer goes on hover (a `title`), behind the small **?** by the page title, or is spoken by the coach.
- The coach's bubble shows two sentences and one button; More shows the rest. The voice says it all.
- Long page intros (`<p class="sub">` over 90 characters) fold into the **?** by themselves (`foldIntros` in app.js).

## 7c. How the coach behaves (decided in the 22–23 Oct hand test)
- **She comes up by herself.** Opening a page in the app or on chess.com, she says the one new thing for it and points
  (the app: it glows; chess.com: the red ring starts). Each suggestion once a day, three a day at most per place;
  never in a game against a real person or in a review.
- **A coach, not a tool.** Asked "what should I do?", she suggests one thing and the menu item for it glows. She opens
  it only when the player says yes, ok or please do (`offer` in `RULES`, `point()` in `askBox()`).
- **Her typed answer goes away** after a minute, or when the player presses a button or link or types elsewhere; not
  on a click on empty space, and not while the mouse rests on it.
- **On chess.com:** she greets and talks once per visit, then waits as a folded tab. When she has buttons to offer,
  the whole text shows; otherwise two sentences and More.
- **chess.com things asked for in the app** (its puzzles, bots, lessons) open chess.com in the browser; Knightwise's
  own practice is not chess.com. On chess.com itself, the red ring shows the way.
- **Small talk gets small talk.** Her habit tip only when it answers the question (finding 38 is still open).
- **Teaching pace:** reviews, training and numbers are spoken slower than greetings.

## 8. After 1.0: ideas kept for later, with how to start
Each is a separate, small piece of work. Paste this section with the files named.
- **Blindfold, harder questions.** `coach/blindfold.py` `questions()`: add a kind (e.g. "which square is attacked
  twice?"), with its answers from python-chess, and a test in `tests/test_blindfold.py`.
- **"Where you lose pieces" heat map.** From `data/moves.jsonl` (the squares of hanging pieces) to a board coloured
  by count. A new page in `coach/ui/app.js` and an `/api/...` in `coach/service.py`, the data from `coach/insights.py`.
- **The bigger human-move model (Maia-3 23M).** `logits()` in `coach/maia.py` needs the per-square part of the
  attention bias (`gab_per_square_dim`, `sm1`), copied from Maia-3's `models.py`; then the 23M weights in
  `installer/make_maia3.py`. 92 MB and slower: measure first.
- **Languages.** All the words are in `coach/coaches.py`, `coach/ui/*.js` and `extension/*.js`; a language switch
  means keeping each sentence per language, plus Kokoro voices for it. Only with a native speaker checking.
- **Re-measure chess.com → Lichess ratings** for the human-move model with more games above 400: the method is in
  `coach/maia.py` (`RATING_FROM_CHESSCOM`); one Python script over your games and your opponents' moves.

---

## 9. About the owner
How the owner likes to work, and what the app's decisions were, is in the owner's private notes on their own PC
(`jarvis-keep\KNIGHTWISE-OWNER-NOTES.md`), not in this public repo. A chat helping the owner should ask for them.
The public decisions are in `ROADMAP.md`, `docs/PLAN-1.0.md` and `docs/FLAGSHIPS.md`.
