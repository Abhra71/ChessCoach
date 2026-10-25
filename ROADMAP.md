# Knightwise: where we are and what comes next

## 26 Oct 2026: Knightwise 1.0 is ready to submit (START HERE)

**State:** dev-0.6 merged into main. The final Store package is `dist\Knightwise-1.0.0.0.msix` (359 MB, built from
main; not in the repo). Checked: 275 tests, a smoke test of the built app (every page, the voice, the human-move
model), Defender clean, VirusTotal 1/62 (SentinelOne's "Static AI - Suspicious MSIX", a false positive on an
unsigned package), offline, no AI key, a brand-new chess.com account (0 games) and a one-game account. Two
independent code reviews (0.6-0.9 and 0.9-1.0): every real finding fixed, four of them fair play.

**Launch, with a parent (Partner Center):** upload the MSIX; listing text from `installer/msix/STORE_LISTING.md`;
screenshots; age rating (IARC questionnaire); privacy link https://github.com/Abhra71/ChessCoach/blob/main/PRIVACY.md;
free; publish manually after certification (1-5 days: first public release, full-trust and microphone are reviewed).
Trailer: later, as a listing update (no new package).

**1.1 list:** Claude and OpenAI keys back (tested); a backup and restore file; the local server accepts only
Knightwise's own extension ID; master games (undecided); report the SentinelOne false positive; the trailer;
a GitHub release with the Windows installer (unsigned: SmartScreen warns), only if wanted.

**Tidy after launch:** the main folder `C:\Syntax_Assembler\ChessCoach` has two 19 Oct leftovers (an empty
`coach/ladder.py` and a one-line label change in `app.js`); uninstall the old Store Knightwise 0.4.1 from this PC.

*Hand-over notes for the next work session (updated 14 Oct 2026). Read this after CLAUDE.md.*

## Branch dev-0.6, 14 Oct 2026 (built while the user was away; worktree C:\Syntax_Assembler\ChessCoach-0.6)
On top of 0.5.0 and the 0.6 AI backend (branch ai-0.6, merged in). Test guide: docs/TEST-0.6.md. Version 0.6.0.
- **0.6 Talk by voice (flagship 2):** hands-free, in the app and on chess.com. Hearing: Groq's cloud Whisper with the
  player's key, Gemini as backup (Jarvis's record: 107 sentences at about 0.5 s); Whisper on the PC only optional.
  The coach can open a page, a game's review, a rematch, or the review's next step; each action is checked.
- **0.6 Your level:** the ladder from beginner to 2,000+, five levels, each skill measured on the last 20 games, with
  its training one click away. Goals are a first estimate, said so; no rating promised.
- **0.6 Send feedback** for beta testers: saved on the PC; where it goes is the user's choice (not decided).
- **0.7 Endgame trainer:** six endings against perfect defence from Lichess's tablebase (engine when offline).
- **0.7 Clock coach part 2:** the slow-down drill on your own rushed mistakes.
- **0.8 Prep before a game (flagship 1):** a player's openings and how their games end, from public games; chess.com
  profile pages offer it. **Your repertoire:** three lines, from what you play, the catalogue and Stockfish.
- **0.9 See it in your head:** calculation, the whole line before anything moves; 11 more Lichess themes.
- **0.10 The teacher (user's go-ahead, 14 Oct evening: "is this app a teacher or only a tracker?"):**
  - **The why** (coach/why.py): every mistake gets a reason worked out from the board and the engine's line (about 20
    ideas: a piece put where it's taken, a threat not answered, a guard moved away, forks, pins, skewers, discovered
    attacks, back rank, pieces left at home, king safety, pawn weaknesses, passed pawns, the king in the endgame...).
    On the user's 769 real mistakes: a simple reason for 67%; in a game review the engine's longer line explains about
    a third of the rest; the remainder is said honestly ("a few moves deep"). Shown in the review, app and chess.com.
  - **Your course** (coach/course.py): 40 lessons in five levels, written for Knightwise. Each review moment links to
    its lesson ("Learn it"). The next lesson is the idea that costs most in the last 20 games against its goal; a lesson
    is passed only when that mistake drops in the 5+ games played after studying it; rare mistakes show "you already
    do this". Practice: the user's own positions plus Lichess puzzles on the idea. 5 lessons wait for the Elite games.
  - The user's next lesson today: "Look at their checks" (0.25 checkmates walked into a game, goal 0.1).
- **0.11 Human-like opponents and strong players' games (user's yes on both downloads, 14 Oct evening):**
  - **Maia** (coach/maia.py): Leela lc0 v0.32.1 CPU (24 MB, its own network removed) and the nine Maia networks
    (1,100 to 1,900, 1.3 MB each), in engine/ (python -m coach.get_engine fetches them). Off until switched on in
    Settings. One Leela process per rating (switching networks in one process returned cached answers). Used by:
    Rematch (900 to 1,900 opponents; under 900 the weakened Stockfish stays, since the user is 211 and Maia's lowest
    level is 1,100), the review's "Real players" line, and sparring.
  - **Spar against them** (coach/spar.py), the user's plan: the opponent's own moves from their public games while
    they last (a position reached twice or more), then Maia at their rating. "Someone who plays like them", said so.
  - **Lichess Elite** (coach/elite.py): three months (Sep to Nov 2025, 240 MB zipped, deleted after) sorted into 8
    pawn structures, 200 games each at 2,400+; kept: 6 model games won by the plan and 10 "find the strong player's
    move" positions per structure (Stockfish agrees within 40 centipawns; other equal moves are "also good, find the
    plan move"). coach/library/elite.json, 0.8 MB, bundled. Three course lessons unlocked; prophylaxis still coming.
  - **Fixed on the way:** any Knightwise process that had used Stockfish never finished exiting (python-chess's
    thread). Engines now close before Python waits. Also fixed on main for 0.5.0.
- **Renamed to Knightwise everywhere it shows** (user, 14 Oct: "many files still use chess coach"): the program is
  Knightwise.exe (Task Manager, the Store package), the Startup shortcut Knightwise.lnk (the old one is removed),
  saved AI keys move from "ChessCoach" to "Knightwise" in Credential Manager on first use, web requests say
  Knightwise. Kept on purpose, invisible to players: the chesscoach:// link name, CSS class names, the data folder
  of the old non-Store installer (%LOCALAPPDATA%\ChessCoach) and the old Inno Setup script. The GitHub repository
  (Abhra71/ChessCoach) and the folders on this PC are the user's to rename.
- **Not done:** studying strong players' games (Lichess's masters database now needs an account: a parent's
  decision, or a download to approve). Voice not tried with a real key yet (Round 2 brings the key).

## Now, 14 Oct 2026
- **0.5.0 is on main, not uploaded.** Round 1 test on 13 Oct gave 48 points (docs/TEST-FINDINGS-0.5.0.md); the
  user asked for every one of them in 0.5.0, and all are built. Next: **Round 2** (docs/TEST-ROUND-2.md, about 45
  minutes, the AI part with a parent), then Round 3 on the installed msix, then the Store upload with a parent.
- **Coaches:** two, Maya (af_heart: home, games, practice, puzzles, the archive) and Viktor (am_michael at 0.9:
  progress, plan, lessons).
- **Flagships in 0.5.0** (docs/FLAGSHIPS.md): 3 curated training, 4 Rematch your loss, 5 Clock coach (first part).
  On chess.com: the review one moment at a time on its own board, a warm-up on its home page, tags on the archive,
  and the coach's pick on each page. Then 0.6 voice conversation (flagship 2; branch ai-0.6), 0.8 prep before a game.
- **The chess.com self-check** (docs/SELF-CHECK.md) runs on every visit and weekly on GitHub; Settings and the
  pop-up show its state.
- **Puzzles:** 18,000 Lichess puzzles, 40 per theme in every 100-point band from 300 to about 2,900.
- **Watch out:** the old Store build 0.4.1 is installed on the builder's PC and starts with Windows; a newer
  Knightwise now closes an older running copy by itself.
- Not done, needs the user: GitHub CLI (offered: winget GitHub.cli, MIT, about 35 MB); screenshots of Groq's key pages
  (Round 2, with a parent); ffmpeg for a README GIF.

## Where we were, 11 Oct
- **Microsoft Store:** Knightwise **0.4.1** (MSIX, `Abhra71.Knightwise`, Store ID `9NKLGS6K72J2`) submitted for
  certification on 11 Oct 2026 as a **private beta** (group "Knightwise beta", free). Install link once it passes:
  https://apps.microsoft.com/detail/restricted/9NKLGS6K72J2. Store page text: `installer/msix/STORE_LISTING.md`.
  **Passed certification on 11 Oct 2026 (about 30 minutes) and is live as a private beta ("In Microsoft Store").**
  Updates: Partner Center → Knightwise → Start update (upload a new MSIX with a higher version).
- **After it passes:** install from the link, uninstall the old "Chess Coach" (Settings → Apps), remove the old Chrome
  extension and load `Documents\Knightwise\extension`. Old backups in `%LOCALAPPDATA%\Programs\ChessCoach`
  (`_internal-0.3.0-backup`, `ChessCoach-0.3.0-backup.exe`) can then be deleted.
- **Local testing (builder):** the old installed Chess Coach 0.4.0 has the same screens. Open
  `http://127.0.0.1:8765/#/welcome` (or `#/home`) in a browser while it runs. The `chesscoach://` link on this PC is
  missing its open-command (offered to fix; not done).
- Smart App Control blocks any unsigned build on the builder's PC, so only Store-signed builds can be run there.

## The vision (confirmed by the builder, 11 Oct 2026)
A grandmaster-level coach that **appears when chess.com opens**:
1. An **animated character** on the chess.com page, a text box under it showing what it says, and a voice.
   Its expressions change (pleased / worried / thinking).
2. It **greets you and suggests what to do** (warm-up puzzles, which bot or mode to play).
3. **Silent in any game against a real person** (fair play). Reviews it **right after**, move by move, with arrows
   on chess.com's board.
4. **Guides you around chess.com** ("click Puzzles"), checks whether you did it, highlights the spot if not.
5. **Builds your history**: where you improve and where you don't.
6. **Suggests curated puzzles**, plus extra curated training in the app (premium quality, free).

Today the "brain" exists (Stockfish review of every game, habits, practice, voice, AI explanations, in the app window).
The "body" on chess.com (character, voice there, navigation, instant review) does not.

## Decisions
- **Stockfish decides all chess.** The AI never judges a position.
- **Our code:** reading the chess.com page (no screen capture), navigation highlights, the fair-play gate (the AI never
  receives positions from a live game against a person), progress, the character's expressions (driven by the engine).
- **AI:** the coach's words, understanding what the player says (speech → intent → action, no sentence patterns),
  personality and memory. **Highly personalised per player**: a short player card (rating, habits, progress, preferred
  tone, things they said) goes with the engine facts; one or two points at a time.
- Works without a key (ready-made sentences from engine facts); better with the player's own free key (Gemini, Groq).
- **No auto-clicking on chess.com** (terms-of-service risk): the coach points, the player clicks, the coach checks.
- **Help during bot games:** not until chess.com confirms it's allowed (their rules ban help "during play").
  Draft a message to chess.com support for the builder.
- **Adding an AI key:** a guided in-app walkthrough with **real screenshots** (Google AI Studio first, Groq second),
  red circles on the click spots, a paste box that tests the key and turns green. The builder takes the screenshots;
  personal details are cropped or blurred.

## 0.4.2 (built 11 Oct 2026, waiting for the builder to upload)
`dist/Knightwise-0.4.2.0.msix` (327 MB). Store screenshots (1920x1080, welcome first) in `dist/store-screenshots`.
Done: Store app keeps its data in its package LocalState (fresh start per install; the builder chose a fresh start
for themself too); window opens maximised; cinematic welcome (film with depth of field, typed lines, Satie
Gymnopedie No. 1 by Michael Laucke, public domain, ~18% volume, fades in, mute remembered); Play the Coach removed;
extension guide uses real Chrome screenshots (`installer/make_guide_shots.py`); README has screenshots.
Notes: `?shot=N` starts the film on shot N (for screenshots/trailer). AI keys live in Windows Credential Manager,
so they survive a reinstall. The old Chess Coach uses the same port (8765): while it runs, Knightwise defers to it,
so it must be uninstalled.

## The big update (decided 11 Oct 2026): 0.4.2 is held and ships together with the coaches on chess.com
No beta testers yet, so one big Store update instead of 0.4.2 now. **Waiting for the builder's go-ahead before building.**

**Four original coaches, nothing to pick, no switch option.** Two women, two men, original faces and names (never real
players' likeness: personality rights, Store rules, false endorsement). Each always appears for the same sections, so it
feels like a specialist; the brain (Stockfish + our facts) is identical. Full expressions for all (pleased, worried,
thinking, talking, blinking), driven by engine facts. Draft (names/ages/voices to confirm):
- Maya (woman, calm former champion): game reviews, instant review after a game.
- Arjun (man, young prodigy): puzzles and practice.
- Zara (woman, bold attacker): before you play: greeting, suggestions, navigation guide on chess.com.
- Viktor (man, veteran): progress and history, lessons, endgames. New sections go to whoever fits best.
Voices: Kokoro voices already installed (samples in dist/voice-samples); builder picks one per coach.
Art style: flat cartoon or illustrated portrait (builder picks). Drawn by us, nothing downloaded.

**How they talk (written sentences + optional AI, merged):**
- Always: written sentences in each coach's own style, many wordings per situation picked at random, plus memory
  ("last week 3 hanging pieces, this week 1"). Free, instant, offline, never wrong.
- With the player's free key (Gemini, Groq): real two-way conversation, questions answered in the coach's personality.
  The AI only words the engine's facts; our code checks every move/square it mentions against them, else falls back.
- Never fails: if both AI providers are busy or down, the coach answers with a written sentence in a positive tone and
  the conversation goes on; a small note says replies are briefly simpler.
- Not hidden: everyone is told clearly, in the app and by the coach, "Add a free key (2 minutes, guided) and you can
  talk with your coaches and get replies." Optional, never nagging.
- No AI running on the PC (builder's decision). Live games are never sent to any AI (fair play).

### Big update progress (11 Oct 2026, evening; builder away, provisional choices)
Built and committed (tested with mock chess.com pages in build/preview, not yet in the builder's Chrome):
- coach/coaches.py: four coaches, sections, written sentences per coach, moods; /api/coach.
- extension/faces.js (flat cartoon, 4 moods, blink, talking mouth), buddy.js/css (allow-list of sections; hidden on
  play/game/battle pages), voice via offscreen.html; Maya heads the review panel.
- Instant review (archive-gated), navigation guide (red ring on chess.com's Puzzles link, never clicks).
- Chat: /api/chat, coaches.chat (persona, square check, never-fail fallback); ask box only with a key; the app's
  ask boxes explain the free-key feature instead of a disabled field. Not tested with a real key (none on this PC).
Provisional (builder to confirm): voices Maya bf_emma, Arjun am_puck, Zara af_nova, Viktor bm_george; flat style.
Also done: Viktor's weekly memory. Left: AI key walkthrough with the builder's screenshots, voice
questions on chess.com, Settings note about the coaches, README/Store text, test in the builder's Chrome with
`try.bat`, screenshots, build 0.5.0.

### Built on the night of 11 Oct 2026 (builder away, tested on real chess.com + the app in the builder's Chrome)
- 12 gestures for the four coaches; neck fixed; character centred on the box.
- Library from real data: 30,000 Lichess puzzles in 20 themes (data/puzzles.json, v2), the Lichess opening catalogue
  (coach/openings, CC0). The Lichess opening explorer now needs a Lichess login, so it isn't used.
- coach/plan.py: the sense (stalemated wins, new mistakes, opening trouble, losing streak, stuck habit, fresh idea);
  Your plan tab; Zara brings the new thing on chess.com ("Learn it in Knightwise" opens the app there).
- App: coaches on every tab, reactions on every board move, AI card at the right moments, green chess.com board.
Next: AI key guide (needs the builder's screenshots), real-key test of chat, voice questions on chess.com,
an AI-written "new idea" when a key exists, build 0.5.0, Store text and screenshots.

### Release plan (12 Oct 2026, confirmed by the builder)
1. The builder tests 0.5.0 with docs/TEST-SESSION.md, with part 9 using a real Groq key.
2. Fix everything found: major, smaller and minor.
3. Publish 0.5.0.
4. Then 0.6.0: AI features and AI orchestration, meaning voice conversation, voice game review, the bridge, the usage panel, Groq first; then publish.

### 0.6 work started on branch `ai-0.6` (12 Oct 2026, builder away): main stays exactly as the builder will test 0.5.0
- coach/ai.py: Groq first; a busy model falls back to the provider's small model (Groq llama-3.1-8b-instant, Gemini
  flash-lite), then the provider rests 10 minutes and the next key answers; usage counted per day; Groq's own
  rate-limit headers kept, so "left" is exact. Tests in tests/test_ai_orchestra.py.
- Usage panel: "AI · N% used today" in the sidebar opens a bar per key, what's left, reset time, who is resting.
- Merge into main after 0.5.0 is published. Free-limit numbers still to be checked on the providers' pages.

### Next big piece (the builder, 12 Oct 2026; waiting for the hearing choice)
- Voice-to-voice conversation with the coach of each field, not a text chat: hold to talk, she answers out loud, and the turns continue.
- "Review my game against X" by voice: the coach finds the game, opens it, and talks through every move: what you played,
  what was better, and one new thing to learn. Finished, archived games only.
- A two-way bridge: app to chess.com, which opens the game on chess.com with Maya there; chess.com to app, which opens the right page.
  Every pop-up has navigation to where it makes sense.
- Hearing: recommended, the player's free Groq or Gemini key, so nothing AI runs on the PC; or Chrome's speech recognition, chess.com only;
  or local Whisper. The builder will choose.

### Hooked by value (builder's go-ahead, night of 11-12 Oct 2026; all in 0.5.0)
- Sounds: the builder picked each one on a picker page from Kenney's CC0 packs (coach/ui/sounds, 81 KB): move, capture,
  check, right, wrong, finished (with confetti), coach arriving, button click. Own switch in Settings; no background music.
- Motion: pieces slide, numbers roll up, lines draw themselves, bars and rings fill.
- No brackets in anything the player reads; shorter lines everywhere.
- Home redesigned (the builder found the "Where your games go wrong" box cramped): Today's 5 minutes on top; focus with a
  sparkline and Practise this; habits as clickable tiles (each opens practice for that habit, fewer or more lately);
  You vs you; rating with a win bar; last game in one line from Maya. The big trend chart and the totals row are gone.
- Today's 5 minutes (coach/daily.py): own position, puzzle on today's idea, first 3 moves of your opening; streak
  forgives one missed day.
- Progress tab with Viktor (coach/progress.py): story of the week (or the last 10 games), saved as a picture to
  Pictures\Knightwise; badges from real games only (Safe pieces, Fork-proof, Safe king, Clean games, Daily habit).
- Try it again: any key moment as a puzzle with Maya. Your opening tree (coach/tree.py) with a note on costly branches;
  found for the builder: as Black against 1.d4, 23%, 10 of 35 losses.
- README rewritten as honest marketing: real numbers only (30,000 puzzles, 3,865 openings, 0.7 vs 1.2 pieces a game,
  45% vs 25% wins), what it doesn't do.
Next: the animated preview for the README needs ffmpeg (ask first); the builder's verdict on the new Home and sounds.

### Vision widened (builder, 11 Oct 2026 night): "a grandmaster sitting beside you" (proposal, awaiting confirmation)
- Gestures and faces per situation, per coach: greet (wave), explain (open palm), point (towards the ring), celebrate,
  encourage (fist pump), think (chin), worried (cheek), warn (raised finger), listen (tilt), goodbye; smooth moves.
- On chess.com, before/after games: what to do and what NOT to do today, from the player's data (e.g. which time
  control, rated puzzles slowly instead of Rush, take a break after 3 losses).
- In the Knightwise app: the same coaches pop up by themselves on each tab and on key buttons, with voice; the board
  looks like chess.com's (colours/feel; our own pieces); a "Your plan" section: ONE opening that suits the player's
  games, one strategy idea, one endgame, taught on the board; curated practice with memory of past mistakes.
- Boards: full live guidance on Knightwise's own boards; on chess.com puzzles/lessons only habits and encouragement
  (never solving rated puzzles); bot games only if chess.com allows; games against people: never.

## Found after the Store launch (11 Oct 2026, builder's first use of 0.4.1)
- **No welcome screen on first start:** the Store app reads `%LOCALAPPDATA%\ChessCoach` (`paths.HOME`), the same
  folder the old Chess Coach uses, found `player.txt` and went straight to Home. Fix in 0.4.2: the Store app keeps its
  data in its own package storage, so uninstalling wipes it and a reinstall shows the welcome again (no accounts;
  Google sign-in to keep progress across reinstalls is a later idea).
- **Window opened small and low, not centred:** `create_window(width=1240, height=820)` with no position. Fix: open
  maximised.
- **Music:** FreePD.com has closed. Options offered (Wikimedia Commons, free to use): Satie Gymnopédie No. 1
  (Michael Laucke, public domain) chosen and shipped in 0.4.2.
- **Making public:** stays a private beta until the welcome redesign, the coach on chess.com (steps 4–5) and the AI-key
  walkthrough are in and a few beta testers have used it. Remind the builder then.
- **GitHub:** make the repo page industry-grade (README with real screenshots/GIF walkthroughs, accurate features,
  install steps, releases) as part of each update.

## Build order
1. ~~Welcome screen redesign~~ (done in 0.4.2).
2. ~~Remove "Play the Coach"~~ (done in 0.4.2).
3. ~~Extension guide with the builder's real screenshots~~ (done in 0.4.2) (`screenshots-raw/9-11.png`, gitignored): crop, remove other
   extensions and the OneDrive name (profile picture may stay), type the extension path into the folder dialog's
   address bar, mark the clicks in red; note that Developer mode must stay on and Chrome's "unsafe" warning is expected.
4. **The coach character on chess.com** (extension overlay, voice, appears when chess.com opens, greets with the focus).
5. **Instant review on chess.com** after a game ends.
6. **Navigation guide** (highlight, then check).
7. **Suggestions and progress**; **AI key walkthrough**; **voice commands through the AI**.
8. Optional: **Builder mode** in Settings (replay welcome, start fresh as a new player in a separate profile).
9. **Store trailer video** (builder asked, 11 Oct 2026): about 45–60 s, 1920×1080 MP4, made by recording the app
   itself (3D welcome film, a game review with arrows, practice, the coach on chess.com once built), titles typed on
   screen, the coach's Kokoro voice as narrator and quiet piano underneath. Needs ffmpeg (ask before downloading)
   and a 16:9 "Super hero art" image (the 3D board, no title text) for the trailer to show at the top of the Store page.
   Also: put the 3D welcome screenshot first in the Store listing.
Each change ships as a Store update (new MSIX, version bump); update `STORE_LISTING.md` when what players see changes.

## Welcome screen redesign (requested 11 Oct 2026)
- Started (not yet committed or tested when this was written): `coach/ui/backdrop.js` camera "film" (high above → glide
  down beside the pieces → follow each move → slow orbit) and higher piece hops. Test it in the browser before shipping.
- **Layout:** the welcome card sits on the **right 30–40%** of the screen as a solid, crisp black panel
  (no blurred glass), with a short professional line and the set-up steps. The **left 60–70%** is the 3D scene.
- **Typed lines** over the scene: short phrases typed letter by letter, held, then erased, for example
  "Every move you played, checked." / "Your habits, found." / "A coach that never sleeps."
- **Cinematic camera** (keep the Poly Haven chess set, which the builder likes): start high, looking straight down;
  glide down close to the pieces at their height with depth of field (background softly out of focus); pieces
  **lift, arc and land** with a shadow and the camera follows; a slow orbit; dark vignette edges like a spotlight.
- **Soft piano music**, very quiet (about 15–20%), fades in over 3 seconds, only on the welcome screen, with a mute
  button that's remembered. Preferred source: a real CC0 recording (e.g. FreePD.com). **Ask before downloading**
  (name, size, licence); offer 2–3 to choose from. Fallback: piano generated in code.

## Recent fixes (for context)
- 0.4.1: the first start always shows the welcome screen (the start-up task hides the window only once set up); the
  welcome says "never sells or shares your data" instead of "sends your data anywhere".
- AI: if a provider retires the model in use (404/410), the app picks the current one from the provider's list and
  retries (Gemini prefers `gemini-flash-latest`).
